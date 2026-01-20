# Gemini CLI Telegram

This is a Telegram bridge for Gemini CLI.

It is for the kind of setup where you want to prod Gemini from your phone, laptop, VPS, or cloud VM without turning the whole thing into a haunted shell script.

## What you get

- Telegram chat interface for Gemini CLI
- Persistent session per Telegram chat
- Sandboxed project switching under one workspace root
- Safe, balanced, and power modes
- Transcript and audit storage in SQLite
- Markdown, JSON, and HTML transcript export
- A host-side `check` command that tells you what is broken in plain English

## What you still need on the host

- Python 3.11+
- Gemini CLI installed
- Gemini CLI authenticated in a normal terminal first
- A Telegram bot token
- Your Telegram user ID in the allowlist

## Fast path

```bash
git clone <your-repo-url>
cd gemini-cli-telegram
./setup.sh
source venv/bin/activate
gemini-telegram check
gemini-telegram run
```

## If you are not that technical

Run `gemini-telegram check`.

It will tell you:

- if Gemini CLI is missing
- if your Telegram token is missing
- if your workspace path is wrong
- if you forgot to authenticate Gemini on the host

No vague mysticism. Just the broken thing and what to do next.
