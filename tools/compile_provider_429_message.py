from pathlib import Path

p = Path('website/main.js')
s = p.read_text(encoding='utf-8')
old = """function modularErrorMessage(e) {
    if (e?.code === 'free_quota_exhausted' || e?.status === 429) {
        return window.currentLang === 'zh'
            ? '今天的免費 AI 額度暫時用完。牌局已保留，稍後可沿用同一副牌重新祈請。'
            : 'The free AI quota is temporarily exhausted. Your draw is preserved for retry.';
    }
    if (e?.status === 503 || e?.name === 'AbortError') {
"""
new = """function modularErrorMessage(e) {
    if (e?.code === 'provider_429_billing_or_quota_state' || e?.status === 429) {
        return window.currentLang === 'zh'
            ? 'Gemini 目前回報供應商端額度／帳務狀態異常。牌局已保留，稍後可沿用同一副牌重新祈請。'
            : 'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.';
    }
    if (e?.code === 'free_quota_exhausted') {
        return window.currentLang === 'zh'
            ? '免費 AI 額度目前不可用。牌局已保留，稍後可沿用同一副牌重新祈請。'
            : 'Free AI capacity is currently unavailable. Your draw is preserved for retry.';
    }
    if (e?.status === 503 || e?.name === 'AbortError') {
"""
assert old in s, 'target error-message block changed'
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')

Path('website/tests/test_provider_429_user_message.py').write_text('''from pathlib import Path\n\n\ndef test_provider_429_message_does_not_claim_free_quota_exhaustion():\n    js = (Path(__file__).resolve().parents[1] / "main.js").read_text(encoding="utf-8")\n    assert "provider_429_billing_or_quota_state" in js\n    assert "供應商端額度／帳務狀態異常" in js\n    assert "今天的免費 AI 額度暫時用完" not in js\n''', encoding='utf-8')
