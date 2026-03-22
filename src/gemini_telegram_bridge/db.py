from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .security import SecurityMode


@dataclass(slots=True)
class SessionState:
    chat_id: int
    session_id: str
    project_path: str
    mode: str


class Storage:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.database_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS session_state (
                    chat_id INTEGER PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    project_path TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS transcript_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    action TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                """
            )

    def get_session_state(self, chat_id: int) -> SessionState | None:
        row = self._conn.execute(
            "SELECT chat_id, session_id, project_path, mode FROM session_state WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()
        if not row:
            return None
        return SessionState(
            chat_id=row["chat_id"],
            session_id=row["session_id"],
            project_path=row["project_path"],
            mode=row["mode"],
        )

    def save_session_state(
        self,
        chat_id: int,
        session_id: str,
        project_path: str,
        mode: SecurityMode,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO session_state (chat_id, session_id, project_path, mode, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    session_id = excluded.session_id,
                    project_path = excluded.project_path,
                    mode = excluded.mode,
                    updated_at = excluded.updated_at
                """,
                (chat_id, session_id, project_path, mode.value, now),
            )

    def append_transcript(self, chat_id: int, role: str, content: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                "INSERT INTO transcript_entries (chat_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, role, content, now),
            )

    def export_transcript(self, chat_id: int) -> list[sqlite3.Row]:
        return self._conn.execute(
            """
            SELECT role, content, created_at
            FROM transcript_entries
            WHERE chat_id = ?
            ORDER BY id ASC
            """,
            (chat_id,),
        ).fetchall()

    def append_audit(self, chat_id: int, user_id: int, action: str, detail: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._conn:
            self._conn.execute(
                "INSERT INTO audit_log (chat_id, user_id, action, detail, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, action, detail, now),
            )
