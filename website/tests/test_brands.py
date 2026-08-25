import json
from pathlib import Path

from divination.brands import BrandRegistry
from divination.decks import DeckRegistry


def _registry(tmp_path: Path) -> BrandRegistry:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps([{"id": "card-00", "title": {"zh": "愚者", "en": "The Fool"}, "image": "art/fool.webp"}]), encoding="utf-8")
    custom = tmp_path / "custom"
    deck_dir = custom / "test-brand"
    deck_dir.mkdir(parents=True)
    (deck_dir / "deck.json").write_text(json.dumps({
        "name": "TEST Brand",
        "creator": "AAA",
        "description": "My deck",
        "cards": [{"id": "c1", "title": {"zh": "測試牌", "en": "Test Card"}, "image": "/api/v1/decks/test-brand/images/card-001.webp"}],
    }), encoding="utf-8")
    return BrandRegistry(DeckRegistry(manifest, custom))


def test_leopardcat_brand_pack(tmp_path):
    brand = _registry(tmp_path).public_info("leopardcat")
    assert brand["brand_id"] == "leopardcat"
    assert "石虎塔羅" in brand["share_title"]["zh"]
    assert brand["file_prefix"] == "leopardcat-tarot"


def test_custom_brand_has_no_leopardcat_leak(tmp_path):
    brand = _registry(tmp_path).public_info("test-brand")
    serialized = json.dumps(brand, ensure_ascii=False)
    assert brand["brand_id"] == "deck:test-brand"
    assert brand["app_name"] == "TEST Brand"
    assert brand["share_site_tag"]["zh"] == "牌卡創作：AAA"
    assert "TEST Brand" in brand["share_copy_template"]["zh"]
    assert "石虎" not in serialized
    assert "LeopardCat" not in serialized
