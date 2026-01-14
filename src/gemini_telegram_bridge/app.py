from __future__ import annotations

import asyncio
import contextlib
import html
import json
import logging
import tempfile
import uuid
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import AppConfig
from .db import Storage
from .gemini import GeminiProcessHandle, run_gemini
from .helptext import HELP_TEXT, START_TEXT
from .media import ensure_upload_size, extract_archive, voice_support_message
from .sandbox import WorkspaceSandbox
from .security import AccessController, RateLimiter, SecurityMode

logger = logging.getLogger(__name__)


class BridgeApp:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.storage = Storage(config.database_path)
        self.sandbox = WorkspaceSandbox(config.workspace_root)
        self.access = AccessController(
            allowed_ids=config.allowed_telegram_ids,
            admin_ids=config.admin_telegram_ids,
            default_mode=config.security_mode,
        )
        self.rate_limiter = RateLimiter(config.rate_limit_count, config.rate_limit_window_seconds)
        self.active_runs: dict[int, GeminiProcessHandle] = {}

    def build_application(self) -> Application:
        app = Application.builder().token(self.config.telegram_bot_token).build()
        app.bot_data["bridge"] = self

        app.add_handler(CommandHandler("start", self.start))
        app.add_handler(CommandHandler("help", self.help))
        app.add_handler(CommandHandler("status", self.status))
        app.add_handler(CommandHandler("project", self.project))
        app.add_handler(CommandHandler("repo", self.project))
        app.add_handler(CommandHandler("projects", self.projects))
        app.add_handler(CommandHandler("pwd", self.pwd))
        app.add_handler(CommandHandler("ls", self.ls))
        app.add_handler(CommandHandler("git", self.git_status))
        app.add_handler(CommandHandler("actions", self.actions))
        app.add_handler(CommandHandler("session", self.continue_session))
        app.add_handler(CommandHandler("continue", self.continue_session))
        app.add_handler(CommandHandler("end", self.end_session))
        app.add_handler(CommandHandler("mode", self.mode))
        app.add_handler(CommandHandler("new", self.new_session))
        app.add_handler(CommandHandler("export", self.export))
        app.add_handler(CallbackQueryHandler(self.stop_callback, pattern=r"^stop:"))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        app.add_handler(MessageHandler(filters.Document.ALL, self.handle_document))
        app.add_handler(MessageHandler(filters.VOICE, self.handle_voice))
        app.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))
        return app

    def get_state(self, chat_id: int) -> tuple[str, Path, SecurityMode]:
        state = self.storage.get_session_state(chat_id)
        if state:
            project_path = self.sandbox.resolve(state.project_path)
            return state.session_id, project_path, SecurityMode.from_value(state.mode)
        session_id = f"tg-{chat_id}-{uuid.uuid4().hex[:8]}"
        project_path = self.config.workspace_root
        mode = self.config.security_mode
        self.storage.save_session_state(chat_id, session_id, str(project_path), mode)
        return session_id, project_path, mode

    def save_state(self, chat_id: int, session_id: str, project_path: Path, mode: SecurityMode) -> None:
        self.storage.save_session_state(chat_id, session_id, str(project_path), mode)

    async def ensure_access(self, update: Update) -> bool:
        user = update.effective_user
        chat = update.effective_chat
        if user is None or chat is None:
            return False
        try:
            self.access.ensure_allowed(user.id)
            return True
        except PermissionError as exc:
            if update.effective_message:
                await update.effective_message.reply_text(
                    f"{exc}\n\nAdd this Telegram ID on the host: {user.id}"
                )
            self.storage.append_audit(chat.id, user.id, "deny", str(exc))
            return False

    async def send_typing(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.effective_chat:
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await update.effective_message.reply_text(START_TEXT)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await update.effective_message.reply_text(HELP_TEXT)

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        session_id, project_path, mode = self.get_state(update.effective_chat.id)
        details = [
            f"Workspace root: {self.config.workspace_root}",
            f"Current project: {project_path}",
            f"Security mode: {mode.value}",
            f"Session ID: {session_id}",
            f"Gemini binary: {self.config.gemini_bin}",
            f"Data dir: {self.config.data_dir}",
        ]
        await update.effective_message.reply_text("\n".join(details))

    async def continue_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        session_id, project_path, mode = self.get_state(update.effective_chat.id)
        await update.effective_message.reply_text(
            f"Resuming session {session_id}\nProject: {project_path}\nMode: {mode.value}"
        )

    async def end_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        _, project_path, mode = self.get_state(chat_id)
        session_id = f"tg-{chat_id}-{uuid.uuid4().hex[:8]}"
        self.save_state(chat_id, session_id, project_path, mode)
        await update.effective_message.reply_text("Current session ended. The next prompt starts clean.")

    async def project(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        session_id, current_project, mode = self.get_state(chat_id)
        raw_path = " ".join(context.args).strip()
        if not raw_path:
            await update.effective_message.reply_text(f"Current project: {current_project}")
            return
        try:
            target = self.sandbox.resolve(raw_path, current_project=current_project)
        except PermissionError as exc:
            await update.effective_message.reply_text(str(exc))
            return
        if not target.exists() or not target.is_dir():
            await update.effective_message.reply_text(f"Project path is not a directory: {target}")
            return
        self.save_state(chat_id, session_id, target, mode)
        await update.effective_message.reply_text(f"Project switched to {target}")

    async def projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        children = [item.name for item in sorted(self.config.workspace_root.iterdir()) if item.is_dir()]
        if not children:
            await update.effective_message.reply_text("No project directories found under WORKSPACE_ROOT.")
            return
        await update.effective_message.reply_text("\n".join(children[:200]))

    async def pwd(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        _, current_project, _ = self.get_state(update.effective_chat.id)
        await update.effective_message.reply_text(str(current_project))

    async def ls(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        _, current_project, mode = self.get_state(chat_id)
        if not self.access.allow_shell(update.effective_user.id, mode):
            await update.effective_message.reply_text("Listing files is disabled in SAFE mode.")
            return
        raw_path = " ".join(context.args).strip()
        try:
            target = self.sandbox.resolve(raw_path or ".", current_project=current_project)
        except PermissionError as exc:
            await update.effective_message.reply_text(str(exc))
            return
        if not target.exists():
            await update.effective_message.reply_text(f"Path does not exist: {target}")
            return
        entries = [item.name + ("/" if item.is_dir() else "") for item in sorted(target.iterdir())[:200]]
        await update.effective_message.reply_text("\n".join(entries) or "(empty)")

    async def git_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        _, current_project, mode = self.get_state(chat_id)
        if not self.access.allow_shell(update.effective_user.id, mode):
            await update.effective_message.reply_text("Git helpers are disabled in SAFE mode.")
            return
        process = await asyncio.create_subprocess_exec(
            "git",
            "-C",
            str(current_project),
            "status",
            "--short",
            "--branch",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        text = stdout.decode("utf-8", errors="replace").strip()
        error = stderr.decode("utf-8", errors="replace").strip()
        if process.returncode != 0:
            await update.effective_message.reply_text(error or "Current project is not a git repository.")
            return
        await update.effective_message.reply_text(text or "Working tree clean.")

    async def actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await update.effective_message.reply_text(
            "Quick moves:\n"
            "- /status\n"
            "- /project <path>\n"
            "- /ls\n"
            "- /git\n"
            "- /export md\n"
            "- /new"
        )

    async def mode(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        session_id, project_path, current_mode = self.get_state(chat_id)
        raw = context.args[0] if context.args else None
        if not raw:
            await update.effective_message.reply_text(f"Current mode: {current_mode.value}")
            return
        try:
            new_mode = self.access.resolve_mode(update.effective_user.id, raw)
        except (PermissionError, ValueError) as exc:
            await update.effective_message.reply_text(str(exc))
            return
        self.save_state(chat_id, session_id, project_path, new_mode)
        await update.effective_message.reply_text(f"Mode updated to {new_mode.value}")

    async def new_session(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        _, project_path, mode = self.get_state(chat_id)
        session_id = f"tg-{chat_id}-{uuid.uuid4().hex[:8]}"
        self.save_state(chat_id, session_id, project_path, mode)
        await update.effective_message.reply_text("Started a fresh Gemini session for this chat.")

    async def export(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        chat_id = update.effective_chat.id
        export_format = (context.args[0] if context.args else "md").lower()
        rows = self.storage.export_transcript(chat_id)
        if not rows:
            await update.effective_message.reply_text("No transcript entries stored yet.")
            return

        if export_format == "json":
            payload = [
                {"role": row["role"], "content": row["content"], "created_at": row["created_at"]}
                for row in rows
            ]
            content = json.dumps(payload, indent=2)
            suffix = ".json"
        elif export_format == "html":
            parts = ["<html><body><h1>Gemini Telegram Export</h1>"]
            for row in rows:
                parts.append(
                    f"<p><strong>{html.escape(row['role'])}</strong> "
                    f"<em>{html.escape(row['created_at'])}</em><br>{html.escape(row['content'])}</p>"
                )
            parts.append("</body></html>")
            content = "\n".join(parts)
            suffix = ".html"
        else:
            lines = ["# Gemini Telegram Export", ""]
            for row in rows:
                lines.append(f"## {row['role']} - {row['created_at']}")
                lines.append(row["content"])
                lines.append("")
            content = "\n".join(lines)
            suffix = ".md"

        export_path = self.config.data_dir / f"export-{chat_id}{suffix}"
        export_path.write_text(content, encoding="utf-8")
        with export_path.open("rb") as handle:
            await update.effective_message.reply_document(handle, filename=export_path.name)

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await self.run_agent(update, context, update.effective_message.text)

    async def handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        document = update.effective_message.document
        with tempfile.TemporaryDirectory(dir=self.config.data_dir) as temp_dir:
            local_dir = Path(temp_dir)
            local_path = local_dir / (document.file_name or "upload.bin")
            telegram_file = await document.get_file()
            await telegram_file.download_to_drive(custom_path=str(local_path))
            ensure_upload_size(local_path, self.config)

            note = f"User uploaded file: {local_path.name}"
            extracted_note = ""
            try:
                extracted_dir = local_dir / "extracted"
                extracted_dir.mkdir(exist_ok=True)
                extracted_paths = extract_archive(local_path, extracted_dir, self.sandbox, self.config)
                extracted_note = f"\nArchive extracted with {len(extracted_paths)} entries."
            except ValueError:
                extracted_note = ""

            await self.run_agent(update, context, f"{note}{extracted_note}")

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await self.run_agent(
            update,
            context,
            "The user uploaded a screenshot/photo. Ask them what they want analyzed and mention that image-aware prompts depend on local Gemini CLI capabilities.",
        )

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if not await self.ensure_access(update):
            return
        await update.effective_message.reply_text(voice_support_message())

    async def stop_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        chat_id = int(query.data.split(":", 1)[1])
        handle = self.active_runs.get(chat_id)
        if handle:
            handle.terminate()
        await query.edit_message_text("Stopped the active Gemini process.")

    async def run_agent(self, update: Update, context: ContextTypes.DEFAULT_TYPE, prompt: str) -> None:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        if not self.rate_limiter.allow(user_id):
            await update.effective_message.reply_text(
                f"Slow down a bit. Limit is {self.config.rate_limit_count} requests every "
                f"{self.config.rate_limit_window_seconds} seconds."
            )
            return
        session_id, project_path, mode = self.get_state(chat_id)
        self.storage.append_transcript(chat_id, "user", prompt)
        self.storage.append_audit(chat_id, user_id, "prompt", prompt[:300])

        reply = await update.effective_message.reply_text(
            "Thinking...",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Stop", callback_data=f"stop:{chat_id}")]]
            ),
        )

        handle = GeminiProcessHandle()
        self.active_runs[chat_id] = handle

        async def typing_loop() -> None:
            try:
                while True:
                    await self.send_typing(update, context)
                    await asyncio.sleep(4)
            except asyncio.CancelledError:
                return

        async def on_update(text: str, is_final: bool) -> None:
            payload = text[-3900:] if text else "No response text was produced."
            with contextlib.suppress(Exception):
                await reply.edit_text(
                    payload,
                    reply_markup=None if is_final else InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Stop", callback_data=f"stop:{chat_id}")]]
                    ),
                )
            if is_final:
                await self.send_typing(update, context)

        typing_task = asyncio.create_task(typing_loop())
        try:
            result = await run_gemini(
                self.config,
                prompt=prompt,
                session_id=session_id,
                cwd=project_path,
                on_update=on_update,
                handle=handle,
            )
        except FileNotFoundError:
            await reply.edit_text(
                "Gemini CLI is not installed or GEMINI_BIN is wrong.\n"
                "Run `gemini-telegram check` on the host and fix GEMINI_BIN."
            )
            self.storage.append_transcript(chat_id, "assistant", "Gemini CLI missing.")
            return
        finally:
            typing_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await typing_task
            self.active_runs.pop(chat_id, None)

        final_message = result.text or "Gemini returned no visible response."
        if result.stderr:
            final_message = f"{final_message}\n\nstderr:\n{result.stderr[-1200:]}"
        if result.timed_out:
            final_message = (
                f"{final_message}\n\nThe command timed out. Increase SUBPROCESS_TIMEOUT or retry with a smaller prompt."
            )

        await reply.edit_text(final_message[-3900:])
        self.storage.append_transcript(chat_id, "assistant", final_message)


def run_bot(config: AppConfig) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    application = BridgeApp(config).build_application()
    application.run_polling(timeout=config.polling_timeout)
