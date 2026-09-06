import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_homepage_preserves_explicit_spread_selection_and_no_prod_vconsole():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    assert 'vconsole' not in html.lower()
    assert 'id="spread-select"' in html
    assert '<option value="auto" selected>自動</option>' in html
    assert '<option value="single"' in html
    assert '<option value="three_card"' in html
    assert "window.activeSpread = 'auto'" in js
    assert 'resolvedSpreadForQuestion(q)' in js
    assert "spread: resolvedSpreadForQuestion(q)" in js

def test_dynamic_errors_and_nav_are_locale_driven():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    data=json.loads((ROOT/'public/locales_v10.json').read_text(encoding='utf-8'))
    assert 'data-i18n="nav.create_deck"' in html
    assert "uiText('provider_429_error'" in js
    assert 'Dynamic runtime states must change language too' in js
    required={'provider_429_error','privacy_note','social_share','copy_link','spread_label','spread_single_short','spread_three_short'}
    for lang in ('zh','en','ja','ko','es'):
        assert data[lang]['nav']['create_deck']
        assert required.issubset(data[lang]['common'])

def test_public_controls_share_one_rounded_geometry_contract():
    css=(ROOT/'style.css').read_text(encoding='utf-8')
    read_css=(ROOT/'public/read.css').read_text(encoding='utf-8')
    assert '--control-radius: 18px' in css
    assert 'Public control geometry contract' in css
    assert 'Public control geometry contract' in read_css
    for file in ('create.html','manage.html'):
        assert 'Public control geometry contract' in (ROOT/'public'/file).read_text(encoding='utf-8')

def test_primary_read_page_still_exposes_single_and_three_card_spreads():
    js=(ROOT/'public/read.js').read_text(encoding='utf-8')
    assert "{id:'single'" in js
    assert "{id:'three_card'" in js


def test_dynamic_persona_and_theme_labels_retranslate():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    assert 'persona-switcher-label' in js
    assert 'theme-switcher-label' in js
    assert "el.textContent = uiText('persona_label'" in js
    assert "el.textContent = uiText('theme_label'" in js
