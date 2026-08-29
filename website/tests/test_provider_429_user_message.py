from pathlib import Path


def test_provider_429_message_does_not_claim_free_quota_exhaustion():
    js = (Path(__file__).resolve().parents[1] / "main.js").read_text(encoding="utf-8")
    assert "provider_429_billing_or_quota_state" in js
    assert "供應商端額度／帳務狀態異常" in js
    assert "今天的免費 AI 額度暫時用完" not in js
