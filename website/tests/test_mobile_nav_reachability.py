from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def test_language_switcher_is_compact_select():
    js=(ROOT/"main.js").read_text(encoding="utf-8")
    assert "document.createElement('select')" in js
    assert "language-select" in js
    assert "window.setLanguage(event.target.value)" in js

def test_mobile_nav_wraps_without_sacrificing_existing_controls():
    css=(ROOT/"style.css").read_text(encoding="utf-8")
    marker="/* Governed mobile nav reachability v3: wrap, never hide capabilities for space. */"
    assert marker in css
    block=css.split(marker,1)[1]
    assert "flex-wrap: wrap !important" in block
    assert "overflow-x: hidden !important" in block
    for selector in ("#global-stats", ".nav-links > a", "#user-spirit-badge", "#user-dharma-name", ".lang-switcher"):
        assert selector in block
    assert "#global-stats {\n    display: flex !important" in block
    assert "#user-dharma-name {\n    display: inline-block !important" in block

def test_mobile_reachability_is_governed():
    caps=(ROOT.parent/"governance/capabilities.json").read_text(encoding="utf-8")
    guard=(ROOT.parent/"scripts/check_capability_regressions.py").read_text(encoding="utf-8")
    assert '"navigation.mobile-reachability"' in caps
    assert 'navigation.mobile-reachability' in guard
