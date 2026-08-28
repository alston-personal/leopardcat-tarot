from arcana_forge import CallableGenerationProvider, PromptFileProvider, SvgProofProvider, forge, generate_collection


def test_prompt_provider_materializes_one_asset_per_symbolic_unit(tmp_path):
    collection = forge(system="iching-zhouyi", subject="Taiwan leopard cat", style="sacred Chinese ink")
    assets = generate_collection(collection, PromptFileProvider(), output_dir=tmp_path)
    assert len(assets) == 64
    first = tmp_path / "hexagram-01.prompt.txt"
    assert first.exists()
    text = first.read_text(encoding="utf-8")
    assert "乾" in text
    assert "Taiwan leopard cat" in text
    assert "INVARIANTS" in text


def test_svg_provider_produces_visual_collection(tmp_path):
    collection = forge(system="tarot-rws", subject="Taiwan leopard cat", style="sacred mountain watercolor")
    assets = generate_collection(collection, SvgProofProvider(), output_dir=tmp_path)
    assert len(assets) == 78
    first = tmp_path / "major-00.svg"
    text = first.read_text(encoding="utf-8")
    assert "The Fool" in text
    assert "semantic proof" in text


def test_callable_provider_is_the_model_adapter_boundary(tmp_path):
    seen = []
    def fake_model(prompt, output_path):
        seen.append(prompt)
        output_path.write_bytes(b"fake-image")
        return {"model": "fake"}

    collection = forge(system="iching-zhouyi", subject="leopard cat", style="ink")
    provider = CallableGenerationProvider("test-model", fake_model)
    assets = generate_collection(collection, provider, output_dir=tmp_path)
    assert len(assets) == 64
    assert assets[0].metadata["model"] == "fake"
    assert "乾" in seen[0]


def test_iching_preserves_canonical_line_identity():
    collection = forge(system="iching-zhouyi", subject="leopard cat", style="ink")
    assert collection.units[0].unit.metadata["line_pattern_bottom_to_top"] == "111111"
    assert collection.units[1].unit.metadata["line_pattern_bottom_to_top"] == "000000"
    assert collection.units[-1].unit.metadata["upper_trigram"] == "fire"
    assert collection.units[-1].unit.metadata["lower_trigram"] == "water"
