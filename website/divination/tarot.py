from __future__ import annotations

import random
from typing import Any

from .core import DivinationError
from .decks import DeckRegistry


SPREADS: dict[str, list[tuple[str, str]]] = {
    "single": [("guidance", "核心指引")],
    "clarifier": [("clarifier", "補充訊息")],
    "three_card": [
        ("past", "過去／根源"),
        ("present", "現在／核心"),
        ("future", "未來／發展"),
    ],
    "situation_advice": [
        ("situation", "現況"),
        ("obstacle", "阻礙／盲點"),
        ("advice", "建議／下一步"),
    ],
    "decision": [
        ("situation", "現況"),
        ("path_a", "選擇 A 的能量"),
        ("path_b", "選擇 B 的能量"),
    ],
    "relationship": [
        ("self", "你的狀態"),
        ("other", "對方的狀態"),
        ("bond", "關係核心"),
        ("challenge", "關係課題"),
        ("direction", "可能發展"),
    ],
    "career": [
        ("present", "目前位置"),
        ("strength", "可運用的優勢"),
        ("challenge", "主要阻力"),
        ("opportunity", "可把握的機會"),
        ("action", "建議行動"),
    ],
    "path": [
        ("origin", "目前起點"),
        ("lesson", "核心課題"),
        ("resource", "可運用資源"),
        ("next_step", "下一步"),
        ("direction", "發展方向"),
    ],
    "celtic_cross": [
        ("present", "核心現況"),
        ("cross", "交叉影響／阻力"),
        ("foundation", "深層根源"),
        ("recent_past", "近期過去"),
        ("possibility", "可見可能性"),
        ("near_future", "近期發展"),
        ("self", "你的內在位置"),
        ("environment", "外在環境"),
        ("hopes_fears", "期待與擔憂"),
        ("outcome", "整體走向"),
    ],
}

SPREAD_INFO: dict[str, dict[str, Any]] = {
    "single": {"label": "單張指引", "intent": "guidance", "complexity": "low"},
    "clarifier": {"label": "補充牌", "intent": "clarification", "complexity": "low"},
    "three_card": {"label": "時間流三牌", "intent": "timeline", "complexity": "medium"},
    "situation_advice": {"label": "現況・阻礙・建議", "intent": "guidance", "complexity": "medium"},
    "decision": {"label": "選擇分析", "intent": "decision", "complexity": "medium"},
    "relationship": {"label": "關係五牌", "intent": "relationship", "complexity": "medium"},
    "career": {"label": "職涯五牌", "intent": "career", "complexity": "medium"},
    "path": {"label": "道路五牌", "intent": "direction", "complexity": "medium"},
    "celtic_cross": {"label": "凱爾特十字", "intent": "deep_reading", "complexity": "high"},
}


def spread_catalog() -> list[dict[str, Any]]:
    """Public, stable spread capability catalog.

    The catalog is derived from the canonical registry so UI/API consumers never
    maintain a second card-count table.
    """
    return [
        {
            "id": spread_id,
            "name": SPREAD_INFO[spread_id]["label"],
            "card_count": len(positions),
            "intent": SPREAD_INFO[spread_id]["intent"],
            "complexity": SPREAD_INFO[spread_id]["complexity"],
        }
        for spread_id, positions in SPREADS.items()
    ]


def plan_spread(question: str) -> dict[str, Any]:
    """Choose one canonical spread for automatic Tarot readings.

    This is deliberately server-side and source-agnostic: typed questions and
    resolved Threads text arrive here as plain question text and are planned by
    the same authority. Downstream render/share code must consume the resulting
    reading receipt rather than re-plan it.
    """
    q = str(question or "").strip()
    lower = q.lower()

    def has(*markers: str) -> bool:
        return any(marker in lower for marker in markers)

    if has("補牌", "補充", "釐清", "clarify", "clarifier"):
        spread_id = "clarifier"
        reason = "question explicitly asks for clarification"
    elif has("感情", "關係", "對方", "他對我", "她對我", "我們之間", "relationship", "love"):
        spread_id = "relationship"
        reason = "relationship questions benefit from both parties, bond, challenge, and direction"
    elif has("哪個", "二選一", "兩個選擇", "選擇 a", "選擇 b", "比較", "vs", " or "):
        spread_id = "decision"
        reason = "question compares alternatives"
    elif has("工作", "職涯", "轉職", "換工作", "升遷", "事業", "career", "job", "work"):
        spread_id = "career"
        reason = "career question needs strengths, obstacles, opportunity, and action"
    elif has("人生方向", "方向", "道路", "下一步怎麼走", "該往哪", "path", "direction"):
        spread_id = "path"
        reason = "direction question needs a broader action path"
    elif has("凱爾特", "完整分析", "深入分析", "全面分析", "整體局勢", "複雜", "deep reading", "celtic") or len(q) >= 120:
        spread_id = "celtic_cross"
        reason = "high-complexity question needs a deep multi-position reading"
    elif has("未來", "發展", "接下來", "過去", "時間", "走向", "future", "next", "timeline"):
        spread_id = "three_card"
        reason = "question is primarily about change over time"
    elif has("今天", "今日", "此刻", "現在給我一個指引", "一句指引", "抽一張", "one card", "daily guidance") and len(q) <= 48:
        spread_id = "single"
        reason = "question explicitly asks for a compact present-moment guidance"
    else:
        spread_id = "situation_advice"
        reason = "general question is best served by situation, obstacle, and advice rather than a binary answer"

    info = SPREAD_INFO[spread_id]
    return {
        "spread": spread_id,
        "card_count": len(SPREADS[spread_id]),
        "intent": info["intent"],
        "complexity": info["complexity"],
        "reason": reason,
    }


