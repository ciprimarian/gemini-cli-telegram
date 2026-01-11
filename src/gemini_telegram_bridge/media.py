from __future__ import annotations

import shutil
import tarfile
import zipfile
from pathlib import Path

from .config import AppConfig
from .sandbox import WorkspaceSandbox


def ensure_upload_size(path: Path, config: AppConfig) -> None:
    size_mb = path.stat().st_size / (1024 * 1024)
    if size_mb > config.max_upload_size_mb:
        raise ValueError(f"Upload exceeds MAX_UPLOAD_SIZE_MB ({config.max_upload_size_mb} MB).")


def extract_archive(path: Path, destination: Path, sandbox: WorkspaceSandbox, config: AppConfig) -> list[Path]:
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if len(names) > config.archive_max_members:
                raise ValueError("Archive has too many members.")
            sandbox.safe_members([str(destination.relative_to(sandbox.root) / member) for member in names])
            archive.extractall(destination)
            return [destination / member for member in names]

    if tarfile.is_tarfile(path):
        with tarfile.open(path) as archive:
            members = archive.getmembers()
            if len(members) > config.archive_max_members:
                raise ValueError("Archive has too many members.")
            sandbox.safe_members([str(destination.relative_to(sandbox.root) / member.name) for member in members])
            archive.extractall(destination, filter="data")
            return [destination / member.name for member in members]

    raise ValueError("Unsupported archive format.")


def voice_support_message() -> str:
    if shutil.which("ffmpeg") is None:
        return "Voice-note transcription is unavailable because ffmpeg is not installed."
    return (
        "Voice-note transcription is not wired to a speech model yet. "
        "Install ffmpeg plus your preferred transcription stack, then extend the bridge hook."
    )
