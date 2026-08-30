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
                    share_token_hash TEXT,
                    method TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    deck_id TEXT,
                    method_result TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            columns = {row[1] for row in con.execute("PRAGMA table_info(reading_sessions)")}
            if "share_token_hash" not in columns:
                con.execute("ALTER TABLE reading_sessions ADD COLUMN share_token_hash TEXT")
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
        share_token = secrets.token_urlsafe(24)
        now = int(time.time())
        expires_at = now + self.ttl_seconds
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO reading_sessions(reading_id,token_hash,share_token_hash,method,persona,deck_id,method_result,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (reading_id, self._hash(token), self._hash(share_token), method, persona, deck_id, json.dumps(method_result, ensure_ascii=False), now, expires_at),
            )
        return {"session_token": token, "share_token": share_token, "expires_at": expires_at}

    def _row(self, reading_id: str):
        self.purge_expired()
        with self._connect() as con:
            return con.execute(
                "SELECT token_hash,share_token_hash,method,persona,deck_id,method_result,expires_at FROM reading_sessions WHERE reading_id=?",
                (reading_id,),
            ).fetchone()

    @staticmethod
    def _public(reading_id: str, row) -> dict[str, Any]:
        return {
            "reading_id": reading_id,
            "method": row[2],
            "persona": row[3],
            "deck_id": row[4],
            "method_result": json.loads(row[5]),
            "expires_at": row[6],
        }

    def get(self, reading_id: str, token: str) -> dict[str, Any]:
        row = self._row(reading_id)
        if not row or not secrets.compare_digest(row[0], self._hash(token or "")):
            raise DivinationError("reading session not found or expired")
        return self._public(reading_id, row)

    def get_shared(self, reading_id: str, share_token: str) -> dict[str, Any]:
        row = self._row(reading_id)
        share_hash = row[1] if row else None
        if not row or not share_hash or not secrets.compare_digest(share_hash, self._hash(share_token or "")):
            raise DivinationError("shared reading not found or expired")
        return self._public(reading_id, row)
