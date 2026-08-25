from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from .core import DivinationError


class ReadingSessionStore:
    """Stores only immutable symbolic state. Questions and answers are intentionally not persisted."""

    def __init__(self, db_path: str | Path, ttl_seconds: int = 86400) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS reading_sessions (
                    reading_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL,
                    method TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    deck_id TEXT,
                    method_result TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_reading_sessions_expiry ON reading_sessions(expires_at)")

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def purge_expired(self) -> None:
        now = int(time.time())
        with self._connect() as con:
            con.execute("DELETE FROM reading_sessions WHERE expires_at <= ?", (now,))

    def create(self, *, reading_id: str, method: str, persona: str, deck_id: str | None, method_result: dict[str, Any]) -> dict[str, Any]:
        self.purge_expired()
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        expires_at = now + self.ttl_seconds
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO reading_sessions(reading_id,token_hash,method,persona,deck_id,method_result,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?)",
                (reading_id, self._hash(token), method, persona, deck_id, json.dumps(method_result, ensure_ascii=False), now, expires_at),
            )
        return {"session_token": token, "expires_at": expires_at}

    def get(self, reading_id: str, token: str) -> dict[str, Any]:
        self.purge_expired()
        with self._connect() as con:
            row = con.execute(
                "SELECT token_hash,method,persona,deck_id,method_result,expires_at FROM reading_sessions WHERE reading_id=?",
                (reading_id,),
            ).fetchone()
        if not row or not secrets.compare_digest(row[0], self._hash(token or "")):
            raise DivinationError("reading session not found or expired")
        return {
            "reading_id": reading_id,
            "method": row[1],
            "persona": row[2],
            "deck_id": row[3],
            "method_result": json.loads(row[4]),
            "expires_at": row[5],
        }
