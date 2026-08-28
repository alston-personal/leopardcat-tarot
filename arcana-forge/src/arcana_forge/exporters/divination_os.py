from __future__ import annotations

from arcana_forge.schema import SymbolicCollection


def export_divination_os(collection: SymbolicCollection, *, collection_id: str) -> dict:
    """Export system-neutral visual/semantic assets; mechanics stay in Divination OS."""
    return {
        "schema": "divination-os.asset-pack/v0.1",
        "id": collection_id,
        "symbolic_system": collection.system,
        "title": collection.title or collection_id,
        "source": {"generator": "arcana-forge", "schema": collection.schema},
        "subject": collection.subject.concept,
        "style": collection.style.name,
        "units": [
            {
                "id": item.unit.id,
                "number": item.unit.number,
                "name": item.unit.name,
                "archetype": item.unit.archetype,
                "keywords": list(item.unit.keywords),
                "required_cues": list(item.unit.required_cues),
                "scene": item.scene,
                "generation_prompt": item.prompt,
                "metadata": item.unit.metadata,
            }
            for item in collection.units
        ],
    }


def export_tarot_deck_manifest(
    collection: SymbolicCollection,
    *,
    deck_id: str,
    creator: str = "ArcanaForge",
    description: str = "",
    default_persona: str = "master",
    reversals: bool = True,
    image_paths: dict[str, str] | None = None,
) -> dict:
    """Emit the current Divination OS custom Tarot deck.json contract.

    ArcanaForge does not publish/manage ownership tokens; it only compiles the portable manifest.
    """
    if collection.system != "tarot-rws":
        raise ValueError("Divination OS deck.json export is Tarot-only; use the generic asset pack for other systems")
    images = image_paths or {}
    cards = []
    for item in collection.units:
        title = item.unit.name
        upright = item.unit.archetype
        reversed_meaning = f"Shadow, blocked, excessive, or inward expression of: {item.unit.archetype}"
        cards.append({
            "id": item.unit.id,
            "title": {"zh": title, "zh-TW": title, "en": title},
            "meanings": {
                "upright": upright,
                "reversed": reversed_meaning if reversals else upright,
            },
            "image": images.get(item.unit.id, f"images/{item.unit.id}.png"),
            "arcana_forge": {
                "number": item.unit.number,
                "keywords": list(item.unit.keywords),
                "required_cues": list(item.unit.required_cues),
                "metadata": item.unit.metadata,
            },
        })
    return {
        "schema_version": 1,
        "deck_id": deck_id,
        "name": collection.title or deck_id,
        "creator": creator,
        "description": description,
        "reversals": reversals,
        "default_persona": default_persona,
        "card_count": len(cards),
        "cards": cards,
    }
