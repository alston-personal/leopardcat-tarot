from pathlib import Path


def test_mobile_language_switcher_keeps_all_locales_tappable_without_navbar_scroll():
    css = (Path(__file__).resolve().parents[1] / "style.css").read_text(encoding="utf-8")
    block = css.split("/* Mobile language switcher v1 */", 1)[1]
    assert "overflow-x: hidden !important" in block
    assert ".nav-links > a" in block
    assert ".lang-switcher" in block
    assert "touch-action: manipulation" in block
    assert "max-width: calc(100vw - 112px)" in block
