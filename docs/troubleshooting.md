# Troubleshooting

## "Gemini CLI is not installed"

Install Gemini CLI on the host and verify `gemini --help` works.

## "Not authorized"

Add your Telegram user ID to `ALLOWED_TELEGRAM_IDS` or `ADMIN_TELEGRAM_IDS` in `.env`.

## "Nothing happens after I send a prompt"

Run:

```bash
gemini-telegram check
```

Then verify:

- the bridge process is still running
- Gemini CLI is authenticated
- the Telegram bot token is valid

## "Voice notes do not work"

That path intentionally falls back cleanly right now.

Use text or files unless you wire in a speech backend and `ffmpeg`.

## "Archive upload failed"

The archive was blocked because it looked unsafe or exceeded configured limits.

That is a feature, not rudeness.
