from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
website = root / 'website'

# 1) Tarot engine: one shuffle() + one draw() path for auto/manual.
tarot_path = website / 'divination/tarot.py'
tarot_path.write_text(r'''from __future__ import annotations

import random
from typing import Any

from .core import DivinationError
from .decks import DeckRegistry


SPREADS: dict[str, list[tuple[str, str]]] = {
    "single": [("guidance", "核心指引")],
    "three_card": [("past", "過去／根源"), ("present", "現在／核心"), ("future", "未來／發展")],
    "decision": [("situation", "現況"), ("path_a", "選擇 A 的能量"), ("path_b", "選擇 B 的能量")],
}


def shuffle(cards: list[dict[str, Any]], *, reversal_rate: float, rng: random.Random) -> list[dict[str, Any]]:
    """Create one hidden physical deck state: order + orientation are fixed before selection."""
    ordered = list(cards)
    rng.shuffle(ordered)
    return [
        {
            "card": card,
            "draw_index": idx + 1,  # public/manual API is intentionally 1-based
            "orientation": "reversed" if rng.random() < reversal_rate else "upright",
        }
        for idx, card in enumerate(ordered)
    ]


def draw(
    shuffled: list[dict[str, Any]],
    indices: list[int],
    positions: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    """Select positions from an already shuffled deck. Auto/manual both call this function."""
    if len(indices) != len(positions):
        raise DivinationError(f"draw requires {len(positions)} indices")
    if len(set(indices)) != len(indices):
        raise DivinationError("draw indices must be unique")
    if any(not isinstance(i, int) or isinstance(i, bool) or i < 1 or i > len(shuffled) for i in indices):
        raise DivinationError(f"draw indices must be between 1 and {len(shuffled)}")

    results: list[dict[str, Any]] = []
    for index, (position, position_label) in zip(indices, positions):
        entry = shuffled[index - 1]
        card = entry["card"]
        orientation = entry["orientation"]
        meanings = card.get("meanings") or {}
        selected_meaning = meanings.get(orientation) or meanings.get("upright") or card.get("meaning") or ""
        results.append({
            "card_id": card.get("id"),
            "title": card.get("title") or {},
            "arcana": card.get("arcana"),
            "suit": card.get("suit"),
            "number": card.get("number"),
            "position": position,
            "position_label": position_label,
            "orientation": orientation,
            "draw_index": index,
            "meaning": selected_meaning,
            "upright_meaning": meanings.get("upright"),
            "reversed_meaning": meanings.get("reversed"),
            "ecology": card.get("ecology"),
            "image": card.get("image"),
        })
    return results


class TarotMethod:
    method_id = "tarot"

    def __init__(self, decks: DeckRegistry) -> None:
        self.decks = decks

    @staticmethod
    def _auto_spread(question: str) -> str:
        q = question.lower()
        decision_markers = ("是否", "要不要", "該不該", "哪個", "選擇", "vs", " or ")
        timeline_markers = ("未來", "發展", "接下來", "過去", "現在", "future", "next")
        if any(x in q for x in decision_markers):
            return "decision"
        if any(x in q for x in timeline_markers):
            return "three_card"
        return "single"

    def generate(self, *, input_data: dict[str, Any], question: str, rng: random.Random) -> dict[str, Any]:
        deck = self.decks.get(str(input_data.get("deck_id") or "leopardcat"))
        cards = deck.cards
        spread_id = str(input_data.get("spread") or "single")
        if spread_id == "auto":
            spread_id = self._auto_spread(question)
        if spread_id not in SPREADS:
            raise DivinationError(f"unsupported tarot spread: {spread_id}")

        positions = SPREADS[spread_id]
        if len(cards) < len(positions):
            raise DivinationError(f"deck has {len(cards)} cards but spread requires {len(positions)}")

        requested_rate = float(input_data.get("reversal_rate", 0.5))
        if not 0.0 <= requested_rate <= 1.0:
            raise DivinationError("reversal_rate must be between 0 and 1")
        reversal_rate = requested_rate if deck.reversals else 0.0

        hidden_deck = shuffle(cards, reversal_rate=reversal_rate, rng=rng)
        requested_indices = input_data.get("draw_indices")
        if requested_indices is None:
            # Existing automatic mode: shuffle first, then draw the required number from the top.
            draw_indices = list(range(1, len(positions) + 1))
            draw_mode = "auto"
        else:
            if not isinstance(requested_indices, list):
                raise DivinationError("draw_indices must be a list")
            draw_indices = requested_indices
            draw_mode = "manual"

        results = draw(hidden_deck, draw_indices, positions)

        return {
            "method": "tarot",
            "deck": {
                "deck_id": deck.deck_id,
                "name": deck.name,
                "creator": deck.creator,
                "card_count": len(deck.cards),
                "reversals": deck.reversals,
                "source": deck.source,
                "card_back": deck.card_back,
            },
            "spread": spread_id,
            "cards": results,
            "rules": {
                "without_replacement": True,
                # Kept for backward compatibility: orientation becomes visible at draw/reveal time.
                "orientation_decided_at_draw_time": True,
                "orientation_assigned_at_shuffle_time": True,
                "orientation_hidden_until_reveal": True,
                "shuffle_before_draw": True,
                "draw_indices_are_1_based": True,
                "draw_mode": draw_mode,
                "draw_indices": draw_indices,
                "reversal_rate": reversal_rate,
            },
        }
''', encoding='utf-8')

