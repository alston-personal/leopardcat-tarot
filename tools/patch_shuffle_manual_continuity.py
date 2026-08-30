from pathlib import Path

root = Path(__file__).resolve().parents[1]
main_path = root / 'website/main.js'
main = main_path.read_text(encoding='utf-8')

# Preserve manual selection authority across a network-layer failure that occurs
# before the server can return a reading session receipt.
anchor = "window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };\n"
if anchor not in main:
    raise SystemExit('manual draw state anchor missing')
main = main.replace(anchor, anchor + "window.pendingDrawOptions = null; // preserves manual seed/indices until a reading receipt exists\n", 1)

old = """        try {\n            await window.getModularReading(q);\n        } catch (e) {\n"""
new = """        try {\n            await window.getModularReading(q, window.pendingDrawOptions || {});\n        } catch (e) {\n"""
if old not in main:
    raise SystemExit('retry getModularReading anchor missing')
main = main.replace(old, new, 1)

old = """    appendBubble('user', q);\n    try {\n        await window.getModularReading(q, {drawIndices, seed});\n"""
new = """    appendBubble('user', q);\n    window.pendingDrawOptions = Array.isArray(drawIndices) ? {drawIndices: drawIndices.slice(), seed} : {};\n    try {\n        await window.getModularReading(q, window.pendingDrawOptions);\n"""
if old not in main:
    raise SystemExit('performReading pending options anchor missing')
main = main.replace(old, new, 1)

old = """    const data = await resp.json();\n    window.pendingReadingSession = null;\n"""
new = """    const data = await resp.json();\n    window.pendingReadingSession = null;\n    window.pendingDrawOptions = null;\n"""
if old not in main:
    raise SystemExit('success clear pending options anchor missing')
main = main.replace(old, new, 1)

# Reload/shared-receipt state must retain the draw provenance that is already
# immutable inside method_result.
old = """        spread: data.method_result?.spread || 'single',\n        cards: specs.map(spec => ({card_id: spec.card_id || spec.id, orientation: spec.orientation || 'upright', position: spec.position, position_label: spec.position_label}))\n    };\n"""
new = """        spread: data.method_result?.spread || 'single',\n        draw_mode: data.method_result?.rules?.draw_mode || 'auto',\n        draw_indices: data.method_result?.rules?.draw_indices || [],\n        cards: specs.map(spec => ({card_id: spec.card_id || spec.id, orientation: spec.orientation || 'upright', draw_index: spec.draw_index, position: spec.position, position_label: spec.position_label}))\n    };\n"""
if old not in main:
    raise SystemExit('buildReadingStateFromEnvelope anchor missing')
main = main.replace(old, new, 1)

# Reset also invalidates any pre-receipt manual retry material.
old = """    window.currentReadingState = null;\n    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };\n    lastShareFile = null;\n"""
new = """    window.currentReadingState = null;\n    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false };\n    window.pendingDrawOptions = null;\n    lastShareFile = null;\n"""
if old not in main:
    raise SystemExit('reset continuity anchor missing')
main = main.replace(old, new, 1)

main_path.write_text(main, encoding='utf-8')

test_path = root / 'website/tests/test_shuffle_manual_continuity.py'
test_path.write_text(r'''from pathlib import Path

JS = Path('main.js').read_text(encoding='utf-8')


def test_reload_state_preserves_draw_provenance():
    block = JS.split('function buildReadingStateFromEnvelope', 1)[1].split('async function restoreReadingAfterReload', 1)[0]
    assert "draw_mode: data.method_result?.rules?.draw_mode || 'auto'" in block
    assert "draw_indices: data.method_result?.rules?.draw_indices || []" in block
    assert 'draw_index: spec.draw_index' in block


def test_network_retry_reuses_same_manual_seed_and_indices():
    assert 'window.pendingDrawOptions = Array.isArray(drawIndices) ? {drawIndices: drawIndices.slice(), seed} : {}' in JS
    retry = JS.split('function showModularRetry', 1)[1].split('window.drawFortune', 1)[0]
    assert 'window.getModularReading(q, window.pendingDrawOptions || {})' in retry
    assert 'window.pendingDrawOptions = null;' in JS


def test_manual_selection_does_not_create_second_reading_algorithm():
    assert 'performReading(q, state.selected.slice(), state.seed)' in JS
    assert 'draw_indices: drawOptions.drawIndices' in JS
''', encoding='utf-8')

print('manual draw continuity patch applied')
