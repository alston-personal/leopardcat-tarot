from pathlib import Path

main = Path('website/main.js')
src = main.read_text(encoding='utf-8')

old_ios = """function isIOSShareRuntime() {\n    return /iP(?:hone|ad|od)/i.test(navigator.userAgent);\n}\n"""
new_ios = """function isIOSShareRuntime() {\n    // Do not rely on UA alone. iPadOS desktop mode and embedded WKWebView/PWA\n    // runtimes can omit the classic iPhone/iPad/iPod token even though they\n    // still have the same WebKit rendering constraints.\n    const ua = String(navigator.userAgent || '');\n    const platform = String(navigator.platform || '');\n    const touchPoints = Number(navigator.maxTouchPoints || 0);\n    const explicitIOS = /iP(?:hone|ad|od)/i.test(`${ua} ${platform}`);\n    const touchMacIOS = platform === 'MacIntel' && touchPoints > 1;\n    const standaloneIOS = typeof navigator.standalone !== 'undefined' && touchPoints > 0;\n    return explicitIOS || touchMacIOS || standaloneIOS;\n}\n"""
if src.count(old_ios) != 1:
    raise SystemExit(f'expected exactly one iOS runtime function, found {src.count(old_ios)}')
src = src.replace(old_ios, new_ios, 1)

old_restore = """    document.getElementById('fortune-actions')?.classList.remove('hidden');\n    updateSocialLinks(currentDrawnCard);\n    return true;\n"""
new_restore = """    document.getElementById('fortune-actions')?.classList.remove('hidden');\n    const restoredCards = Array.isArray(window.currentReadingState?.cards) ? window.currentReadingState.cards : [];\n    const restoredSpread = window.currentReadingState?.spread || data.method_result?.spread || (restoredCards.length > 1 ? 'three_card' : 'single');\n    if (restoredSpread === 'single' && restoredCards.length <= 1) {\n        updateSocialLinks(currentDrawnCard);\n    } else {\n        // A restored multi-card reading has higher semantic authority than\n        // currentDrawnCard. Do not let the legacy single-card writer collapse it\n        // to the first card; social links are rebuilt from canonical reading state\n        // when the share artifact is generated.\n        lastShareBaseMessage = '';\n        lastShareUrl = '';\n        lastShareText = '';\n        document.getElementById('social-share-row')?.classList.add('hidden');\n    }\n    return true;\n"""
if src.count(old_restore) != 1:
    raise SystemExit(f'expected exactly one restored-reading social anchor, found {src.count(old_restore)}')
src = src.replace(old_restore, new_restore, 1)
main.write_text(src, encoding='utf-8')

test = Path('website/tests/test_ios_share_runtime_v2.py')
test.write_text("""from pathlib import Path\n\n\ndef source():\n    return Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')\n\n\ndef test_ios_runtime_detection_is_not_ua_only():\n    src = source()\n    assert \"const platform = String(navigator.platform || '');\" in src\n    assert \"const touchPoints = Number(navigator.maxTouchPoints || 0);\" in src\n    assert \"platform === 'MacIntel' && touchPoints > 1\" in src\n    assert \"typeof navigator.standalone !== 'undefined' && touchPoints > 0\" in src\n    assert \"return /iP(?:hone|ad|od)/i.test(navigator.userAgent);\" not in src\n\n\ndef test_restored_multicard_reading_cannot_use_single_card_social_writer():\n    src = source()\n    assert \"const restoredCards = Array.isArray(window.currentReadingState?.cards) ? window.currentReadingState.cards : [];\" in src\n    assert \"if (restoredSpread === 'single' && restoredCards.length <= 1)\" in src\n    assert \"updateSocialLinks(currentDrawnCard);\" in src\n    restore_block = src[src.index('async function restoreReadingAfterReload()'):src.index('// ⚡ Restored to normal limit (5) for production')]\n    assert restore_block.count('updateSocialLinks(currentDrawnCard);') == 1\n    assert \"document.getElementById('social-share-row')?.classList.add('hidden');\" in restore_block\n\n\ndef test_ios_share_still_routes_to_canvas2d():\n    src = source()\n    assert \"isIOSShareRuntime()\n            ? await renderMobileSafeSquareCanvas(shareContext, shareEntries, shareTheme, quote)\" in src\n    assert \"if (!isIOSShareRuntime()) {\" in src\n""", encoding='utf-8')

fixture = Path('docs/experience/IOS_SHARE_RENDERER_CEIR_FIXTURE.md')
if fixture.exists():
    text = fixture.read_text(encoding='utf-8')
    marker = '## Follow-up: runtime classification and restore projection'
    if marker not in text:
        text += """\n\n## Follow-up: runtime classification and restore projection\n\nReal-device reproduction after the first Canvas2D change exposed two additional causal edges:\n\n- platform routing itself is an authority decision: a UA-only classifier can incorrectly route an iOS WebView/PWA back to the superseded DOM-raster path;\n- restoring an N-card reading and then invoking a single-card social writer is another forbidden lossy transition, even if the initial draw path is monotonic.\n\nNew invariants:\n\n1. runtime classification for safety-critical renderer selection must use multiple platform/capability signals, not a single UA token;\n2. `reading_state(cards.length > 1) -> currentDrawnCard -> social/share authority` is forbidden in restore paths as well as fresh-reading paths;\n3. a fix is not accepted until the actual production artifact identity is proven and real-device evidence passes.\n"""
        fixture.write_text(text, encoding='utf-8')