# 2) Deck contract: every deck has a usable card back; custom manifests may override it.
decks_path = website / 'divination/decks.py'
decks = decks_path.read_text(encoding='utf-8')
decks = decks.replace(
    '    default_theme: str = "minimal-light"\n',
    '    default_theme: str = "minimal-light"\n    card_back: str = "/art/card-back.svg"\n'
)
decks = decks.replace(
    '                "leopardcat",\n            )\n',
    '                "leopardcat",\n                "/art/card-back.svg",\n            )\n',
    1,
)
decks = decks.replace(
    '            default_theme=default_theme,\n        )\n',
    '            default_theme=default_theme,\n            card_back=str(data.get("card_back") or "/art/card-back.svg"),\n        )\n',
    1,
)
decks = decks.replace(
    '            "default_theme": d.default_theme,\n',
    '            "default_theme": d.default_theme,\n            "card_back": d.card_back,\n',
    1,
)
if decks.count('card_back') < 4:
    raise SystemExit('deck card_back patch incomplete')
decks_path.write_text(decks, encoding='utf-8')

# 3) Add four-way symmetric default card back asset.
art_dir = website / 'public/art'
art_dir.mkdir(parents=True, exist_ok=True)
(art_dir / 'card-back.svg').write_text(r'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 1000" role="img" aria-label="Symmetric tarot card back">
  <defs>
    <radialGradient id="bg" cx="50%" cy="50%" r="70%">
      <stop offset="0" stop-color="#173226"/>
      <stop offset="0.55" stop-color="#08150f"/>
      <stop offset="1" stop-color="#020604"/>
    </radialGradient>
    <linearGradient id="gold" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#f0d98a"/>
      <stop offset="0.45" stop-color="#a77b23"/>
      <stop offset="1" stop-color="#e6c76d"/>
    </linearGradient>
    <g id="corner">
      <path d="M70 70h115c-40 18-69 47-88 88V70" fill="none" stroke="url(#gold)" stroke-width="5"/>
      <path d="M94 94c20 10 37 27 47 47-20-10-37-27-47-47Z" fill="#caa64a" opacity=".72"/>
      <circle cx="118" cy="118" r="7" fill="#f0d98a"/>
    </g>
    <g id="quarterMotif">
      <path d="M300 500C255 455 226 405 214 344c42 26 73 63 92 108" fill="none" stroke="url(#gold)" stroke-width="8" stroke-linecap="round"/>
      <path d="M300 500C247 481 204 448 174 402c51 5 95 25 132 59" fill="none" stroke="#80611f" stroke-width="4"/>
      <circle cx="244" cy="416" r="16" fill="none" stroke="#d7b85b" stroke-width="5"/>
      <circle cx="206" cy="374" r="8" fill="#d7b85b" opacity=".8"/>
    </g>
  </defs>
  <rect width="600" height="1000" rx="36" fill="url(#bg)"/>
  <rect x="26" y="26" width="548" height="948" rx="28" fill="none" stroke="url(#gold)" stroke-width="8"/>
  <rect x="45" y="45" width="510" height="910" rx="22" fill="none" stroke="#7e6427" stroke-width="2"/>

  <!-- Four corners are mirrored horizontally and vertically. -->
  <use href="#corner"/>
  <use href="#corner" transform="translate(600 0) scale(-1 1)"/>
  <use href="#corner" transform="translate(0 1000) scale(1 -1)"/>
  <use href="#corner" transform="translate(600 1000) scale(-1 -1)"/>

  <!-- Central forest/leopard rosette: exact four-way symmetry. -->
  <use href="#quarterMotif"/>
  <use href="#quarterMotif" transform="translate(600 0) scale(-1 1)"/>
  <use href="#quarterMotif" transform="translate(0 1000) scale(1 -1)"/>
  <use href="#quarterMotif" transform="translate(600 1000) scale(-1 -1)"/>
  <circle cx="300" cy="500" r="88" fill="#07110c" stroke="url(#gold)" stroke-width="8"/>
  <circle cx="300" cy="500" r="62" fill="none" stroke="#7f6223" stroke-width="3"/>
  <path d="M300 440l20 40 40 20-40 20-20 40-20-40-40-20 40-20Z" fill="none" stroke="#e1c268" stroke-width="7"/>
  <circle cx="300" cy="500" r="14" fill="#e1c268"/>
  <circle cx="300" cy="455" r="6" fill="#c89e3b"/><circle cx="300" cy="545" r="6" fill="#c89e3b"/>
  <circle cx="255" cy="500" r="6" fill="#c89e3b"/><circle cx="345" cy="500" r="6" fill="#c89e3b"/>
</svg>
''', encoding='utf-8')

# 4) Ritual UI: auto/manual are controllers over same draw engine; manual stage shows card backs.
index_path = website / 'index.html'
index = index_path.read_text(encoding='utf-8')
old = '''                        <div id="legacy-spread-picker" class="legacy-spread-picker" role="radiogroup" aria-label="Spread">\n                            <span class="legacy-spread-label" data-i18n="common.spread_label">牌陣</span>\n                            <button type="button" class="legacy-spread-btn active" data-spread-choice="single" data-i18n="common.spread_single_short">單牌</button>\n                            <button type="button" class="legacy-spread-btn" data-spread-choice="three_card" data-i18n="common.spread_three_short">三牌</button>\n                        </div>\n                        <button class="btn btn-gold" data-i18n="common.btn_draw" onclick="drawFortune()">祈請大師開牌</button>\n'''
new = '''                        <div id="legacy-spread-picker" class="legacy-spread-picker" role="radiogroup" aria-label="Spread">\n                            <span class="legacy-spread-label" data-i18n="common.spread_label">牌陣</span>\n                            <button type="button" class="legacy-spread-btn active" data-spread-choice="single" data-i18n="common.spread_single_short">單牌</button>\n                            <button type="button" class="legacy-spread-btn" data-spread-choice="three_card" data-i18n="common.spread_three_short">三牌</button>\n                        </div>\n                        <div id="draw-mode-picker" class="legacy-spread-picker draw-mode-picker" role="radiogroup" aria-label="Draw mode">\n                            <span class="legacy-spread-label" data-i18n="common.draw_mode_label">抽牌方式</span>\n                            <button type="button" class="legacy-spread-btn active" data-draw-mode="auto" data-i18n="common.draw_mode_auto">自動</button>\n                            <button type="button" class="legacy-spread-btn" data-draw-mode="manual" data-i18n="common.draw_mode_manual">手動</button>\n                        </div>\n                        <div id="manual-draw-stage" class="manual-draw-stage hidden">\n                            <div class="manual-draw-toolbar">\n                                <button type="button" id="btn-manual-shuffle" class="btn btn-gold-outline btn-small" onclick="shuffleManualDeck()" data-i18n="common.shuffle_cards">洗牌</button>\n                                <span id="manual-draw-status" class="manual-draw-status" aria-live="polite"></span>\n                            </div>\n                            <div id="manual-card-pool" class="manual-card-pool" aria-label="Card backs"></div>\n                        </div>\n                        <button id="btn-primary-draw" class="btn btn-gold" data-i18n="common.btn_draw" onclick="drawFortune()">祈請大師開牌</button>\n'''
if old not in index:
    raise SystemExit('index spread picker anchor missing')
index_path.write_text(index.replace(old, new, 1), encoding='utf-8')

# 5) Front-end state/controller.
main_path = website / 'main.js'
main = main_path.read_text(encoding='utf-8')
state_anchor = "window.currentShareReceipt = null; // read-only receipt identity; never grants follow-up authority\n"
state_block = state_anchor + r'''window.drawMode = 'auto';
window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };

