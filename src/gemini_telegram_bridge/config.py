from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    def load_dotenv(dotenv_path: str | os.PathLike[str] | None = None) -> bool:
        path = Path(dotenv_path or ".env")
        if not path.exists():
            return False
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())
        return True

from .security import SecurityMode


def _parse_id_set(raw_value: str | None) -> set[int]:
    if not raw_value:
        return set()
    values: set[int] = set()
    for chunk in raw_value.split(","):
        candidate = chunk.strip()
        if not candidate:
            continue
        values.add(int(candidate))
    return values


@dataclass(slots=True)
class AppConfig:
    telegram_bot_token: str
    allowed_telegram_ids: set[int]
    admin_telegram_ids: set[int]
    workspace_root: Path
    data_dir: Path
    database_url: str
    gemini_bin: str
    security_mode: SecurityMode
    polling_timeout: int
    stream_edit_chars: int
    stream_edit_seconds: float
    subprocess_timeout: int
    archive_max_members: int
    archive_max_size_mb: int
    max_upload_size_mb: int
    rate_limit_count: int
    rate_limit_window_seconds: int

    @property
    def database_path(self) -> Path:
        if self.database_url.startswith("sqlite:///"):
            return Path(self.database_url.removeprefix("sqlite:///")).expanduser().resolve()
        raise ValueError("Only sqlite:/// DATABASE_URL values are currently supported.")

    def validate_for_run(self) -> None:
        if not self.telegram_bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required.")
        if not self.allowed_telegram_ids and not self.admin_telegram_ids:
            raise ValueError("Set ALLOWED_TELEGRAM_IDS or ADMIN_TELEGRAM_IDS before running.")
        if not self.workspace_root.exists():
            raise ValueError(f"WORKSPACE_ROOT does not exist: {self.workspace_root}")
        if not self.workspace_root.is_dir():
            raise ValueError(f"WORKSPACE_ROOT is not a directory: {self.workspace_root}")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)


def load_config(dotenv_path: str | os.PathLike[str] | None = None) -> AppConfig:
    load_dotenv(dotenv_path=dotenv_path)

    workspace_root = Path(os.getenv("WORKSPACE_ROOT", os.getcwd())).expanduser().resolve()
    data_dir = Path(os.getenv("DATA_DIR", workspace_root / ".gemini-telegram")).expanduser().resolve()
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{data_dir / 'gemini-telegram.db'}")
    security_mode = SecurityMode.from_value(os.getenv("SECURITY_MODE", SecurityMode.BALANCED.value))

    return AppConfig(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
        allowed_telegram_ids=_parse_id_set(os.getenv("ALLOWED_TELEGRAM_IDS")),
        admin_telegram_ids=_parse_id_set(os.getenv("ADMIN_TELEGRAM_IDS")),
        workspace_root=workspace_root,
        data_dir=data_dir,
        database_url=database_url,
        gemini_bin=os.getenv("GEMINI_BIN", "gemini"),
        security_mode=security_mode,
        polling_timeout=int(os.getenv("POLLING_TIMEOUT", "30")),
        stream_edit_chars=int(os.getenv("STREAM_EDIT_CHARS", "160")),
        stream_edit_seconds=float(os.getenv("STREAM_EDIT_SECONDS", "1.5")),
        subprocess_timeout=int(os.getenv("SUBPROCESS_TIMEOUT", "1800")),
        archive_max_members=int(os.getenv("ARCHIVE_MAX_MEMBERS", "2000")),
        archive_max_size_mb=int(os.getenv("ARCHIVE_MAX_SIZE_MB", "250")),
        max_upload_size_mb=int(os.getenv("MAX_UPLOAD_SIZE_MB", "50")),
        rate_limit_count=int(os.getenv("RATE_LIMIT_COUNT", "8")),
        rate_limit_window_seconds=int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
    )
