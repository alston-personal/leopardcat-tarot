from divination.capsules import SCHEMA, build_capsule, compile_prompt, public_handoff


def test_capsule_is_provider_neutral_and_immutable_contract():
    result = {"method":"tarot","spread":"single","cards":[{"card_id":"x","orientation":"reversed"}]}
    capsule = build_capsule(reading_id="rd_test", method="tarot", persona="master", question="我該注意什麼？", lang="zh-TW", method_result=result)
    assert capsule["schema"] == SCHEMA
    assert capsule["result"] == result
    assert capsule["contract"]["immutable_result"] is True
    assert capsule["contract"]["redraw_forbidden"] is True


def test_external_prompts_preserve_capsule_and_provider_destinations():
    capsule = build_capsule(reading_id="rd_test", method="lenormand", persona="master", question="接下來如何？", lang="zh-TW", method_result={"method":"lenormand","cards":[]})
    text = compile_prompt(capsule, "chatgpt")
    assert "divination-reading/1" in text
    assert "Never redraw" in text
    handoff = public_handoff(capsule)
    ids = {x["id"] for x in handoff["providers"]}
    assert ids == {"chatgpt", "claude", "gemini"}
    assert all(x["url"].startswith("https://") for x in handoff["providers"])
