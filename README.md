# Gemini CLI Telegram

`gemini-cli-telegram` is a Telegram bridge for Gemini CLI. It is meant to run on a laptop, VPS, or cloud VM anywhere Gemini CLI itself works.

## What it does

- Talks to Gemini CLI through Telegram
- Keeps a persistent Gemini session per Telegram chat
- Restricts project access to one `WORKSPACE_ROOT`
- Supports `safe`, `balanced`, and `power` modes
- Stores transcript and audit data in SQLite
- Exports transcripts to Markdown, JSON, or HTML
- Includes a guided setup path and a local environment check

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e .
cp .env.example .env
```

You also need Gemini CLI installed and authenticated on the same host.

## Quick start

```bash
./setup.sh
source venv/bin/activate
gemini-telegram check
gemini-telegram run
```

## Helpful commands

- `gemini-telegram init`
- `gemini-telegram check`
- `gemini-telegram run`

## Project docs

- Architecture: `docs/architecture.md`
- Roadmap: `docs/roadmap.md`
- Commands: `docs/commands.md`
- Security: `docs/security.md`

## Contributing

Read [`CONTRIBUTING.md`](/home/ciprimarian/Repos/Local%20Repos/gemini-cli-telegram/CONTRIBUTING.md) before opening changes. Keep patches small, keep behavior explicit, and do not smuggle magic into the runtime.

## GitHub Pages and domain

The docs site is built with MkDocs and deployed with GitHub Pages through the workflow in `.github/workflows/docs.yml`.

If you want a proper domain:

1. pick a real domain or subdomain you control
2. replace `docs/CNAME.example` with a real `CNAME`
3. point DNS at GitHub Pages
4. update `site_url` in `mkdocs.yml`

## Telegram commands

- `/start`
- `/help`
- `/status`
- `/project <path>`
- `/projects`
- `/pwd`
- `/ls [path]`
- `/git`
- `/actions`
- `/continue`
- `/end`
- `/mode [safe|balanced|power]`
- `/new`
- `/export [md|json|html]`

## Recovery guide

- Bot does not start:
  Run `gemini-telegram check` and fix the first reported problem.
- Gemini is installed but not responding:
  Run `gemini` manually in a terminal on the host and complete authentication there.
- Telegram says you are unauthorized:
  Add your Telegram user ID to `ALLOWED_TELEGRAM_IDS` or `ADMIN_TELEGRAM_IDS`.
- File extraction is blocked:
  The archive likely tries to escape `WORKSPACE_ROOT` or exceeds configured safety limits.
- Voice notes do not work:
  This build provides a graceful fallback message; use text or files unless you wire in a transcription backend.

## Security notes

- Access is deny-by-default.
- Every path resolves under `WORKSPACE_ROOT`.
- `POWER` mode is admin-only.
- Archive extraction is sandbox checked before unpacking.

## Service example

See [`systemd/gemini-telegram.service`](/home/ciprimarian/Repos/Local%20Repos/gemini-cli-telegram/systemd/gemini-telegram.service) for a basic user service template.
