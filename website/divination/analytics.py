from __future__ import annotations

import json
import os
import secrets
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_SOURCES = {"direct", "threads", "line", "share", "search", "other"}
ALLOWED_CATEGORIES = {
    "love_relationship",
    "career_study",
    "money",
    "decision",
    "self_growth",
    "general",
    "other",
}


def normalize_source(value: Any) -> str:
    source = str(value or "direct").strip().lower()
    return source if source in ALLOWED_SOURCES else "other"


def normalize_language(value: Any) -> str:
    raw = str(value or "").strip().replace("_", "-").lower()
    if raw.startswith("zh"):
        return "zh"
    if raw.startswith("ja"):
        return "ja"
    if raw.startswith("ko"):
        return "ko"
    if raw.startswith("es"):
        return "es"
    if raw.startswith("en"):
        return "en"
    return "other"


def classify_question(question: str, method_result: dict[str, Any] | None) -> str:
    """Classify transient question text into a coarse category.

    The caller must discard the raw question after this function returns. Only
    the resulting enum is eligible for persistence.
    """
    text = str(question or "").strip().lower()

    keyword_groups = (
        ("money", ("錢", "金錢", "財運", "收入", "薪水", "投資", "股票", "理財", "貸款", "房貸", "money", "finance", "financial", "salary", "income", "investment", "dinero", "inversión", "お金", "投資", "収入", "돈", "투자", "수입")),
        ("love_relationship", ("感情", "愛情", "關係", "對方", "他對我", "她對我", "我們之間", "戀愛", "relationship", "love", "partner", "boyfriend", "girlfriend", "amor", "pareja", "恋愛", "関係", "相手", "연애", "관계")),
        ("career_study", ("工作", "職涯", "轉職", "換工作", "升遷", "事業", "學業", "考試", "career", "job", "work", "study", "exam", "trabajo", "carrera", "estudio", "仕事", "転職", "勉強", "직장", "이직", "공부")),
        ("decision", ("哪個", "二選一", "兩個選擇", "選擇 a", "選擇 b", "比較", "該選", "vs", " or ", "which", "choose", "decision", "elegir", "decisión", "どちら", "選ぶ", "선택")),
        ("self_growth", ("自己", "成長", "人生方向", "方向", "下一步", "內在", "課題", "self", "growth", "direction", "purpose", "crecimiento", "dirección", "自分", "成長", "方向", "자기", "성장", "방향")),
    )
    for category, markers in keyword_groups:
        if any(marker in text for marker in markers):
            return category

    result = method_result or {}
    plan = result.get("spread_plan") if isinstance(result.get("spread_plan"), dict) else {}
    intent = str(plan.get("intent") or "").strip().lower()
    intent_map = {
        "relationship": "love_relationship",
        "career": "career_study",
        "decision": "decision",
        "direction": "self_growth",
        "guidance": "general",
        "timeline": "general",
        "clarification": "general",
        "deep_reading": "general",
    }
    return intent_map.get(intent, "general")