function requiredDrawCount() {
    return window.activeSpread === 'single' ? 1 : 3;
}

function freshShuffleSeed() {
    const bytes = new Uint32Array(4);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, n => n.toString(16).padStart(8, '0')).join('');
}

function activeCardBack() {
    return window.activeDeckInfo?.card_back || '/art/card-back.svg';
}

function manualStatus() {
    const el = document.getElementById('manual-draw-status');
    if (!el) return;
    if (!window.manualDrawState.shuffled) {
        el.textContent = uiText('manual_draw_shuffle_first', 'Shuffle first, then choose your cards.');
        return;
    }
    const need = requiredDrawCount();
    const selected = window.manualDrawState.selected.length;
    el.textContent = uiText('manual_draw_progress', 'Selected {selected} / {need}', {selected, need});
}

function renderManualCardPool() {
    const pool = document.getElementById('manual-card-pool');
    if (!pool) return;
    pool.innerHTML = '';
    const total = Array.isArray(window.cardData) ? window.cardData.length : 0;
    const back = activeCardBack();
    for (let i = 1; i <= total; i++) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'manual-card-back';
        button.dataset.drawIndex = String(i);
        button.setAttribute('aria-label', uiText('manual_card_aria', 'Choose card position {index}', {index:i}));
        const img = document.createElement('img');
        img.src = back;
        img.alt = '';
        img.draggable = false;
        button.appendChild(img);
        if (window.manualDrawState.selected.includes(i)) button.classList.add('selected');
        button.addEventListener('click', () => selectManualCard(i, button));
        pool.appendChild(button);
    }
    manualStatus();
}

