from __future__ import annotations

import os
import re
import secrets
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "milkcat.analytics-event/v1"
ALLOWED_EVENTS = {"page_view", "project_open", "cta_click", "funnel_step"}
ALLOWED_SOURCES = {"direct", "threads", "line", "share", "search", "other"}
ALLOWED_LANGUAGES = {"zh", "ja", "ko", "es", "en", "other"}
ALLOWED_DEVICES = {"mobile", "tablet", "desktop", "other"}
_KEY_RE = re.compile(r"^[a-z0-9/_-]{1,96}$")


def _safe_key(value: Any, *, max_length: int = 96, required: bool = False) -> str | None:
    raw = str(value or "").strip().lower()
    if not raw:
        if required:
            raise ValueError("analytics_key_required")
        return None
    if len(raw) > max_length or not _KEY_RE.fullmatch(raw):
        raise ValueError("analytics_key_invalid")
    return raw


class SiteAnalyticsStore:
    """Privacy-first aggregate product analytics.

    Persistence invariant: no raw referrer, query string, IP address, user-agent,
    cookie, account identity, persistent visitor id, or free-form text is stored.
    """

    def __init__(self, db_path: str | os.PathLike[str]) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS site_analytics (
                    event_id TEXT PRIMARY KEY,
                    occurred_date TEXT NOT NULL,
                    site TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    page_key TEXT NOT NULL,
                    project TEXT,
                    action TEXT,
                    step TEXT,
                    source TEXT NOT NULL,
                    language TEXT NOT NULL,
                    device_class TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_site_analytics_date
                  ON site_analytics(occurred_date);
                CREATE INDEX IF NOT EXISTS idx_site_analytics_event
                  ON site_analytics(event_type);
                CREATE INDEX IF NOT EXISTS idx_site_analytics_page
                  ON site_analytics(page_key);
                CREATE INDEX IF NOT EXISTS idx_site_analytics_project
                  ON site_analytics(project);
                """
            )

    def record(self, payload: dict[str, Any]) -> str:
        if not isinstance(payload, dict) or payload.get("schema") != SCHEMA:
            raise ValueError("analytics_schema_invalid")

        event_type = str(payload.get("event_type") or "").strip()
        if event_type not in ALLOWED_EVENTS:
            raise ValueError("analytics_event_invalid")

        source = str(payload.get("source") or "other").strip().lower()
        language = str(payload.get("language") or "other").strip().lower()
        device = str(payload.get("device_class") or "other").strip().lower()

        event_id = secrets.token_urlsafe(18)
        row = (
            event_id,
            datetime.now(timezone.utc).date().isoformat(),
            _safe_key(payload.get("site"), max_length=64, required=True),
            event_type,
            _safe_key(payload.get("page_key"), max_length=96, required=True),
            _safe_key(payload.get("project"), max_length=64),
            _safe_key(payload.get("action"), max_length=64),
            _safe_key(payload.get("step"), max_length=64),
            source if source in ALLOWED_SOURCES else "other",
            language if language in ALLOWED_LANGUAGES else "other",
            device if device in ALLOWED_DEVICES else "other",
        )

        # Reject anything outside the explicit protocol. This prevents a future
        # client from silently adding free-form or identity-bearing fields.
        allowed_fields = {
            "schema", "site", "event_type", "page_key", "project", "action",
            "step", "source", "language", "device_class",
        }
        if set(payload) - allowed_fields:
            raise ValueError("analytics_field_not_allowed")

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO site_analytics (
                    event_id, occurred_date, site, event_type, page_key, project,
                    action, step, source, language, device_class
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                row,
            )
        return event_id

    def summary(self, *, days: int = 30, site: str | None = None) -> dict[str, Any]:
        days = max(1, min(int(days), 3650))
        params: list[Any] = [f"-{days - 1} days"]
        where = "occurred_date >= date('now', ?)"
        if site:
            where += " AND site = ?"
            params.append(_safe_key(site, max_length=64, required=True))

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM site_analytics WHERE {where} ORDER BY occurred_date ASC",
                params,
            ).fetchall()

        def counts(key: str) -> dict[str, int]:
            counter = Counter(str(row[key] or "unknown") for row in rows)
            return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))

        daily = Counter(str(row["occurred_date"]) for row in rows)
        return {
            "schema": "milkcat.analytics-summary/v1",
            "privacy": {
                "ip_stored": False,
                "user_agent_stored": False,
                "referrer_url_stored": False,
                "query_string_stored": False,
                "cookie_id_stored": False,
                "persistent_visitor_id": False,
                "free_form_text": False,
            },
            "window_days": days,
            "site": site,
            "total_events": len(rows),
            "by_date": dict(sorted(daily.items())),
            "by_event": counts("event_type"),
            "by_page": counts("page_key"),
            "by_project": counts("project"),
            "by_source": counts("source"),
            "by_language": counts("language"),
            "by_device": counts("device_class"),
            "by_action": counts("action"),
            "by_step": counts("step"),
        }
