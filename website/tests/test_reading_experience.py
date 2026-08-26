from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_focused_reading_keeps_brand_theme_and_followup_contract():
    html = (ROOT / 'public' / 'read.html').read_text(encoding='utf-8')
    js = (ROOT / 'public' / 'read.js').read_text(encoding='utf-8')
    css = (ROOT / 'public' / 'read.css').read_text(encoding='utf-8')

    assert 'id="brand-link"' in html
    assert 'id="back-to-deck"' in html
    assert 'id="followup"' in html
    assert 'id="followup-input"' in html
    assert '繼續詢問大師' in html
    assert '備援／進階：交給你自己的 AI' in html

    assert '/api/v1/brands/' in js
    assert '/api/v1/themes/' in js
    assert "state.deck==='leopardcat'?'leopardcat':'minimal-light'" in js
    assert 'readingId:state.envelope.reading_id' in js
    assert 'sessionToken:state.envelope.session_token' in js
    assert "'/api/v1/readings'" in js
    assert 'hidden-quote' in js
    assert 'cleanReading' in js
    assert "root.style.setProperty('--bg'" in js

    assert '--bg:' in css
    assert 'var(--paper)' in css
    assert '.followup-bubble.assistant' in css


def test_primary_tarot_entry_stays_on_active_deck_page():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert "el.setAttribute('href', '#fortune')" in js
    assert 'must not feel like leaving the deck' in js


def test_leopardcat_persona_preserves_familiar_master_voice():
    pack = json.loads((ROOT / 'oracle_packs' / 'leopardcat' / 'pack.json').read_text(encoding='utf-8'))
    voice = '\n'.join(pack['voice'])
    principles = '\n'.join(pack['interpretation_principles'])
    role = pack['identity']['role']

    assert 'Mystical, elegant, Zen-like' in voice
    assert 'present guide rather than an analyst' in voice
    assert 'familiar LeopardCat Tarot experience' in principles
    assert 'never turn the answer into an ecology essay' in role
    assert 'hidden-quote' in pack['closing_instruction']
