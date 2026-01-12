START_TEXT = """
Gemini Telegram Bridge is online.

What this does:
- Chat with Gemini CLI from Telegram
- Keep a session per chat
- Work inside one sandboxed workspace root
- Switch between safe, balanced, and power modes

Good first commands:
/help
/status
/project .
/mode
/new

If you are not technical:
- Send a normal message and the bot will talk to Gemini for you.
- If setup fails, run `gemini-telegram check` on the host machine and follow the printed fixes.
- If Gemini is not logged in, open a terminal on the host and authenticate Gemini CLI there first.
""".strip()

HELP_TEXT = """
Commands
/start - intro and quick-start
/help - this help
/status - environment and project status
/project <path> - switch active project inside WORKSPACE_ROOT
/projects - list immediate project directories
/pwd - show current project
/ls [path] - list files inside the sandbox
/mode [safe|balanced|power] - show or set mode
/new - start a fresh Gemini session for this chat
/export [md|json|html] - export this chat transcript

Fallbacks
- If the bot says you are unauthorized, add your Telegram user ID to ALLOWED_TELEGRAM_IDS or ADMIN_TELEGRAM_IDS.
- If replies fail immediately, run `gemini-telegram check` on the host.
- If Gemini says it is not authenticated, sign in to Gemini CLI on the host machine.
- If a voice note does not work, upload text or a file instead and check whether ffmpeg is installed.
""".strip()
