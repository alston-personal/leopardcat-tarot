from pathlib import Path


def source():
    return Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')


def test_ios_runtime_detection_is_not_ua_only():
    src = source()
    assert "const platform = String(navigator.platform || '');" in src
    assert "const touchPoints = Number(navigator.maxTouchPoints || 0);" in src
    assert "platform === 'MacIntel' && touchPoints > 1" in src
    assert "typeof navigator.standalone !== 'undefined' && touchPoints > 0" in src
    assert "return /iP(?:hone|ad|od)/i.test(navigator.userAgent);" not in src


def test_restored_multicard_reading_cannot_use_single_card_social_writer():
    src = source()
    assert "const restoredCards = Array.isArray(window.currentReadingState?.cards) ? window.currentReadingState.cards : [];" in src
    assert "if (restoredSpread === 'single' && restoredCards.length <= 1)" in src
    restore_block = src[src.index('async function restoreReadingAfterReload()'):src.index('// ⚡ Restored to normal limit (5) for production')]
    assert restore_block.count('updateSocialLinks(currentDrawnCard);') == 1
    assert "document.getElementById('social-share-row')?.classList.add('hidden');" in restore_block


def test_ios_share_still_routes_to_canvas2d():
    src = source()
    assert 'isIOSShareRuntime()' in src
    assert 'renderMobileSafeSquareCanvas(shareContext, shareEntries, shareTheme, quote)' in src
    assert 'if (!isIOSShareRuntime()) {' in src
