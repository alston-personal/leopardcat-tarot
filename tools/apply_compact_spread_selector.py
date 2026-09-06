from pathlib import Path

html_path = Path('website/index.html')
main_path = Path('website/main.js')
css_path = Path('website/style.css')

html = html_path.read_text()
start = html.index('<div id="reading-config-card"')
end = html.index('<button id="btn-primary-draw"', start)
compact = '''<div id="reading-config-card" class="reading-config-card reading-config-compact" aria-label="Reading setup">
                            <div id="legacy-spread-picker" class="compact-spread-picker">
                                <label for="spread-select" class="compact-spread-label" data-i18n="common.spread_label">牌陣</label>
                                <select id="spread-select" class="compact-spread-select" aria-label="Spread">
                                    <option value="auto" selected>自動</option>
                                    <option value="single" data-i18n="common.spread_single_short">單牌</option>
                                    <option value="three_card" data-i18n="common.spread_three_short">三牌</option>
                                </select>
                                <span class="compact-spread-hint">依問題自動選擇適合的牌陣</span>
                            </div>
                            <details id="draw-mode-details" class="draw-mode-details">
                                <summary><span data-i18n="common.draw_mode_label">抽牌方式</span><span id="draw-mode-summary">自動</span></summary>
                                <div id="draw-mode-picker" class="draw-mode-picker compact-draw-mode" role="radiogroup" aria-label="Draw mode">
                                    <button type="button" class="legacy-spread-btn active" data-draw-mode="auto" data-i18n="common.draw_mode_auto">自動</button>
                                    <button type="button" class="legacy-spread-btn" data-draw-mode="manual" data-i18n="common.draw_mode_manual">手動</button>
                                </div>
                                <div id="manual-draw-stage" class="manual-draw-stage hidden">
                                    <div class="manual-draw-toolbar">
                                        <button type="button" id="btn-manual-shuffle" class="btn btn-gold-outline btn-small" onclick="shuffleManualDeck()" data-i18n="common.shuffle_cards">洗牌</button>
                                        <span id="manual-draw-status" class="manual-draw-status" aria-live="polite"></span>
                                    </div>
                                    <div id="manual-card-pool" class="manual-card-pool" aria-label="Card backs"></div>
                                </div>
                            </details>
                        </div>
                        '''
html = html[:start] + compact + html[end:]
html_path.write_text(html)

main = main_path.read_text()
main = main.replace("window.activeSpread = 'single'; // homepage spread selector; preserved across retries", "window.activeSpread = 'auto'; // requested spread mode; auto resolves from the question\nwindow.effectiveSpread = null; // concrete spread selected for the current reading")
main = main.replace("function requiredDrawCount() {\n    return window.activeSpread === 'single' ? 1 : 3;\n}", "function automaticSpreadForQuestion(question) {\n    const q = String(question || '').trim();\n    if (!q) return 'three_card';\n    const simple = /^(?:今天|現在|目前|是否|能不能|可不可以|適不適合|會不會|要不要|should\\s+i|is\\s+it|will\\s+i|can\\s+i)/i.test(q);\n    const complex = /(?:關係|比較|選擇|原因|阻礙|建議|發展|未來|過去|工作|感情|對方|兩個|方案|影響|走向)/.test(q);\n    return simple && !complex && q.length <= 36 ? 'single' : 'three_card';\n}\n\nfunction resolvedSpreadForQuestion(question) {\n    const resolved = window.activeSpread === 'auto' ? automaticSpreadForQuestion(question) : (window.activeSpread || 'single');\n    window.effectiveSpread = resolved;\n    return resolved;\n}\n\nfunction requiredDrawCount() {\n    const spread = window.effectiveSpread || (window.activeSpread === 'auto' ? 'three_card' : window.activeSpread);\n    return spread === 'single' ? 1 : 3;\n}")
main = main.replace("window.shuffleManualDeck = function() {\n    const q = document.getElementById('fortune-question')?.value?.trim() || '';\n    if (!q) return alert", "window.shuffleManualDeck = function() {\n    const q = document.getElementById('fortune-question')?.value?.trim() || '';\n    if (!q) return alert")
main = main.replace("    const seed = freshShuffleSeed();\n    window.manualDrawState", "    resolvedSpreadForQuestion(q);\n    const seed = freshShuffleSeed();\n    window.manualDrawState", 1)
main = main.replace("spread: window.activeSpread || 'single',", "spread: resolvedSpreadForQuestion(q),")
old_bind = """function bindLegacySpreadPicker() {
    const buttons = Array.from(document.querySelectorAll('[data-spread-choice]'));
    if (!buttons.length) return;
    const select = spread => {
        window.activeSpread = spread || 'single';
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));
        if (window.drawMode === 'manual') {
            window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
            const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';
            manualStatus();
        }
    };
    buttons.forEach(btn => btn.addEventListener('click', () => select(btn.dataset.spreadChoice)));
    select(window.activeSpread);
}
"""
new_bind = """function bindLegacySpreadPicker() {
    const selectEl = document.getElementById('spread-select');
    if (selectEl) {
        const select = spread => {
            window.activeSpread = ['auto', 'single', 'three_card'].includes(spread) ? spread : 'auto';
            window.effectiveSpread = null;
            selectEl.value = window.activeSpread;
            if (window.drawMode === 'manual') {
                window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
                const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';
                manualStatus();
            }
        };
        selectEl.addEventListener('change', () => select(selectEl.value));
        select(window.activeSpread);
        return;
    }
    const buttons = Array.from(document.querySelectorAll('[data-spread-choice]'));
    if (!buttons.length) return;
    const choose = spread => {
        window.activeSpread = spread || 'single';
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));
    };
    buttons.forEach(btn => btn.addEventListener('click', () => choose(btn.dataset.spreadChoice)));
    choose(window.activeSpread);
}
"""
if old_bind not in main:
    raise SystemExit('bindLegacySpreadPicker block not found')
