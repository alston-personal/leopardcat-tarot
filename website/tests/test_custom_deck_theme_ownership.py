import json
from pathlib import Path

from divination.decks import DeckRegistry
from divination.publishing import DeckPublisher


def _card():
    return {"id": "x", "title": {"zh": "X"}, "meanings": {"upright": "u", "reversed": "r"}, "image": "/x.webp"}


def test_old_custom_manifest_defaults_theme_without_migration(tmp_path):
    builtin = tmp_path / "manifest.json"
    builtin.write_text(json.dumps([_card()]), encoding="utf-8")
    root = tmp_path / "custom"
    d = root / "legacy-deck"
    d.mkdir(parents=True)
    (d / "deck.json").write_text(json.dumps({"name": "Legacy", "cards": [_card()]}), encoding="utf-8")
    deck = DeckRegistry(builtin, root).get("legacy-deck")
    assert deck.default_theme == "minimal-light"


def test_public_info_exposes_owned_theme(tmp_path):
    builtin = tmp_path / "manifest.json"
    builtin.write_text(json.dumps([_card()]), encoding="utf-8")
    root = tmp_path / "custom"
    d = root / "owned-theme"
    d.mkdir(parents=True)
    (d / "deck.json").write_text(json.dumps({"name": "Owned", "default_theme": "midnight", "cards": [_card()]}), encoding="utf-8")
    assert DeckRegistry(builtin, root).public_info("owned-theme")["default_theme"] == "midnight"


def test_sources_keep_url_override_and_creator_persists_theme():
    website = Path(__file__).resolve().parents[1]
    creator = (website / "public" / "creator.js").read_text(encoding="utf-8")
    main = (website / "main.js").read_text(encoding="utf-8")
    read = (website / "public" / "read.js").read_text(encoding="utf-8")
    assert "theme: selectedThemeId" in creator
    assert "window.explicitThemeId" in main
    assert "!window.explicitThemeId && deck.default_theme" in main
    assert "deck.default_theme||defaultTheme" in read
    assert "theme: qs.get('theme') || ''" in read