window.setDrawMode = function(mode) {
    window.drawMode = mode === 'manual' ? 'manual' : 'auto';
    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.classList.toggle('active', btn.dataset.drawMode === window.drawMode));
    const stage = document.getElementById('manual-draw-stage');
    const primary = document.getElementById('btn-primary-draw');
    stage?.classList.toggle('hidden', window.drawMode !== 'manual');
    primary?.classList.toggle('hidden', window.drawMode === 'manual');
    if (window.drawMode === 'manual') {
        window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };
        const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';
        manualStatus();
    }
};

window.shuffleManualDeck = function() {
    const q = document.getElementById('fortune-question')?.value?.trim() || '';
    if (!q) return alert(uiText('err_empty_question', 'Please enter your question first.'));
    window.manualDrawState = { seed: freshShuffleSeed(), selected: [], shuffled: true, submitting: false };
    renderManualCardPool();
    const pool = document.getElementById('manual-card-pool');
    pool?.classList.remove('is-shuffling');
    void pool?.offsetWidth;
    pool?.classList.add('is-shuffling');
    setTimeout(() => pool?.classList.remove('is-shuffling'), 650);
};

async function selectManualCard(index, button) {
    const state = window.manualDrawState;
    if (!state.shuffled || state.submitting || state.selected.includes(index)) return;
    const need = requiredDrawCount();
    if (state.selected.length >= need) return;
    state.selected.push(index);
    button.classList.add('selected');
    button.disabled = true;
    manualStatus();
    if (state.selected.length === need) {
        state.submitting = true;
        const q = document.getElementById('fortune-question')?.value?.trim() || '';
        await new Promise(resolve => setTimeout(resolve, 320));
        await performReading(q, state.selected.slice(), state.seed);
    }
}

