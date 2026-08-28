from arcana_forge import PromptFileProvider, forge, generate_collection


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
