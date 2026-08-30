from pathlib import Path
import json


def test_provider_429_message_does_not_claim_free_quota_exhaustion():
    root = Path(__file__).resolve().parents[1]
    js = (root / "main.js").read_text(encoding="utf-8")
    locales = json.loads((root / "public" / "locales_v10.json").read_text(encoding="utf-8"))

    assert "provider_429_billing_or_quota_state" in js
    assert "uiText('provider_429_error'" in js
    assert "今天的免費 AI 額度暫時用完" not in js

    for lang in ("zh", "en", "ja", "ko", "es"):
        message = locales[lang]["common"]["provider_429_error"]
        assert message
        assert "free quota exhausted" not in message.lower()

    assert "供應商端額度／帳務狀態異常" in locales["zh"]["common"]["provider_429_error"]
