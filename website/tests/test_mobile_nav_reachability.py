from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_language_switcher_is_compact_select():
    js=(ROOT/"main.js").read_text(encoding="utf-8")
    assert "language-select" in js
    assert "document.createElement('select')" in js
    assert "window.setLanguage(event.target.value)" in js

def test_mobile_nav_preserves_original_controls():
    css=(ROOT/"style.css").read_text(encoding="utf-8")
    block=css.split("/* Mobile nav reachability + compact locale selector v2 */",1)[1]
    assert ".nav-links > a," in block
    assert "#user-spirit-badge { display: flex !important; }" in block
    assert "overflow-x: hidden !important" in block
    assert ".language-select" in block
