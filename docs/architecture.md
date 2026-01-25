# Architecture

The bridge has a pretty plain shape on purpose.

## Runtime pieces

### `config.py`

Loads environment-driven configuration and keeps the runtime knobs in one place.

### `security.py`

Handles allowlists, mode selection, and rate limiting.

### `sandbox.py`

Makes sure project paths stay under `WORKSPACE_ROOT`.

### `db.py`

Stores session state, transcripts, and audit entries in SQLite.

### `gemini.py`

Runs Gemini CLI in headless mode and streams JSON events back into the bot.

### `app.py`

Telegram command routing, session flow, file handling, exports, and user-facing fallbacks.

## Design bias

- fail clearly
- keep shell assumptions narrow
- keep deployment simple
- keep the host in charge of Gemini authentication

This is not trying to be a full remote operating system in chat clothing.

It is a bridge.
