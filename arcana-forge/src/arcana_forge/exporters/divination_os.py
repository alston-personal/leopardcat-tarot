from __future__ import annotations

from arcana_forge.schema import SymbolicCollection


def export_divination_os(collection: SymbolicCollection, *, collection_id: str) -> dict:
    """Export visual/semantic assets only; divination mechanics remain downstream."""
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
