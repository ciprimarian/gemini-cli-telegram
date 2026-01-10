from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Awaitable, Callable

from .config import AppConfig


StreamCallback = Callable[[str, bool], Awaitable[None]]


@dataclass(slots=True)
class GeminiRunResult:
    text: str
    stderr: str
    returncode: int
    timed_out: bool = False


@dataclass(slots=True)
class GeminiProcessHandle:
    process: asyncio.subprocess.Process | None = None
    _buffer: list[str] = field(default_factory=list)
    _last_flush_at: float = 0.0
    _last_flush_length: int = 0

    def append(self, chunk: str) -> None:
        self._buffer.append(chunk)

    @property
    def text(self) -> str:
        return "".join(self._buffer)

    def should_flush(self, config: AppConfig, *, force: bool = False) -> bool:
        if force:
            return True
        current_length = len(self.text)
        if current_length - self._last_flush_length >= config.stream_edit_chars:
            return True
        if time.monotonic() - self._last_flush_at >= config.stream_edit_seconds and current_length != self._last_flush_length:
            return True
        return False

    def mark_flushed(self) -> None:
        self._last_flush_at = time.monotonic()
        self._last_flush_length = len(self.text)

    def terminate(self) -> None:
        if self.process and self.process.returncode is None:
            self.process.terminate()


async def run_gemini(
    config: AppConfig,
    *,
    prompt: str,
    session_id: str,
    cwd: Path,
    on_update: StreamCallback,
    handle: GeminiProcessHandle,
) -> GeminiRunResult:
    command = [
        config.gemini_bin,
        "--yolo",
        "--output-format",
        "stream-json",
        "--session-id",
        session_id,
        prompt,
    ]

    handle.process = await asyncio.create_subprocess_exec(
        *command,
        cwd=str(cwd),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    timed_out = False
    stderr_task = asyncio.create_task(handle.process.stderr.read())

    async def _read_stdout() -> None:
        assert handle.process is not None
        while True:
            line = await handle.process.stdout.readline()
            if not line:
                break
            try:
                event = json.loads(line.decode("utf-8").strip())
            except json.JSONDecodeError:
                continue
            event_type = event.get("type")
            text = event.get("text", "")
            if event_type in {"message", "result"} and text:
                handle.append(text)
                if handle.should_flush(config):
                    await on_update(handle.text[-3900:], False)
                    handle.mark_flushed()

    try:
        await asyncio.wait_for(_read_stdout(), timeout=config.subprocess_timeout)
        assert handle.process is not None
        await asyncio.wait_for(handle.process.wait(), timeout=15)
    except asyncio.TimeoutError:
        timed_out = True
        handle.terminate()
        if handle.process:
            await handle.process.wait()

    stderr = (await stderr_task).decode("utf-8", errors="replace").strip()
    final_text = handle.text.strip()
    await on_update(final_text[-3900:] or "No response text was produced.", True)
    return GeminiRunResult(
        text=final_text,
        stderr=stderr,
        returncode=handle.process.returncode if handle.process else 1,
        timed_out=timed_out,
    )