function bindDrawModePicker() {
    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.addEventListener('click', () => window.setDrawMode(btn.dataset.drawMode)));
    window.setDrawMode(window.drawMode);
}
'''
if state_anchor not in main:
    raise SystemExit('main draw state anchor missing')
main = main.replace(state_anchor, state_block, 1)

# Spread changes invalidate a manual shuffle because required slot count changed.
old_picker = '''    const select = spread => {\n        window.activeSpread = spread || 'single';\n        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));\n    };\n'''
new_picker = '''    const select = spread => {\n        window.activeSpread = spread || 'single';\n        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));\n        if (window.drawMode === 'manual') {\n            window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };\n            const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';\n            manualStatus();\n        }\n    };\n'''
if old_picker not in main:
    raise SystemExit('spread picker anchor missing')
main = main.replace(old_picker, new_picker, 1)
main = main.replace(
    "document.addEventListener('DOMContentLoaded', bindLegacySpreadPicker);\ndocument.addEventListener('DOMContentLoaded', initAllSystems);\n",
    "document.addEventListener('DOMContentLoaded', bindLegacySpreadPicker);\ndocument.addEventListener('DOMContentLoaded', bindDrawModePicker);\ndocument.addEventListener('DOMContentLoaded', initAllSystems);\n",
    1,
)

# Replace automatic-only drawFortune with shared performReading controller.
old_draw = r'''window.drawFortune = async function() {
    const common = window.siteData[window.currentLang].common;
    const q = document.getElementById('fortune-question').value;
    if (!q.trim()) return alert(common.err_empty_question);
    const debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
    if (!debug && !chargeLocalMana()) return alert(common.err_mana_depleted);

    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    try {
        await window.getModularReading(q);
    } catch (e) {
        console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
        if (!debug) refundLocalMana();
        showModularRetry(q, e);
    }
};
'''
new_draw = r'''async function performReading(q, drawIndices = null, seed = null) {
    const common = window.siteData[window.currentLang].common;
    if (!q.trim()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_empty_question);
    }
    const debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
    if (!debug && !chargeLocalMana()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_mana_depleted);
    }

    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    try {
        await window.getModularReading(q, {drawIndices, seed});
    } catch (e) {
        console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
        if (!debug) refundLocalMana();
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        showModularRetry(q, e);
    }
}

window.drawFortune = async function() {
    if (window.drawMode === 'manual') return window.shuffleManualDeck();
    const q = document.getElementById('fortune-question').value;
    return performReading(q);
};
'''
if old_draw not in main:
    raise SystemExit('drawFortune anchor missing')
main = main.replace(old_draw, new_draw, 1)

# getModularReading accepts optional deterministic manual selection.
main = main.replace(
    'window.getModularReading = async function(q) {\n',
    'window.getModularReading = async function(q, drawOptions = {}) {\n',
    1,
)
old_request = '''        } : {\n            method: 'tarot', persona: window.activePersonaId || undefined, question: q,\n            input: { spread: window.activeSpread || 'single', deck_id: window.activeDeckId },\n            lang: getAILanguageTag()\n        };\n'''
new_request = '''        } : {\n            method: 'tarot', persona: window.activePersonaId || undefined, question: q,\n            input: {\n                spread: window.activeSpread || 'single',\n                deck_id: window.activeDeckId,\n                ...(Array.isArray(drawOptions.drawIndices) ? {draw_indices: drawOptions.drawIndices} : {})\n            },\n            ...(drawOptions.seed ? {seed: drawOptions.seed} : {}),\n            lang: getAILanguageTag()\n        };\n'''
if old_request not in main:
    raise SystemExit('modular request anchor missing')
main = main.replace(old_request, new_request, 1)

# Persist draw metadata in reading state/receipt for audit and reload.
old_state = '''        spread: data.method_result?.spread || 'single',\n        cards: resolved.map(({spec, card}) => ({ card_id: spec.card_id || card.id, orientation: spec.orientation || 'upright', position: spec.position, position_label: spec.position_label }))\n    };\n'''
new_state = '''        spread: data.method_result?.spread || 'single',\n        draw_mode: data.method_result?.rules?.draw_mode || 'auto',\n        draw_indices: data.method_result?.rules?.draw_indices || [],\n        cards: resolved.map(({spec, card}) => ({ card_id: spec.card_id || card.id, orientation: spec.orientation || 'upright', draw_index: spec.draw_index, position: spec.position, position_label: spec.position_label }))\n    };\n'''
if old_state not in main:
    raise SystemExit('reading state anchor missing')
