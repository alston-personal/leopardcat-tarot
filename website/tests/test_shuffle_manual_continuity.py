from pathlib import Path

JS = Path('main.js').read_text(encoding='utf-8')

# This contract intentionally covers draw provenance across reload and retry.

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
