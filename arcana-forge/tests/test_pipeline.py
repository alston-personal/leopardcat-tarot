import json

from arcana_forge import ForgePipeline, ForgeRegistry, JsonSymbolicSystem, SvgProofProvider


def test_pipeline_builds_valid_visual_collection(tmp_path):
    build = ForgePipeline().build(
        system="tarot-rws",
        subject="Taiwan leopard cat",
        style="sacred mountain watercolor",
        provider=SvgProofProvider(),
        output_dir=tmp_path / "cards",
        title="LeopardCat Tarot",
    )
    assert len(build.assets) == 78
    manifest = build.export_tarot_deck(deck_id="leopardcat-generated", default_persona="leopardcat")
    assert manifest["card_count"] == 78
    assert manifest["cards"][0]["image"].endswith("major-00.svg")


def test_json_system_is_a_real_plugin(tmp_path):
    path = tmp_path / "system.json"
    path.write_text(json.dumps({
        "id": "tiny-oracle",
        "version": "1",
        "units": [
            {"id": "dawn", "name": "Dawn", "archetype": "beginning and emergence", "required_cues": ["horizon"]},
            {"id": "dusk", "name": "Dusk", "archetype": "closure and transition", "required_cues": ["setting light"]},
        ],
    }), encoding="utf-8")
    registry = ForgeRegistry.defaults()
    registry.register(JsonSymbolicSystem.from_file(path))
    collection = ForgePipeline(registry).compile(system="tiny-oracle", subject="fox", style="woodcut")
    assert [item.unit.id for item in collection.units] == ["dawn", "dusk"]
    assert "fox" in collection.units[0].prompt