main = main.replace(old_state, new_state, 1)

# Custom deck load owns its back asset too.
main = main.replace(
    '        window.activeDeckInfo = deck;\n',
    '        window.activeDeckInfo = deck;\n        if (window.drawMode === \'manual\' && window.manualDrawState.shuffled) renderManualCardPool();\n',
    1,
)

# Reset manual controller without changing default auto behavior.
main = main.replace(
    '    window.currentReadingState = null;\n    lastShareFile = null;\n',
    '    window.currentReadingState = null;\n    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };\n    lastShareFile = null;\n',
    1,
)
main_path.write_text(main, encoding='utf-8')

# 6) CSS: lightweight shuffle animation + mobile-safe card-back grid.
css_path = website / 'style.css'
css = css_path.read_text(encoding='utf-8')
css += r'''

/* Shared Draw Engine UI: shuffle is presentation; selection indices feed the same server draw(). */
.draw-mode-picker { margin-top: 8px; }
.manual-draw-stage { margin: 14px 0 4px; }
.manual-draw-toolbar { display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom:12px; flex-wrap:wrap; }
.manual-draw-status { font-size:.76rem; opacity:.82; min-height:1.2em; }
.manual-card-pool {
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(38px,1fr));
  gap:5px;
  max-height:330px;
  overflow:auto;
  padding:10px;
  border:1px solid rgba(212,175,55,.22);
  border-radius:18px;
  background:rgba(0,0,0,.22);
  overscroll-behavior:contain;
}
.manual-card-back {
  appearance:none;
  border:0;
  padding:0;
  background:transparent;
  border-radius:6px;
  cursor:pointer;
  transform:translateY(0) scale(1);
  transition:transform .18s ease, filter .18s ease, opacity .18s ease;
  aspect-ratio:3 / 5;
  min-width:0;
}
.manual-card-back img { width:100%; height:100%; display:block; object-fit:cover; border-radius:6px; box-shadow:0 4px 10px rgba(0,0,0,.45); user-select:none; pointer-events:none; }
.manual-card-back:hover, .manual-card-back:focus-visible { transform:translateY(-7px) scale(1.05); outline:2px solid var(--color-gold); outline-offset:2px; }
.manual-card-back.selected { transform:translateY(-12px) scale(1.06); filter:drop-shadow(0 0 7px rgba(212,175,55,.75)); }
.manual-card-back.selected img { outline:2px solid var(--color-gold); outline-offset:1px; }
.manual-card-pool.is-shuffling .manual-card-back { animation:ritual-shuffle .6s cubic-bezier(.2,.8,.25,1); }
.manual-card-pool.is-shuffling .manual-card-back:nth-child(3n) { animation-delay:.04s; }
.manual-card-pool.is-shuffling .manual-card-back:nth-child(4n) { animation-delay:.08s; }
.manual-card-pool.is-shuffling .manual-card-back:nth-child(5n) { animation-delay:.12s; }
@keyframes ritual-shuffle {
  0% { transform:translate3d(0,0,0) rotate(0deg); }
  35% { transform:translate3d(12px,-10px,0) rotate(5deg); }
  68% { transform:translate3d(-10px,6px,0) rotate(-4deg); }
  100% { transform:translate3d(0,0,0) rotate(0deg); }
}
@media (max-width: 520px) {
  .manual-card-pool { grid-template-columns:repeat(9,minmax(0,1fr)); gap:4px; max-height:300px; padding:7px; }
  .manual-card-back { border-radius:4px; }
  .manual-card-back img { border-radius:4px; }
}
@media (prefers-reduced-motion: reduce) {
  .manual-card-pool.is-shuffling .manual-card-back { animation:none; }
  .manual-card-back { transition:none; }
}
'''
css_path.write_text(css, encoding='utf-8')

