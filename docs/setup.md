# Setup

## 1. Create the bot

Talk to `@BotFather`, create a bot, copy the token.

## 2. Find your Telegram user ID

Talk to a helper like `@userinfobot` and copy your numeric user ID.

## 3. Make sure Gemini CLI works on the host

Open a normal terminal on the host and check:

```bash
gemini --help
```

If Gemini CLI wants authentication, do that first there.

## 4. Run the setup script

```bash
./setup.sh
```

It writes `.env`, installs the package in a venv, and points the bridge at your workspace.

## 5. Run a health check

```bash
gemini-telegram check
```

If this fails, fix the first failure before trying anything else.

## 6. Start the bridge

```bash
gemini-telegram run
```

Then open Telegram and send `/start`.
