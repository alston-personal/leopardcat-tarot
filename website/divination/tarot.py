from __future__ import annotations

import random
from typing import Any

from .core import DivinationError
from .decks import DeckRegistry


SPREADS: dict[str, list[tuple[str, str]]] = {
    "single": [("guidance", "核心指引")],
    "three_card": [("past", "過去／根源"), ("present", "現在／核心"), ("future", "未來／發展")],
    "decision": [("situation", "現況"), ("path_a", "選擇 A 的能量"), ("path_b", "選擇 B 的能量")],
}


class TarotMethod:
    method_id = "tarot"

    def __init__(self, decks: DeckRegistry) -> None:
        self.decks = decks

    @staticmethod
    def _auto_spread(question: str) -> str:
        q = question.lower()
        decision_markers = ("是否", "要不要", "該不該", "哪個", "選擇", "vs", " or ")
        timeline_markers = ("未來", "發展", "接下來", "過去", "現在", "future", "next")
        if any(x in q for x in decision_markers):
            return "decision"
        if any(x in q for x in timeline_markers):
            return "three_card"
        return "single"

    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]:
        deck = self.decks.get(str(input_data.get("deck_id") or "leopardcat"))
        cards = deck.cards
        spread_id = str(input_data.get("spread") or "single")
        if spread_id == "auto":
            spread_id = self._auto_spread(question)
        if spread_id not in SPREADS:
            raise DivinationError(f"unsupported tarot spread: {spread_id}")

        positions = SPREADS[spread_id]
        if len(cards) < len(positions):
            raise DivinationError(f"deck has {len(cards)} cards but spread requires {len(positions)}")

        requested_rate = float(input_data.get("reversal_rate", 0.5))
        if not 0.0 <= requested_rate <= 1.0:
            raise DivinationError("reversal_rate must be between 0 and 1")
        reversal_rate = requested_rate if deck.reversals else 0.0

        picked = rng.sample(cards, len(positions))
        results: list[dict[str, Any]] = []
        for card, (position, position_label) in zip(picked, positions):
            orientation = "reversed" if rng.random() < reversal_rate else "upright"
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
                "meaning": selected_meaning,
                "upright_meaning": meanings.get("upright"),
                "reversed_meaning": meanings.get("reversed"),
                "ecology": card.get("ecology"),
                "image": card.get("image"),
            })

        return {
            "method": "tarot",
            "deck": {
                "deck_id": deck.deck_id,
                "name": deck.name,
                "creator": deck.creator,
                "card_count": len(deck.cards),
                "reversals": deck.reversals,
                "source": deck.source,
            },
            "spread": spread_id,
            "cards": results,
            "rules": {
                "without_replacement": True,
                "orientation_decided_at_draw_time": True,
                "reversal_rate": reversal_rate,
            },
        }
