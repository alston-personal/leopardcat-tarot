from pathlib import Path
import json

ROOT=Path('.')
main=ROOT/'website/main.js'
s=main.read_text(encoding='utf-8')
old='''function renderLanguageSwitcher() {\n    const host = document.getElementById('lang-switcher');\n    if (!host) return;\n    const available = getAvailableLocales();\n    host.innerHTML = '';\n    available.forEach(lang => {\n        const meta = window.localeMeta[lang] || {};\n        const button = document.createElement('button');\n        button.type = 'button';\n        button.className = 'lang-btn';\n        button.id = `btn-${lang}`;\n        button.dataset.locale = lang;\n        button.textContent = meta.label || lang.toUpperCase();\n        button.setAttribute('aria-label', `Language: ${lang}`);\n        button.addEventListener('click', () => window.setLanguage(lang));\n        host.appendChild(button);\n    });\n}\n'''
new='''function renderLanguageSwitcher() {\n    const host = document.getElementById('lang-switcher');\n    if (!host) return;\n    const available = getAvailableLocales();\n    host.innerHTML = '';\n\n    const select = document.createElement('select');\n    select.id = 'language-select';\n    select.className = 'language-select';\n    select.setAttribute('aria-label', 'Language selector');\n\n    available.forEach(lang => {\n        const meta = window.localeMeta[lang] || {};\n        const option = document.createElement('option');\n        option.value = lang;\n        option.textContent = meta.label || lang.toUpperCase();\n        option.selected = lang === window.currentLang;\n        select.appendChild(option);\n    });\n\n    select.addEventListener('change', event => window.setLanguage(event.target.value));\n    host.appendChild(select);\n}\n'''
if old not in s: raise SystemExit('language switcher source block not found')
s=s.replace(old,new,1)
needle="    const activeBtn = document.getElementById(`btn-${lang}`);\n    if (activeBtn) activeBtn.classList.add('active');"
repl=needle+"\n    const languageSelect = document.getElementById('language-select');\n    if (languageSelect) languageSelect.value = lang;"
if needle not in s: raise SystemExit('active locale sync block not found')
s=s.replace(needle,repl,1)
main.write_text(s,encoding='utf-8')

style=ROOT/'website/style.css'
css=style.read_text(encoding='utf-8')
css += r'''

/* Governed mobile nav reachability v3: wrap, never hide capabilities for space. */
.language-select {
  appearance: auto;
  background: rgba(255,255,255,0.06);
  color: var(--color-text-pri);
  border: 1px solid rgba(212,175,55,0.35);
  border-radius: 16px;
  padding: 6px 10px;
  font: inherit;
  min-width: 84px;
  cursor: pointer;
}
.language-select option { color: #111; background: #fff; }

@media (max-width: 768px) {
  :root { --nav-height: 112px; }
  .navbar {
    height: auto !important;
    min-height: var(--nav-height) !important;
    justify-content: space-between !important;
    align-content: center !important;
    flex-wrap: wrap !important;
    gap: 4px 8px !important;
    overflow-x: hidden !important;
    overflow-y: visible !important;
    padding: 6px 10px !important;
  }
  .nav-logo {
    min-width: 0 !important;
    max-width: 112px !important;
    flex: 0 1 auto !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  #global-stats {
    display: flex !important;
    flex: 0 1 auto !important;
    gap: 6px !important;
    padding-left: 6px !important;
    font-size: 0.56rem !important;
  }
  .nav-links {
    display: flex !important;
    flex: 1 1 100% !important;
    width: 100% !important;
    min-width: 0 !important;
    justify-content: center !important;
    align-items: center !important;
    flex-wrap: wrap !important;
    gap: 4px !important;
    overflow: visible !important;
  }
  .nav-links > a,
  #user-spirit-badge {
    display: flex !important;
  }
  .nav-links > a {
    padding: 4px 7px !important;
    font-size: 0.62rem !important;
    letter-spacing: 0 !important;
    white-space: nowrap;
  }
  #user-spirit-badge {
    padding: 3px 6px !important;
    gap: 4px !important;
  }
  #user-dharma-name {
    display: inline-block !important;
    max-width: 72px !important;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .lang-switcher {
    display: flex !important;
    flex: 0 0 auto !important;
    padding: 0 !important;
    background: transparent !important;
    border: 0 !important;
    overflow: visible !important;
  }
  .language-select {
    min-width: 72px;
    max-width: 92px;
    padding: 5px 6px;
    font-size: 0.68rem;
  }
}

@media (max-width: 420px) {
  :root { --nav-height: 132px; }
  .nav-logo { max-width: 86px !important; font-size: 0.7rem !important; }
  #global-stats { font-size: 0.52rem !important; }
  .nav-links > a { font-size: 0.58rem !important; padding: 3px 5px !important; }
  #user-dharma-name { max-width: 58px !important; }
  .language-select { min-width: 66px; max-width: 80px; font-size: 0.62rem; }
}
'''
style.write_text(css,encoding='utf-8')

