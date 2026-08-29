from pathlib import Path


def test_card_scroll_contract_is_unified():
    js = Path("website/main.js").read_text(encoding="utf-8")
    css = Path("website/style.css").read_text(encoding="utf-8")
    assert js.count("function bindCardInteractions(") == 1
    assert js.count("bindCardInteractions(cardInner, scrollableContent)") == 2  # helper signature + built-in call
    assert js.count("bindCardInteractions(cardInner, scrollable);") == 1
    assert js.count("scrollableContent.addEventListener('wheel'") == 1
    assert "touchmove" in js
    assert css.count("/* Card back scrolling: one contract for built-in and creator decks. */") == 1
    assert css.count("Long card meanings: keep the back readable") == 0
