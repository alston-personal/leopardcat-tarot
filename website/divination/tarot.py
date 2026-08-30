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


def shuffle(cards: list[dict[str, Any]], *, reversal_rate: float, rng: random.Random) -> list[dict[str, Any]]:
    """Create one hidden physical deck state: order + orientation are fixed before selection."""
    ordered = list(cards)
    rng.shuffle(ordered)
    return [
        {
            "card": card,
            "draw_index": idx + 1,  # public/manual API is intentionally 1-based
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

        hidden_deck = shuffle(cards, reversal_rate=reversal_rate, rng=rng)
        requested_indices = input_data.get("draw_indices")
        if requested_indices is None:
            # Existing automatic mode: shuffle first, then draw the required number from the top.
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
            "cards": results,
            "rules": {
                "without_replacement": True,
                # Kept for backward compatibility: orientation becomes visible at draw/reveal time.
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
