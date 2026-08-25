from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .core import DivinationError

_SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")


@dataclass(frozen=True)
class Deck:
    deck_id: str
    name: str
    creator: str
    description: str
    cards: list[dict[str, Any]]
    reversals: bool = True
    source: str = "builtin"


class DeckRegistry:
    def __init__(self, default_manifest: str | Path, custom_root: str | Path) -> None:
        self.default_manifest = Path(default_manifest)
        self.custom_root = Path(custom_root)
        self.custom_root.mkdir(parents=True, exist_ok=True)

    def get(self, deck_id: str | None) -> Deck:
        if not deck_id or deck_id == "leopardcat":
            cards = json.loads(self.default_manifest.read_text(encoding="utf-8"))
            return Deck("leopardcat", "靈山靈貓・石虎塔羅", "LeopardCat Tarot", "", cards, True, "builtin")
        if not _SAFE_ID.fullmatch(deck_id):
            raise DivinationError("invalid deck id")
        path = self.custom_root / deck_id / "deck.json"
        if not path.exists():
            raise DivinationError(f"unknown deck: {deck_id}")
        data = json.loads(path.read_text(encoding="utf-8"))
        cards = data.get("cards") or []
        if not isinstance(cards, list) or not cards:
            raise DivinationError("deck has no cards")
        return Deck(
            deck_id=deck_id,
            name=str(data.get("name") or deck_id),
            creator=str(data.get("creator") or ""),
            description=str(data.get("description") or ""),
            cards=cards,
            reversals=bool(data.get("reversals", False)),
            source="custom",
        )

    def public_info(self, deck_id: str) -> dict[str, Any]:
        d = self.get(deck_id)
        return {
            "deck_id": d.deck_id,
            "name": d.name,
            "creator": d.creator,
            "description": d.description,
            "card_count": len(d.cards),
            "reversals": d.reversals,
            "source": d.source,
        }
