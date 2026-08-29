from pathlib import Path


def test_mobile_nav_does_not_require_horizontal_page_scroll():
    css=(Path(__file__).resolve().parents[1]/"style.css").read_text(encoding="utf-8")
    assert "/* Mobile language switcher v1 */" in css
    block=css.split("/* Mobile language switcher v1 */",1)[1]
    assert "overflow-x: hidden !important" in block
    assert ".nav-links > a" in block
    assert ".lang-switcher" in block
    assert "touch-action: manipulation" in block