class ReadingAnalyticsStore:
    """De-identified, append-only reading analytics.

    Privacy invariant: question text, answer text, IP address, referrer URL,
    account identity, reading/session IDs and device fingerprints are not part of
    the schema and are never accepted by record_reading().
    """

    def __init__(self, db_path: str | os.PathLike[str]) -> None:
        self.path = Path(db_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS reading_analytics (
                    event_id TEXT PRIMARY KEY,
                    occurred_date TEXT NOT NULL,
                    source TEXT NOT NULL,
                    question_category TEXT NOT NULL,
                    method TEXT NOT NULL,
                    spread TEXT,
                    deck_id TEXT,
                    persona_id TEXT,
                    language TEXT NOT NULL,
                    card_count INTEGER NOT NULL,
                    draw_mode TEXT
                );
                CREATE TABLE IF NOT EXISTS reading_cards (
                    event_id TEXT NOT NULL,
                    position_index INTEGER NOT NULL,
                    card_id TEXT NOT NULL,
                    orientation TEXT NOT NULL,
                    position TEXT,
                    PRIMARY KEY (event_id, position_index),
                    FOREIGN KEY (event_id) REFERENCES reading_analytics(event_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_reading_analytics_date ON reading_analytics(occurred_date);
                CREATE INDEX IF NOT EXISTS idx_reading_analytics_source ON reading_analytics(source);
                CREATE INDEX IF NOT EXISTS idx_reading_analytics_category ON reading_analytics(question_category);
                CREATE INDEX IF NOT EXISTS idx_reading_cards_card ON reading_cards(card_id, orientation);
                """
            )

    def record_reading(
        self,
        *,
        source: str,
        question_category: str,
        method: str,
        method_result: dict[str, Any],
        language: str,
        persona_id: str | None = None,
    ) -> str:
        result = method_result if isinstance(method_result, dict) else {}
        cards = result.get("cards") if isinstance(result.get("cards"), list) else []
        deck = result.get("deck") if isinstance(result.get("deck"), dict) else {}
        rules = result.get("rules") if isinstance(result.get("rules"), dict) else {}
        category = question_category if question_category in ALLOWED_CATEGORIES else "other"
        event_id = secrets.token_urlsafe(18)
        occurred_date = datetime.now(timezone.utc).date().isoformat()

        event = (
            event_id,
            occurred_date,
            normalize_source(source),
            category,
            str(method or "unknown")[:32],
            str(result.get("spread") or "")[:64] or None,
            str(deck.get("deck_id") or "")[:128] or None,
            str(persona_id or "")[:128] or None,
            normalize_language(language),
            len(cards),
            str(rules.get("draw_mode") or "")[:32] or None,
        )

        card_rows: list[tuple[Any, ...]] = []
        for index, card in enumerate(cards):
            if not isinstance(card, dict):
                continue
            card_id = str(card.get("card_id") or card.get("id") or "").strip()
            if not card_id:
                continue
            orientation = str(card.get("orientation") or "upright").lower()
            if orientation not in {"upright", "reversed"}:
                orientation = "upright"
            card_rows.append(
                (
                    event_id,
                    index,
                    card_id[:160],
                    orientation,
                    str(card.get("position") or "")[:64] or None,
                )
            )

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO reading_analytics (
                    event_id, occurred_date, source, question_category, method,
                    spread, deck_id, persona_id, language, card_count, draw_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                event,
            )
            if card_rows:
                conn.executemany(
                    """
                    INSERT INTO reading_cards (
                        event_id, position_index, card_id, orientation, position
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    card_rows,
                )
        return event_id

    def summary(self, *, days: int = 30) -> dict[str, Any]:
        days = max(1, min(int(days), 3650))
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM reading_analytics
                WHERE occurred_date >= date('now', ?)
                ORDER BY occurred_date DESC
                """,
                (f"-{days - 1} days",),
            ).fetchall()
            card_rows = conn.execute(
                """
                SELECT rc.card_id, rc.orientation, COUNT(*) AS count
                FROM reading_cards rc
                JOIN reading_analytics ra ON ra.event_id = rc.event_id
                WHERE ra.occurred_date >= date('now', ?)
                GROUP BY rc.card_id, rc.orientation
                ORDER BY count DESC, rc.card_id ASC
                """,
                (f"-{days - 1} days",),
            ).fetchall()

        def counts(key: str) -> dict[str, int]:
            counter = Counter(str(row[key] or "unknown") for row in rows)
            return dict(sorted(counter.items(), key=lambda item: (-item[1], item[0])))

        return {
            "privacy": {
                "question_stored": False,
                "answer_stored": False,
                "ip_stored": False,
                "referrer_url_stored": False,
                "persistent_visitor_id": False,
            },
            "window_days": days,
            "total_readings": len(rows),
            "by_source": counts("source"),
            "by_category": counts("question_category"),
            "by_method": counts("method"),
            "by_spread": counts("spread"),
            "by_deck": counts("deck_id"),
            "by_language": counts("language"),
            "by_draw_mode": counts("draw_mode"),
            "cards": [dict(row) for row in card_rows],
        }
