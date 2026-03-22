from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from .config import load_config


ENV_TEMPLATE = """# Copy this file to .env and fill in the values.
TELEGRAM_BOT_TOKEN=
ALLOWED_TELEGRAM_IDS=
ADMIN_TELEGRAM_IDS=
WORKSPACE_ROOT=.
DATA_DIR=.gemini-telegram
DATABASE_URL=
GEMINI_BIN=gemini
SECURITY_MODE=balanced
POLLING_TIMEOUT=30
STREAM_EDIT_CHARS=160
STREAM_EDIT_SECONDS=1.5
SUBPROCESS_TIMEOUT=1800
ARCHIVE_MAX_MEMBERS=2000
ARCHIVE_MAX_SIZE_MB=250
MAX_UPLOAD_SIZE_MB=50
RATE_LIMIT_COUNT=8
RATE_LIMIT_WINDOW_SECONDS=60
"""


def _write_init_file(path: Path) -> int:
    if path.exists():
        print(f"{path} already exists.")
        return 0
    path.write_text(ENV_TEMPLATE, encoding="utf-8")
    print(f"Wrote {path}")
    return 0


def _run_check() -> int:
    config = load_config()
    failures: list[str] = []

    if not config.telegram_bot_token:
        failures.append("Missing TELEGRAM_BOT_TOKEN.")
    if shutil.which(config.gemini_bin) is None:
        failures.append(f"Gemini binary not found in PATH: {config.gemini_bin}")
    if not config.workspace_root.exists():
        failures.append(f"WORKSPACE_ROOT does not exist: {config.workspace_root}")

    print(f"WORKSPACE_ROOT: {config.workspace_root}")
    print(f"DATA_DIR: {config.data_dir}")
    print(f"DATABASE_URL: {config.database_url}")
    print(f"GEMINI_BIN: {config.gemini_bin}")
    print(f"SECURITY_MODE: {config.security_mode.value}")
    print(f"Gemini binary found: {'yes' if shutil.which(config.gemini_bin) else 'no'}")
    print(f"Telegram token configured: {'yes' if bool(config.telegram_bot_token) else 'no'}")

    if failures:
        print("\nProblems found:")
        for failure in failures:
            print(f"- {failure}")
        print("\nFallback guidance:")
        print("- Create a .env file from `.env.example` or run `gemini-telegram init`.")
        print("- Install Gemini CLI and make sure `gemini` runs on the host.")
        print("- Authenticate Gemini CLI manually in a terminal on the host before starting the bot.")
        return 1

    print("\nEnvironment looks usable.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gemini-telegram")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="write a starter .env.example file")
    init_parser.add_argument("--path", default=".env.example")

    subparsers.add_parser("check", help="validate local runtime prerequisites")
    subparsers.add_parser("run", help="run the Telegram bot")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "init":
        return _write_init_file(Path(args.path))
    if args.command == "check":
        return _run_check()
    if args.command == "run":
        from .app import run_bot

        config = load_config()
        config.validate_for_run()
        run_bot(config)
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2