def shuffle(cards: list[dict[str, Any]], *, reversal_rate: float, rng: random.Random) -> list[dict[str, Any]]:
    """Create one hidden physical deck state: order + orientation are fixed before selection."""
    ordered = list(cards)
    rng.shuffle(ordered)
    return [
        {
            "card": card,
            "draw_index": idx + 1,
            "orientation": "reversed" if rng.random() < reversal_rate else "upright",
        }
        for idx, card in enumerate(ordered)
    ]


def draw(
    shuffled: list[dict[str, Any]],
    indices: list[int],
    positions: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Select positions from an already shuffled deck. Auto/manual both call this function."""
    if len(indices) != len(positions):
        raise DivinationError(f"draw requires {len(positions)} indices")
    if len(set(indices)) != len(indices):
        raise DivinationError("draw indices must be unique")
    if any(not isinstance(i, int) or isinstance(i, bool) or i < 1 or i > len(shuffled) for i in indices):
        raise DivinationError(f"draw indices must be between 1 and {len(shuffled)}")

    results: list[dict[str, Any]] = []
    for index, (position, position_label) in zip(indices, positions):
        entry = shuffled[index - 1]
        card = entry["card"]
        orientation = entry["orientation"]
        meanings = card.get("meanings") or {}
        selected_meaning = meanings.get(orientation) or meanings.get("upright") or card.get("meaning") or ""
        results.append({
            "card_id": card.get("id"),
            "title": card.get("title") or {},
            "arcana": card.get("arcana"),
            "suit": card.get("suit"),
            "number": card.get("number"),
            "position": position,
            "position_label": position_label,
            "orientation": orientation,
            "draw_index": index,
            "meaning": selected_meaning,
            "upright_meaning": meanings.get("upright"),
            "reversed_meaning": meanings.get("reversed"),
            "ecology": card.get("ecology"),
            "image": card.get("image"),
        })
    return results


class TarotMethod:
    method_id = "tarot"

    def __init__(self, decks: DeckRegistry) -> None:
        self.decks = decks

    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]:
        deck = self.decks.get(str(input_data.get("deck_id") or "leopardcat"))
        cards = deck.cards
        requested_spread = str(input_data.get("spread") or "single")
        if requested_spread == "auto":
            plan = plan_spread(question)
            spread_id = plan["spread"]
        else:
            spread_id = requested_spread
            if spread_id not in SPREADS:
                raise DivinationError(f"unsupported tarot spread: {spread_id}")
            info = SPREAD_INFO[spread_id]
            plan = {
                "spread": spread_id,
                "card_count": len(SPREADS[spread_id]),
                "intent": info["intent"],
                "complexity": info["complexity"],
                "reason": "explicit spread selected by user",
            }

        positions = SPREADS[spread_id]
        if len(cards) < len(positions):
            raise DivinationError(f"deck has {len(cards)} cards but spread requires {len(positions)}")

        requested_rate = float(input_data.get("reversal_rate", 0.5))
        if not 0.0 <= requested_rate <= 1.0:
            raise DivinationError("reversal_rate must be between 0 and 1")
        reversal_rate = requested_rate if deck.reversals else 0.0

        hidden_deck = shuffle(cards, reversal_rate=reversal_rate, rng=rng)
        requested_indices = input_data.get("draw_indices")
        if requested_indices is None:
            draw_indices = list(range(1, len(positions) + 1))
            draw_mode = "auto"
        else:
            if not isinstance(requested_indices, list):
                raise DivinationError("draw_indices must be a list")
            draw_indices = requested_indices
            draw_mode = "manual"

        results = draw(hidden_deck, draw_indices, positions)

        return {
            "method": "tarot",
            "deck": {
                "deck_id": deck.deck_id,
                "name": deck.name,
                "creator": deck.creator,
                "card_count": len(deck.cards),
                "reversals": deck.reversals,
                "source": deck.source,
                "card_back": deck.card_back,
            },
            "spread": spread_id,
            "spread_plan": plan,
            "cards": results,
            "rules": {
                "without_replacement": True,
                "orientation_decided_at_draw_time": True,
                "orientation_assigned_at_shuffle_time": True,
                "orientation_hidden_until_reveal": True,
                "shuffle_before_draw": True,
                "draw_indices_are_1_based": True,
                "draw_mode": draw_mode,
                "draw_indices": draw_indices,
                "reversal_rate": reversal_rate,
            },
        }
