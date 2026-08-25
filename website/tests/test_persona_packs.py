import json
from pathlib import Path

from divination.decks import DeckRegistry
from divination.personas import GenericMasterPersona, persona_public_info


def test_deck_defaults_are_data_driven(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{"id": "card-1", "title": {"zh": "一"}}]), encoding="utf-8")
    custom = tmp_path / "custom"
    custom.mkdir()

    legacy = custom / "legacy-deck"
    legacy.mkdir()
    (legacy / "deck.json").write_text(json.dumps({
        "name": "Legacy",
        "cards": [{"id": "card-1", "title": {"zh": "一"}, "meanings": {"upright": "x"}}]
    }), encoding="utf-8")

    explicit = custom / "angel-deck"
    explicit.mkdir()
    (explicit / "deck.json").write_text(json.dumps({
        "name": "Angel",
        "default_persona": "angel-guide",
        "cards": [{"id": "card-1", "title": {"zh": "一"}, "meanings": {"upright": "x"}}]
    }), encoding="utf-8")

    decks = DeckRegistry(manifest, custom)
    assert decks.get("leopardcat").default_persona == "leopardcat"
    assert decks.get("legacy-deck").default_persona == "master"
    assert decks.get("angel-deck").default_persona == "angel-guide"
    assert decks.public_info("angel-deck")["default_persona"] == "angel-guide"


def test_persona_pack_has_public_metadata():
    info = persona_public_info(GenericMasterPersona())
    assert info["persona_id"] == "master"
    assert info["name"] == "通用解牌師"
    assert info["source"] == "builtin"
