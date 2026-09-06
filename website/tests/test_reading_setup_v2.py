from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / 'index.html').read_text()
CSS = (ROOT / 'style.css').read_text()


def test_controller_ids_preserved():
    for token in ('id="reading-config-card"', 'id="legacy-spread-picker"', 'id="draw-mode-picker"', 'id="manual-draw-stage"', 'id="btn-primary-draw"'):
        assert token in HTML


def test_ritual_setup_v2_visual_contract():
    assert '/* === Ritual Reading Setup v2 === */' in CSS
    assert '[data-spread-choice="three_card"]::before' in CSS
    assert '[data-draw-mode="auto"]::after' in CSS
    assert '#reading-config-card + #btn-primary-draw' in CSS
    assert '@media (max-width: 620px)' in CSS
