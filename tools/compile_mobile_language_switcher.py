from pathlib import Path

style = Path('website/style.css')
s = style.read_text(encoding='utf-8')
marker = '/* Mobile language switcher v1 */'
if marker not in s:
    s += r'''

/* Mobile language switcher v1 */
@media (max-width: 768px) {
  .navbar {
    justify-content: space-between !important;
    gap: 8px !important;
    overflow-x: hidden !important;
    overflow-y: hidden !important;
    padding: 0 10px !important;
  }

  .nav-logo {
    min-width: 0 !important;
    flex: 0 0 auto !important;
    max-width: 92px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  #global-stats,
  #user-spirit-badge,
  .nav-links > a {
    display: none !important;
  }

  .nav-links {
    display: flex !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    justify-content: flex-end !important;
    gap: 0 !important;
    overflow: visible !important;
  }

  .lang-switcher {
    flex: 0 1 auto !important;
    min-width: 0 !important;
    max-width: calc(100vw - 112px) !important;
    gap: 2px !important;
    padding: 3px !important;
    overflow: visible !important;
    white-space: nowrap;
    touch-action: manipulation;
  }

  .lang-btn {
    flex: 0 1 auto !important;
    min-width: 0 !important;
    padding: 5px 7px !important;
    font-size: 0.68rem !important;
    white-space: nowrap !important;
    touch-action: manipulation;
  }
}

@media (max-width: 390px) {
  .nav-logo { max-width: 72px; font-size: 0.72rem !important; }
  .lang-switcher { max-width: calc(100vw - 88px) !important; }
  .lang-btn { padding: 5px 5px !important; font-size: 0.62rem !important; }
}
'''
style.write_text(s, encoding='utf-8')

t = Path('website/tests/test_mobile_language_switcher.py')
t.write_text('''from pathlib import Path\n\n\ndef test_mobile_nav_does_not_require_horizontal_page_scroll():\n    css=(Path(__file__).resolve().parents[1]/"style.css").read_text(encoding="utf-8")\n    assert "/* Mobile language switcher v1 */" in css\n    block=css.split("/* Mobile language switcher v1 */",1)[1]\n    assert "overflow-x: hidden !important" in block\n    assert ".nav-links > a" in block\n    assert ".lang-switcher" in block\n    assert "touch-action: manipulation" in block\n''', encoding='utf-8')
