import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_read_page_uses_same_five_locale_catalog_and_selector():
    html=(ROOT/'public/read.html').read_text(encoding='utf-8')
    js=(ROOT/'public/read.js').read_text(encoding='utf-8')
    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))
    assert 'id="read-language"' in html
    assert "localStorage.getItem('leopard-lang')" in js
    assert "fetch('/locales_v10.json'" in js
    keys=set(data['en']['read'])
    assert keys
    for lang in ('zh','en','ja','ko','es'):
        assert set(data[lang]['read'])==keys

def test_read_page_ai_language_follows_selected_locale():
    js=(ROOT/'public/read.js').read_text(encoding='utf-8')
    assert "lang:aiLang()" in js
    assert "lang:'zh-TW'" not in js
    for token in ("zh:'zh-TW'","ja:'ja'","ko:'ko'","es:'es'"):
        assert token in js

def test_read_page_runtime_labels_are_locale_driven():
    js=(ROOT/'public/read.js').read_text(encoding='utf-8')
    for token in ("rt('upright'","rt('reversed'","rt('question_required'","rt('drawing'","rt('master_unavailable'","rt('cards_count'"):
        assert token in js
    assert '張牌</span>' not in js
