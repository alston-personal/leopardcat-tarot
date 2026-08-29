import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_public_ui_has_five_locales_with_matching_shape():
    data = json.loads((ROOT / 'public' / 'locales_v10.json').read_text(encoding='utf-8'))
    assert set(['zh','en','ja','ko','es']).issubset(data)
    reference = data['en']
    for lang in ('ja','ko','es'):
        assert set(data[lang]) == set(reference)
        assert set(data[lang]['common']) == set(reference['common'])
        assert set(data[lang]['nav']) == set(reference['nav'])
        assert set(data[lang]['hero']) == set(reference['hero'])
        assert set(data[lang]['labels']) == set(reference['labels'])
        assert [g['id'] for g in data[lang]['groups']] == [g['id'] for g in reference['groups']]


def test_runtime_exposes_switcher_and_ai_language_tags():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    for token in ("ja: { label: '日本語'", "ko: { label: '한국어'", "es: { label: 'ES'"):
        assert token in js
    assert 'function getAILanguageTag' in js
    assert "ja: 'ja'" in js and "ko: 'ko'" in js and "es: 'es'" in js
    assert "window.currentLang === 'zh' ? 'zh-TW' : 'en'" not in js