# 7) Five-locale catalog entries.
locale_path = website / 'public/locales_v10.json'
locales = json.loads(locale_path.read_text(encoding='utf-8'))
copy = {
    'zh': {
        'draw_mode_label':'抽牌方式','draw_mode_auto':'自動','draw_mode_manual':'手動','shuffle_cards':'洗牌',
        'manual_draw_shuffle_first':'先洗牌，再憑直覺選牌。','manual_draw_progress':'已選 {selected} / {need} 張','manual_card_aria':'選擇第 {index} 個位置'
    },
    'en': {
        'draw_mode_label':'Draw mode','draw_mode_auto':'Auto','draw_mode_manual':'Manual','shuffle_cards':'Shuffle',
        'manual_draw_shuffle_first':'Shuffle first, then choose by intuition.','manual_draw_progress':'Selected {selected} / {need}','manual_card_aria':'Choose card position {index}'
    },
    'ja': {
        'draw_mode_label':'引き方','draw_mode_auto':'自動','draw_mode_manual':'手動','shuffle_cards':'シャッフル',
        'manual_draw_shuffle_first':'まずシャッフルして、直感でカードを選んでください。','manual_draw_progress':'選択 {selected} / {need} 枚','manual_card_aria':'{index} 番のカードを選ぶ'
    },
    'ko': {
        'draw_mode_label':'카드 뽑기','draw_mode_auto':'자동','draw_mode_manual':'수동','shuffle_cards':'셔플',
        'manual_draw_shuffle_first':'먼저 셔플한 뒤 직감으로 카드를 고르세요.','manual_draw_progress':'선택 {selected} / {need}장','manual_card_aria':'{index}번 위치 카드 선택'
    },
    'es': {
        'draw_mode_label':'Modo de extracción','draw_mode_auto':'Automático','draw_mode_manual':'Manual','shuffle_cards':'Barajar',
        'manual_draw_shuffle_first':'Baraja primero y luego elige por intuición.','manual_draw_progress':'Elegidas {selected} / {need}','manual_card_aria':'Elegir la posición {index}'
    },
}
for lang, values in copy.items():
    if lang not in locales or not isinstance(locales[lang], dict):
        raise SystemExit(f'missing locale {lang}')
    locales[lang].setdefault('common', {}).update(values)
