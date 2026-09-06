from pathlib import Path
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