main = main.replace(old_bind, new_bind)
main = main.replace("    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.classList.toggle('active', btn.dataset.drawMode === window.drawMode));", "    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.classList.toggle('active', btn.dataset.drawMode === window.drawMode));\n    const summary = document.getElementById('draw-mode-summary');\n    if (summary) summary.textContent = window.drawMode === 'manual' ? uiText('draw_mode_manual', '手動') : uiText('draw_mode_auto', '自動');")
main_path.write_text(main)

css = css_path.read_text()
css += r'''

/* === Compact scalable spread selector v3 === */
#reading-config-card.reading-config-compact {
  margin: 16px 0 0;
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}
#reading-config-card.reading-config-compact::before { display: none; }
.compact-spread-picker {
  display: grid;
  grid-template-columns: auto minmax(150px, 240px);
  align-items: center;
  justify-content: center;
  gap: 8px 12px;
  padding: 12px 14px;
  border: 1px solid rgba(212,175,55,.22);
  border-radius: 14px;
  background: rgba(8,14,10,.72);
}
.compact-spread-label { color: rgba(244,241,234,.72); font-size: .78rem; font-weight: 700; }
.compact-spread-select {
  width: 100%;
  min-height: 42px;
  padding: 0 36px 0 14px;
  border: 1px solid rgba(212,175,55,.42);
  border-radius: 12px;
  color: #f2d56b;
  background: #0a100d;
  font: inherit;
  font-weight: 700;
}
.compact-spread-hint {
  grid-column: 2;
  margin-top: -2px;
  color: rgba(244,241,234,.42);
  font-size: .62rem;
}
.draw-mode-details {
  margin: 8px auto 0;
  width: min(100%, 430px);
  color: rgba(244,241,234,.58);
}
.draw-mode-details > summary {
  display: flex;
  justify-content: center;
  gap: 8px;
  padding: 6px 10px;
  cursor: pointer;
  font-size: .66rem;
  list-style: none;
}
.draw-mode-details > summary::-webkit-details-marker { display: none; }
#draw-mode-summary { color: rgba(226,190,66,.86); }
.compact-draw-mode {
  display: grid !important;
  grid-template-columns: 1fr 1fr;
  gap: 8px !important;
  padding: 8px 0 0 !important;
}
#reading-config-card .compact-draw-mode .legacy-spread-btn {
  min-height: 42px;
  padding: 8px 12px !important;
  border-radius: 10px !important;
  font-size: .72rem;
}
#reading-config-card .compact-draw-mode .legacy-spread-btn::before,
#reading-config-card .compact-draw-mode .legacy-spread-btn::after { display: none !important; }
#reading-config-card + #btn-primary-draw {
  width: min(100%, 430px);
  margin: 14px auto 28px;
  min-height: 52px;
  border-radius: 14px;
}
@media (max-width: 620px) {
  #reading-config-card.reading-config-compact { margin: 12px 4px 0; padding: 0 !important; }
  .compact-spread-picker { grid-template-columns: auto 1fr; padding: 10px 12px; }
  .compact-spread-hint { grid-column: 2; }
  #reading-config-card + #btn-primary-draw { width: calc(100% - 8px); margin-top: 12px; }
}
'''
css_path.write_text(css)

Path('website/tests/test_compact_spread_selector.py').write_text(r'''from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()
MAIN = (ROOT / 'main.js').read_text()
CSS = (ROOT / 'style.css').read_text()

def test_compact_selector_is_default_and_scalable():
    assert 'id="spread-select"' in HTML
    assert '<option value="auto" selected>自動</option>' in HTML
    assert '<option value="single"' in HTML
    assert '<option value="three_card"' in HTML
    assert 'window.activeSpread = \'auto\'' in MAIN
    assert 'resolvedSpreadForQuestion(q)' in MAIN

def test_manual_draw_is_secondary_but_preserved():
    assert 'id="draw-mode-details"' in HTML
    for token in ('id="draw-mode-picker"', 'id="manual-draw-stage"', 'id="btn-manual-shuffle"', 'id="btn-primary-draw"'):
        assert token in HTML
    assert 'Compact scalable spread selector v3' in CSS
''')
