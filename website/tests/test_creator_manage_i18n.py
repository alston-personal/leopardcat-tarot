import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_creator_and_manage_use_shared_five_locale_state():
    creator=(ROOT/'public/creator.js').read_text(encoding='utf-8')
    manage=(ROOT/'public/manage.js').read_text(encoding='utf-8')
    for js in (creator,manage):
        assert "localStorage.getItem('leopard-lang')" in js
        assert "fetch('/locales_v10.json'" in js
    assert 'id="creator-language"' in (ROOT/'public/create.html').read_text(encoding='utf-8')
    assert 'id="manage-language"' in (ROOT/'public/manage.html').read_text(encoding='utf-8')

def test_creator_manage_locale_catalog_has_exact_key_parity():
    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))
    for section in ('creator','manage'):
        keys=set(data['en'][section]); assert keys
        for lang in ('zh','en','ja','ko','es'):
            assert set(data[lang][section])==keys

def test_creator_runtime_localizes_previous_hardcoded_states():
    js=(ROOT/'public/creator.js').read_text(encoding='utf-8')
    for token in ("ct('slug_checking'","ct('persona_creating'","ct('cards_added'","ct('preparing_images'","ct('publishing'","ct('complete_count'","apiMessage(data"):
        assert token in js
    assert "toLocaleString('zh-TW')" not in js
    assert "localeCompare(b.name, 'zh-Hant'" not in js

def test_manage_runtime_localizes_sensitive_error_and_confirmation_states():
    js=(ROOT/'public/manage.js').read_text(encoding='utf-8')
    for token in ("mt('saving'","mt('rotate_confirm'","mt('delete_confirm'","mt('delete_prompt'","apiMessage(d"):
        assert token in js
