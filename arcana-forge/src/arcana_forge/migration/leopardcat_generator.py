from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any

from arcana_forge.schema import SubjectPack, SubjectSpec, UnitVisualOverride

_MINOR_PREFIX = {"cu": "cups", "pe": "pentacles", "sw": "swords", "wa": "wands"}


def legacy_card_to_unit_id(card: dict[str, Any]) -> str:
    card_id = str(card.get("id") or "")
    arcana = str(card.get("arcana") or "")
    if arcana == "major":
        number = int(card.get("number"))
        if not 0 <= number <= 21:
            raise ValueError(f"invalid major arcana number: {number}")
        return f"major-{number:02d}"
    match = re.match(r"^card-(cu|pe|sw|wa)-(\d{2})-", card_id)
    if not match:
        raise ValueError(f"cannot map legacy minor card id: {card_id}")
    prefix, rank = match.groups()
    return f"{_MINOR_PREFIX[prefix]}-{int(rank):02d}"


def legacy_card_to_override(card: dict[str, Any]) -> UnitVisualOverride:
    generation = card.get("generation") if isinstance(card.get("generation"), dict) else {}
    meanings = card.get("meanings") if isinstance(card.get("meanings"), dict) else {}
    narrative = str(generation.get("narrative") or "").strip()
    if not narrative:
        narrative = str(generation.get("image_prompt") or "").strip()
    metadata = {
        "legacy_id": card.get("id"),
        "legacy_slug": card.get("slug"),
        "ecology": card.get("ecology") if isinstance(card.get("ecology"), dict) else {},
        "ornaments": card.get("ornaments") if isinstance(card.get("ornaments"), list) else [],
        "website": card.get("website") if isinstance(card.get("website"), dict) else {},
        "palette": card.get("palette") if isinstance(card.get("palette"), dict) else {},
    }
    return UnitVisualOverride(
        scene=narrative or None,
        meanings={
            key: str(meanings.get(key) or "").strip()
            for key in ("upright", "reversed")
            if str(meanings.get(key) or "").strip()
        },
        metadata=metadata,
    )


def import_legacy_leopardcat_cards(cards_dir: str | Path) -> SubjectPack:
    root = Path(cards_dir)
    if not root.is_dir():
        raise ValueError(f"legacy cards directory not found: {root}")
    overrides: dict[str, UnitVisualOverride] = {}
    files = sorted(root.glob("*.json"))
    if not files:
        raise ValueError("legacy cards directory contains no JSON card definitions")
    for path in files:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ValueError(f"legacy card file must contain object: {path}")
        unit_id = legacy_card_to_unit_id(value)
        if unit_id in overrides:
            raise ValueError(f"duplicate legacy mapping for {unit_id}")
        overrides[unit_id] = legacy_card_to_override(value)
    return SubjectPack(
        id="leopardcat-legacy-v1",
        subject=SubjectSpec(
            concept="Taiwan leopard cat",
            role="recurring symbolic protagonist",
            traits=(
                "narrow small-cat facial structure",
                "white stripes between the eyes",
                "white muzzle",
                "large white spots behind black ears",
                "slender agile feline build",
            ),
        ),
        unit_overrides=overrides,
        metadata={
            "source": "leopardcat-tarot/generator/cards",
            "migrated_card_count": len(overrides),
            "migration": "arcana-forge legacy LeopardCat importer",
        },
    )
