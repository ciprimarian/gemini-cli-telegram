#!/usr/bin/env bash
set -euo pipefail

printf "Gemini Telegram setup\n"
printf "=====================\n\n"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
python -m pip install --upgrade pip >/dev/null
python -m pip install -e . >/dev/null

if [ ! -f ".env" ]; then
    cp .env.example .env
fi

printf "This bridge expects Gemini CLI to already be installed and authenticated on this host.\n"
printf "If that is not done yet, stop here and finish Gemini CLI setup in a normal terminal first.\n\n"

read -r -p "Telegram bot token: " TELEGRAM_BOT_TOKEN
read -r -p "Allowed Telegram IDs (comma separated): " ALLOWED_TELEGRAM_IDS
read -r -p "Admin Telegram IDs (comma separated, optional): " ADMIN_TELEGRAM_IDS
read -r -p "Workspace root [$PWD]: " WORKSPACE_ROOT
WORKSPACE_ROOT=${WORKSPACE_ROOT:-$PWD}

cat > .env <<EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ALLOWED_TELEGRAM_IDS=$ALLOWED_TELEGRAM_IDS
ADMIN_TELEGRAM_IDS=$ADMIN_TELEGRAM_IDS
WORKSPACE_ROOT=$WORKSPACE_ROOT
DATA_DIR=$WORKSPACE_ROOT/.gemini-telegram
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
EOF

printf "\nSetup files written.\n"
printf "Next steps:\n"
printf "1. source venv/bin/activate\n"
printf "2. gemini-telegram check\n"
printf "3. gemini-telegram run\n\n"
printf "If something fails, run 'gemini-telegram check' and fix the reported item first.\n"