locale_path.write_text(json.dumps(locales, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# 8) Protected capability: manual/auto are controller choices over identical primitives.
cap_path = root / 'governance/capabilities.json'
caps = json.loads(cap_path.read_text(encoding='utf-8'))
caps['protected_capabilities']['reading.shuffle-draw-engine'] = {
    'status':'protected',
    'owner':'divination',
    'contract':[
        'Tarot automatic and manual selection MUST share the same shuffle() and draw() engine primitives; draw mode is a controller/UI concern, not a second reading algorithm.',
        'shuffle() fixes the hidden card order and each card orientation before selection; card backs MUST not reveal orientation before reveal.',
        'Manual draw indices are unique, 1-based positions in the current shuffled deck and MUST be preserved in the immutable reading result/receipt.',
        'Existing automatic drawing remains available and uses the same shuffled deck contract without requiring manual UI.',
        'Every deck MUST expose a usable card-back asset; missing custom card backs fall back to the system four-way-symmetric card back.',
        'Single-card and three-card spreads MUST both work in automatic and manual controllers without changing share/reload semantics.'
    ],
    'evidence':[
        'website/divination/tarot.py','website/divination/decks.py','website/main.js','website/index.html','website/public/art/card-back.svg','website/tests/test_shuffle_manual_draw.py'
    ]
}
cap_path.write_text(json.dumps(caps, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# 9) Regression tests.
test_path = website / 'tests/test_shuffle_manual_draw.py'
test_path.write_text(r'''import json
import random
from pathlib import Path

import pytest

from divination.core import DivinationError
from divination.tarot import draw, shuffle, TarotMethod


class Deck:
    deck_id='test-deck'; name='Test'; creator=''; reversals=True; source='test'; card_back='/art/card-back.svg'
    cards=[{'id':f'c{i}','title':{'en':f'C{i}'},'meanings':{'upright':f'u{i}','reversed':f'r{i}'}} for i in range(1,79)]
class Registry:
    def get(self, _): return Deck()


def test_shuffle_fixes_order_and_orientation_before_selection():
    a=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(42))
    b=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(42))
    assert [(x['card']['id'],x['orientation']) for x in a] == [(x['card']['id'],x['orientation']) for x in b]
    assert len({x['card']['id'] for x in a}) == 78


def test_draw_uses_one_based_manual_indices_and_preserves_order():
    hidden=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(8))
    result=draw(hidden,[3,76,55],[('past','Past'),('present','Present'),('future','Future')])
    assert [x['draw_index'] for x in result] == [3,76,55]
    assert [x['card_id'] for x in result] == [hidden[2]['card']['id'],hidden[75]['card']['id'],hidden[54]['card']['id']]
    assert [x['orientation'] for x in result] == [hidden[2]['orientation'],hidden[75]['orientation'],hidden[54]['orientation']]


def test_draw_rejects_duplicate_or_out_of_range_indices():
    hidden=shuffle(Deck.cards, reversal_rate=.5, rng=random.Random(1))
    with pytest.raises(DivinationError): draw(hidden,[1,1,2],[('a','a'),('b','b'),('c','c')])
    with pytest.raises(DivinationError): draw(hidden,[0],[('a','a')])
    with pytest.raises(DivinationError): draw(hidden,[79],[('a','a')])


def test_auto_and_manual_share_same_engine_result_when_indices_match():
    method=TarotMethod(Registry())
    auto=method.generate(input_data={'deck_id':'test-deck','spread':'three_card'},question='x',rng=random.Random(99))
    manual=method.generate(input_data={'deck_id':'test-deck','spread':'three_card','draw_indices':[1,2,3]},question='x',rng=random.Random(99))
    assert auto['cards'] == manual['cards']
    assert auto['rules']['draw_mode']=='auto'
    assert manual['rules']['draw_mode']=='manual'
    assert auto['rules']['orientation_assigned_at_shuffle_time'] is True


def test_manual_three_card_arbitrary_indices_are_deterministic():
    method=TarotMethod(Registry())
    x=method.generate(input_data={'spread':'three_card','draw_indices':[3,76,55]},question='x',rng=random.Random(123))
    y=method.generate(input_data={'spread':'three_card','draw_indices':[3,76,55]},question='x',rng=random.Random(123))
    assert x['cards']==y['cards']
    assert x['rules']['draw_indices']==[3,76,55]


def test_card_back_is_four_way_symmetric_by_construction_and_has_no_text():
    svg=Path('public/art/card-back.svg').read_text(encoding='utf-8')
    assert 'scale(-1 1)' in svg and 'scale(1 -1)' in svg and 'scale(-1 -1)' in svg
    assert '<text' not in svg.lower()


def test_ui_has_auto_manual_shuffle_and_shared_draw_payload():
    html=Path('index.html').read_text(encoding='utf-8')
    js=Path('main.js').read_text(encoding='utf-8')
    assert 'data-draw-mode="auto"' in html and 'data-draw-mode="manual"' in html
    assert 'id="manual-card-pool"' in html and 'shuffleManualDeck()' in html
    assert 'performReading(q, state.selected.slice(), state.seed)' in js
    assert 'draw_indices: drawOptions.drawIndices' in js
    assert '...(drawOptions.seed ? {seed: drawOptions.seed} : {})' in js


def test_all_locales_have_draw_mode_copy():
    data=json.loads(Path('public/locales_v10.json').read_text(encoding='utf-8'))
    for lang in ('zh','en','ja','ko','es'):
        c=data[lang]['common']
        for key in ('draw_mode_label','draw_mode_auto','draw_mode_manual','shuffle_cards','manual_draw_shuffle_first','manual_draw_progress','manual_card_aria'):
            assert c.get(key)


def test_governance_protects_shared_shuffle_draw_engine():
    caps=json.loads(Path('../governance/capabilities.json').read_text(encoding='utf-8'))
    c=caps['protected_capabilities']['reading.shuffle-draw-engine']
    assert c['status']=='protected'
    assert any('same shuffle() and draw()' in x for x in c['contract'])
''', encoding='utf-8')

print('shuffle/manual draw patch applied')
