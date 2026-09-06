from pathlib import Path


def source():
    return Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')


def test_ios_square_uses_deterministic_canvas2d_renderer():
    src = source()
    assert 'async function renderMobileSafeSquareCanvas' in src
    assert '? await renderMobileSafeSquareCanvas(shareContext, shareEntries, shareTheme, quote)' in src


def test_ios_native_share_does_not_wait_for_og_dom_raster():
    src = source()
    assert "if (!isIOSShareRuntime())" in src
    assert 'void persistReadingSharePreview(ogBlob)' in src
    assert "console.warn('[Share] OG render unavailable; native share remains valid'" in src


def test_renderer_preserves_spread_orientation_from_canonical_entries():
    src = source()
    assert 'shareEntries.forEach((entry, index)' in src
    assert "if (entry.orientation === 'reversed') ctx.rotate(Math.PI);" in src
    assert 'getShareCardImage(entry.card, shareContext.deckId)' in src
    assert 'updateSocialLinks(currentDrawnCard, bestQuote);' not in src
