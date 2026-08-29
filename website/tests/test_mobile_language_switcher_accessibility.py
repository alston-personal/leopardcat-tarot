from pathlib import Path


def test_mobile_language_buttons_remain_direct_tap_targets():
    css = (Path(__file__).resolve().parents[1] / "style.css").read_text(encoding="utf-8")
    block = css.split("/* Mobile language switcher v1 */", 1)[1]
    assert ".lang-btn" in block
    assert "white-space: nowrap !important" in block
    assert "touch-action: manipulation" in block
