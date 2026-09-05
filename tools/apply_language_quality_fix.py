from pathlib import Path

path = Path('website/divination/ai_gateway.py')
text = path.read_text(encoding='utf-8')
needle = '''    def validate(self, text: str) -> str:\n        value = str(text or "").strip()\n        if len(value) < self.min_chars:\n            raise AIUnavailable("quality_too_short", "AI 大師回應未達品質門檻，已嘗試其他可用引擎")\n'''
replacement = '''    DENSE_SCRIPT = re.compile(r"[\\u3040-\\u30ff\\u3400-\\u4dbf\\u4e00-\\u9fff\\uac00-\\ud7af]")\n\n    def _minimum_chars_for(self, value: str) -> int:\n        dense = len(self.DENSE_SCRIPT.findall(value))\n        ratio = dense / max(1, len(value))\n        if dense >= 24 and ratio >= 0.35:\n            return max(40, int(self.min_chars * 0.6))\n        return self.min_chars\n\n    def validate(self, text: str) -> str:\n        value = str(text or "").strip()\n        if len(value) < self._minimum_chars_for(value):\n            raise AIUnavailable("quality_too_short", "AI 大師回應未達品質門檻，已嘗試其他可用引擎")\n'''
if needle not in text:
    raise SystemExit('quality gate needle not found')
path.write_text(text.replace(needle, replacement, 1), encoding='utf-8')

case = Path('website/tests/test_language_aware_master_quality.py')
case.write_text('''from divination.ai_gateway import MasterExperienceQualityGate, AIUnavailable\n\n\ndef test_dense_japanese_response_uses_language_aware_floor():\n    gate = MasterExperienceQualityGate()\n    text = "今は結論を急ぐより、足元の仕事を一つずつ整える時期です。周囲との調整を丁寧に進めれば、次の機会は自然に見えてきます。"\n    assert 48 <= len(text) < 80\n    assert gate.validate(text) == text\n\n\ndef test_dense_traditional_chinese_response_uses_language_aware_floor():\n    gate = MasterExperienceQualityGate()\n    text = "現在最重要的不是立刻做出決定，而是先把手上的責任與資源整理清楚。當你把真正想守住的核心確認後，下一步會比現在更明確。"\n    assert 48 <= len(text) < 80\n    assert gate.validate(text) == text\n\n\ndef test_short_dense_response_still_fails():\n    gate = MasterExperienceQualityGate()\n    try:\n        gate.validate("焦らず、今できることを整えてください。")\n    except AIUnavailable as exc:\n        assert exc.code == "quality_too_short"\n    else:\n        raise AssertionError("short dense response must fail")\n\n\ndef test_english_keeps_original_floor():\n    gate = MasterExperienceQualityGate()\n    text = "Take a little more time to organize what matters before making the next move."\n    assert len(text) < 80\n    try:\n        gate.validate(text)\n    except AIUnavailable as exc:\n        assert exc.code == "quality_too_short"\n    else:\n        raise AssertionError("English response below original floor must fail")\n''', encoding='utf-8')
print('language_quality_patch=applied')
