"""SQLite-backed memory for multi-agent runs."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any
from uuid import uuid4


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MemoryStore:
    """Persistent run memory with events and artifacts."""

    def __init__(self, db_path: str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._db_path.as_posix())
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                started_at TEXT NOT NULL,
                repo_input TEXT NOT NULL,
                user_focus TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                ts TEXT NOT NULL,
                agent_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS artifacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                key TEXT NOT NULL,
                value_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def start_run(self, repo_input: str, user_focus: str) -> str:
        run_id = str(uuid4())
        self._conn.execute(
            "INSERT INTO runs (run_id, started_at, repo_input, user_focus) VALUES (?, ?, ?, ?)",
            (run_id, _utc_now_iso(), repo_input, user_focus),
        )
        self._conn.commit()
        return run_id

    def log_event(
        self,
        run_id: str,
        agent_name: str,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO events (run_id, ts, agent_name, event_type, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (run_id, _utc_now_iso(), agent_name, event_type, json.dumps(payload)),
        )
        self._conn.commit()

    def save_artifact(self, run_id: str, key: str, value: dict[str, Any]) -> None:
        self._conn.execute(
            """
            INSERT INTO artifacts (run_id, key, value_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (run_id, key, json.dumps(value), _utc_now_iso()),
        )
        self._conn.commit()

    def load_latest_summary(self, repo_input: str) -> dict[str, Any] | None:
        cursor = self._conn.cursor()
        cursor.execute(
            """
            SELECT a.value_json
            FROM artifacts a
            JOIN runs r ON r.run_id = a.run_id
            WHERE r.repo_input = ? AND a.key = 'final_review'
            ORDER BY a.id DESC
            LIMIT 1
            """,
            (repo_input,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        try:
            return json.loads(row["value_json"])
        except (json.JSONDecodeError, TypeError):
            return None

