from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / "main.js").read_text(encoding="utf-8")


def block(start: str, end: str) -> str:
    assert start in MAIN, start
    assert end in MAIN, end
    return MAIN.split(start, 1)[1].split(end, 1)[0]


def test_primary_tarot_flow_never_falls_back_to_legacy_ai():
    draw = block("window.drawFortune = async function() {", "window.activeDeckId =")
    assert "window.getModularReading(q)" in draw
    assert "getAIReading" not in draw
    assert "Falling back to legacy fortune API" not in draw
    assert "refundLocalMana()" in draw
    assert "showModularRetry(q, e)" in draw


def test_modular_error_always_removes_sensing_and_preserves_retry_session():
    modular = block("window.getModularReading = async function(q) {", "window.getAIReading =")
    assert "const removeSensing" in modular
    assert "catch (e)" in modular and "removeSensing();" in modular
    assert "if (!resp.ok)" in modular
    assert "window.pendingReadingSession" in modular
    assert "errData.reading_id" in modular
    assert "errData.session_token" in modular


def test_retry_uses_same_modular_reading_path():
    retry = block("function showModularRetry(q, error) {", "window.drawFortune =")
    assert "await window.getModularReading(q)" in retry
    assert "window.getAIReading" not in retry
    assert "refundLocalMana()" in retry
