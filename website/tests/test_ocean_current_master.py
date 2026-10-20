from pathlib import Path

from divination import build_default_engine, ReadingRequest


def test_ocean_current_master_is_builtin_and_optional():
    engine = build_default_engine(Path(__file__).resolve().parents[1])
    guide = engine.personas.get("ocean-current-master")
    info = guide.public_info()
    assert info["name"] == "洋流大師"
    assert info["source"] == "builtin"
    assert info["methods"] == ["tarot"]
    assert "master" in engine.personas.capabilities()
    assert "leopardcat" in engine.personas.capabilities()


def test_ocean_current_master_prompt_preserves_card_meaning_and_context():
    engine = build_default_engine(Path(__file__).resolve().parents[1])
    guide = engine.personas.get("ocean-current-master")
    result = {"method": "tarot", "cards": [{"card_id": "card-00-the-fool", "orientation": "upright", "meaning": "新的起點"}]}
    prompt = guide.build_prompt(method_result=result, question="我和朋友怎麼和好？", lang="zh-TW")
    assert "新的起點" in prompt
    assert "不要硬塞政見" in prompt
    assert "不可捏造" in prompt
    assert "我和朋友怎麼和好" in prompt
