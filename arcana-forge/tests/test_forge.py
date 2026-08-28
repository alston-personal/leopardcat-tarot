import pytest

from arcana_forge import ForgeRegistry, StyleSpec, SubjectSpec, forge
from arcana_forge.exporters.divination_os import export_divination_os, export_tarot_deck_manifest


def test_same_api_forges_tarot_and_iching():
    tarot = forge(system="tarot-rws", subject="Taiwan leopard cat", style="sacred mountain watercolor")
    iching = forge(system="iching-zhouyi", subject="Taiwan leopard cat", style="sacred Chinese ink")
    assert len(tarot.units) == 78
    assert len(iching.units) == 64
    assert tarot.units[0].unit.name == "The Fool"
    assert iching.units[0].unit.name == "乾"


def test_subject_and_style_do_not_replace_symbolic_identity():
    collection = forge(
        system="iching-zhouyi",
        subject=SubjectSpec("cyberpunk fox"),
        style=StyleSpec("neon ukiyo-e"),
    )
    first = collection.units[0]
    assert first.unit.name == "乾"
    assert "乾" in first.invariants[-1]
    assert "cyberpunk fox" in first.prompt
    assert "neon ukiyo-e" in first.prompt


def test_divination_os_export_keeps_mechanics_outside_forge():
    collection = forge(system="tarot-rws", subject="leopard cat", style="watercolor", title="LeopardCat Tarot")
    payload = export_divination_os(collection, collection_id="leopardcat-tarot")
    assert payload["symbolic_system"] == "tarot-rws"
    assert len(payload["units"]) == 78
    assert "spread" not in payload
    assert "draw" not in payload
    assert "casting" not in payload


def test_tarot_manifest_matches_current_divination_os_shape():
    collection = forge(system="tarot-rws", subject="leopard cat", style="watercolor", title="LeopardCat Tarot")
    manifest = export_tarot_deck_manifest(collection, deck_id="leopardcat-generated", default_persona="leopardcat")
    assert manifest["schema_version"] == 1
    assert manifest["deck_id"] == "leopardcat-generated"
    assert manifest["card_count"] == 78
    assert manifest["default_persona"] == "leopardcat"
    assert set(manifest["cards"][0]) >= {"id", "title", "meanings", "image"}
    assert manifest["cards"][0]["title"]["en"] == "The Fool"


def test_iching_is_not_faked_as_tarot_deck():
    collection = forge(system="iching-zhouyi", subject="leopard cat", style="ink")
    with pytest.raises(ValueError, match="Tarot-only"):
        export_tarot_deck_manifest(collection, deck_id="wrong")


def test_registry_is_plugin_based():
    registry = ForgeRegistry.defaults()
    assert registry.get("tarot-rws").id == "tarot-rws"
    assert registry.get("iching-zhouyi").id == "iching-zhouyi"
