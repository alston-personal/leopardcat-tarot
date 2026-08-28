from pathlib import Path

from arcana_forge import StyleSpec, forge
from arcana_forge.exporters.divination_os import export_tarot_deck_manifest
from arcana_forge.migration import import_legacy_leopardcat_cards, legacy_card_to_unit_id


ROOT = Path(__file__).resolve().parents[2]
LEGACY_CARDS = ROOT / "generator" / "cards"


def test_legacy_card_ids_map_to_arcanaforge_tarot_ids():
    assert legacy_card_to_unit_id({"id": "card-00-the-fool", "arcana": "major", "number": 0}) == "major-00"
    assert legacy_card_to_unit_id({"id": "card-cu-01-ace-of-cups", "arcana": "minor"}) == "cups-01"
    assert legacy_card_to_unit_id({"id": "card-sw-14-king-of-swords", "arcana": "minor"}) == "swords-14"


def test_real_leopardcat_generator_migrates_all_78_cards():
    pack = import_legacy_leopardcat_cards(LEGACY_CARDS)
    assert pack.metadata["migrated_card_count"] == 78
    assert len(pack.unit_overrides) == 78
    assert set(pack.unit_overrides) >= {"major-00", "cups-01", "swords-14", "wands-14", "pentacles-14"}


def test_migrated_subject_pack_preserves_narrative_meanings_and_system_invariants():
    pack = import_legacy_leopardcat_cards(LEGACY_CARDS)
    collection = forge(
        system="tarot-rws",
        subject=pack,
        style=StyleSpec(
            "LeopardCat legacy mystical lithography",
            medium="1900s mystical lithography with bold ink outlines",
            composition_rules=("2:3 vertical", "full bleed"),
        ),
        title="LeopardCat Tarot",
    )
    assert len(collection.units) == 78

    fool = next(item for item in collection.units if item.unit.id == "major-00")
    assert "juvenile anthropomorphic Taiwan leopard cat" in fool.scene
    assert fool.meanings["upright"].startswith("New beginnings")
    assert fool.visual_metadata["ecology"]["species_focus"] == "Taiwan leopard cat"
    assert any("The Fool" in invariant for invariant in fool.invariants)

    ace = next(item for item in collection.units if item.unit.id == "cups-01")
    assert "Source of Life" in ace.scene
    assert ace.meanings["reversed"].startswith("Blocked emotions")
    assert any("cup" in invariant.lower() for invariant in ace.invariants)


def test_migrated_deck_export_preserves_legacy_meanings_and_visual_metadata():
    pack = import_legacy_leopardcat_cards(LEGACY_CARDS)
    collection = forge(system="tarot-rws", subject=pack, style="legacy", title="LeopardCat Tarot")
    manifest = export_tarot_deck_manifest(
        collection,
        deck_id="leopardcat-migrated",
        creator="LeopardCat Tarot",
        default_persona="leopardcat",
    )
    assert manifest["card_count"] == 78
    fool = next(card for card in manifest["cards"] if card["id"] == "major-00")
    assert fool["meanings"]["upright"].startswith("New beginnings")
    assert fool["meanings"]["reversed"].startswith("Naivety")
    assert fool["arcana_forge"]["visual_metadata"]["ecology"]["risk_theme"] == "road mortality during dispersal"
    assert fool["arcana_forge"]["subject_pack_id"] == "leopardcat-legacy-v1"
