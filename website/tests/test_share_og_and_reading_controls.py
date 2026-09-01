from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_reading_controls_are_grouped_without_changing_controller_ids():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    css = (ROOT / 'style.css').read_text(encoding='utf-8')
    assert 'id="reading-config-card"' in html
    assert 'id="legacy-spread-picker"' in html
    assert 'id="draw-mode-picker"' in html
    assert 'id="manual-draw-stage"' in html
    assert '.reading-config-card .legacy-spread-btn.active' in css
    assert '@media (max-width: 700px)' in css


def test_social_preview_has_dedicated_landscape_render():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    css = (ROOT / 'style.css').read_text(encoding='utf-8')
    assert "template.classList.add('share-og-mode')" in js
    assert "template.classList.remove('share-og-mode')" in js
    assert 'width: 1200' in js
    assert 'height: 630' in js
    assert 'persistReadingSharePreview(ogBlob)' in js
    assert '.share-card-body.share-og-mode' in css
    assert 'width: 1200px !important' in css
    assert 'height: 630px !important' in css


def test_square_native_share_is_preserved_separately_from_og_blob():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    assert "const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'))" in js
    assert 'let ogBlob = blob' in js
    assert 'const file = new File([blob]' in js


def test_manual_fan_width_tracks_available_control_surface_width():
    js = (ROOT / 'main.js').read_text(encoding='utf-8')
    css = (ROOT / 'style.css').read_text(encoding='utf-8')
    assert 'const measuredPoolWidth = pool.getBoundingClientRect().width' in js
    assert 'const fanHalfWidth = Math.min(340, Math.max(120, measuredPoolWidth / 2 - 42))' in js
    assert 'const fanX = fanPosition * fanHalfWidth' in js
    assert 'Reading setup intrinsic-width containment' in css
    assert '.reading-config-card .manual-card-pool' in css
    assert 'max-width: 100% !important' in css
