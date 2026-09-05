from divination.ai_gateway import MasterExperienceQualityGate, AIUnavailable


def test_dense_japanese_response_uses_language_aware_floor():
    gate = MasterExperienceQualityGate()
    text = "今は結論を急ぐより、足元の仕事を一つずつ整える時期です。周囲との調整を丁寧に進めれば、次の機会は自然に見えてきます。"
    assert 48 <= len(text) < 80
    assert gate.validate(text) == text


def test_dense_traditional_chinese_response_uses_language_aware_floor():
    gate = MasterExperienceQualityGate()
    text = "現在最重要的不是立刻做出決定，而是先把手上的責任與資源整理清楚。當你把真正想守住的核心確認後，下一步會比現在更明確。"
    assert 48 <= len(text) < 80
    assert gate.validate(text) == text


def test_short_dense_response_still_fails():
    gate = MasterExperienceQualityGate()
    try:
        gate.validate("焦らず、今できることを整えてください。")
    except AIUnavailable as exc:
        assert exc.code == "quality_too_short"
    else:
        raise AssertionError("short dense response must fail")


def test_english_keeps_original_floor():
    gate = MasterExperienceQualityGate()
    text = "Take a little more time to organize what matters before making the next move."
    assert len(text) < 80
    try:
        gate.validate(text)
    except AIUnavailable as exc:
        assert exc.code == "quality_too_short"
    else:
        raise AssertionError("English response below original floor must fail")