cap=ROOT/'governance/capabilities.json'
data=json.loads(cap.read_text(encoding='utf-8'))
data['protected_capabilities']['navigation.mobile-reachability']={
  'status':'protected',
  'owner':'website',
  'contract':[
    'Responsive layout changes may compact, wrap or reorganize navigation but may not make an existing navigation capability unreachable merely to free screen space.',
    'Mobile navigation must keep the existing primary links, identity/mana control, statistics and locale switcher reachable without requiring horizontal page or navbar scrolling.',
    'A control remaining in the DOM does not satisfy this contract if responsive CSS hides it without an equivalent reachable replacement.'
  ],
  'evidence':['website/index.html','website/style.css','website/main.js','website/tests/test_mobile_nav_reachability.py']
}
cap.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

guard=ROOT/'scripts/check_capability_regressions.py'
g=guard.read_text(encoding='utf-8')
needle='''    fortune_server = require("website/fortune_server.py")\n'''
repl=needle+'''    style_css = require("website/style.css")\n'''
if needle not in g: raise SystemExit('guard evidence block not found')
g=g.replace(needle,repl,1)
insert='''\n    # Responsive presence is not enough: protected navigation must remain reachable.\n    if protected.get("navigation.mobile-reachability", {}).get("status") == "protected":\n        marker = "/* Governed mobile nav reachability v3: wrap, never hide capabilities for space. */"\n        if marker not in style_css:\n            fail("mobile navigation reachability contract has no governed responsive implementation")\n        mobile = style_css.split(marker, 1)[1]\n        required_visible = [\n            "#global-stats",\n            ".nav-links > a",\n            "#user-spirit-badge",\n            "#user-dharma-name",\n            ".lang-switcher",\n        ]\n        for selector in required_visible:\n            if selector not in mobile:\n                fail(f"mobile navigation reachability evidence missing selector: {selector}")\n        if "flex-wrap: wrap !important" not in mobile:\n            fail("mobile navigation must wrap instead of deleting capabilities for space")\n        if "overflow-x: hidden !important" not in mobile:\n            fail("mobile navbar horizontal-scroll regression protection disappeared")\n        if "document.createElement('select')" not in main_js or "language-select" not in main_js:\n            fail("compact data-driven locale selector disappeared")\n'''
anchor='''    # Preserve AI multilingual platform rules.\n'''
if anchor not in g: raise SystemExit('guard insertion anchor not found')
g=g.replace(anchor,insert+'\n'+anchor,1)
guard.write_text(g,encoding='utf-8')

t=ROOT/'website/tests/test_mobile_nav_reachability.py'
t.write_text('''from pathlib import Path\n\nROOT=Path(__file__).resolve().parents[1]\n\ndef test_language_switcher_is_compact_select():\n    js=(ROOT/"main.js").read_text(encoding="utf-8")\n    assert "document.createElement('select')" in js\n    assert "language-select" in js\n    assert "window.setLanguage(event.target.value)" in js\n\ndef test_mobile_nav_wraps_without_sacrificing_existing_controls():\n    css=(ROOT/"style.css").read_text(encoding="utf-8")\n    marker="/* Governed mobile nav reachability v3: wrap, never hide capabilities for space. */"\n    assert marker in css\n    block=css.split(marker,1)[1]\n    assert "flex-wrap: wrap !important" in block\n    assert "overflow-x: hidden !important" in block\n    for selector in ("#global-stats", ".nav-links > a", "#user-spirit-badge", "#user-dharma-name", ".lang-switcher"):\n        assert selector in block\n    assert "#global-stats {\\n    display: flex !important" in block\n    assert "#user-dharma-name {\\n    display: inline-block !important" in block\n\ndef test_mobile_reachability_is_governed():\n    caps=(ROOT.parent/"governance/capabilities.json").read_text(encoding="utf-8")\n    guard=(ROOT.parent/"scripts/check_capability_regressions.py").read_text(encoding="utf-8")\n    assert '"navigation.mobile-reachability"' in caps\n    assert 'navigation.mobile-reachability' in guard\n''',encoding='utf-8')
