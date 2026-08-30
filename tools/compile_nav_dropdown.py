from pathlib import Path

main = Path('website/main.js')
s = main.read_text(encoding='utf-8')
old = '''function renderLanguageSwitcher() {
    const host = document.getElementById('lang-switcher');
    if (!host) return;
    const available = getAvailableLocales();
    host.innerHTML = '';
    available.forEach(lang => {
        const meta = window.localeMeta[lang] || {};
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'lang-btn';
        button.id = `btn-${lang}`;
        button.dataset.locale = lang;
        button.textContent = meta.label || lang.toUpperCase();
        button.setAttribute('aria-label', `Language: ${lang}`);
        button.addEventListener('click', () => window.setLanguage(lang));
        host.appendChild(button);
    });
}
'''
new = '''function renderLanguageSwitcher() {
    const host = document.getElementById('lang-switcher');
    if (!host) return;
    const available = getAvailableLocales();
    host.innerHTML = '';

    const select = document.createElement('select');
    select.id = 'language-select';
    select.className = 'language-select';
    select.setAttribute('aria-label', 'Language selector');

    available.forEach(lang => {
        const meta = window.localeMeta[lang] || {};
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = meta.label || lang.toUpperCase();
        option.selected = lang === window.currentLang;
        select.appendChild(option);
    });

    select.addEventListener('change', event => window.setLanguage(event.target.value));
    host.appendChild(select);
}
'''
if old not in s:
    raise SystemExit('renderLanguageSwitcher block not found')
s=s.replace(old,new,1)
needle = "    const activeBtn = document.getElementById(`btn-${lang}`);\n    if (activeBtn) activeBtn.classList.add('active');"
repl = "    const activeBtn = document.getElementById(`btn-${lang}`);\n    if (activeBtn) activeBtn.classList.add('active');\n    const languageSelect = document.getElementById('language-select');\n    if (languageSelect) languageSelect.value = lang;"
if needle not in s:
    raise SystemExit('active locale block not found')
s=s.replace(needle,repl,1)
main.write_text(s,encoding='utf-8')

style=Path('website/style.css')
css=style.read_text(encoding='utf-8')
css += r'''

/* Mobile nav reachability + compact locale selector v2 */
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
  .navbar {
    justify-content: space-between !important;
    overflow-x: hidden !important;
    overflow-y: visible !important;
    gap: 8px !important;
    padding: 0 10px !important;
  }
  .nav-logo { flex: 0 1 auto !important; min-width: 0 !important; max-width: 92px; }
  #global-stats { display: none !important; }
  .nav-links {
    display: flex !important;
    flex: 1 1 auto !important;
    min-width: 0 !important;
    justify-content: flex-end !important;
    align-items: center !important;
    gap: 6px !important;
    overflow: visible !important;
  }
  .nav-links > a,
  #user-spirit-badge { display: flex !important; }
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
  #user-dharma-name { display: none !important; }
  .lang-switcher { flex: 0 0 auto !important; padding: 0 !important; background: transparent !important; border: 0 !important; }
  .language-select { min-width: 72px; max-width: 82px; padding: 5px 6px; font-size: 0.68rem; }
}
'''
style.write_text(css,encoding='utf-8')

t=Path('website/tests/test_mobile_nav_reachability.py')
t.write_text('''from pathlib import Path\n\nROOT=Path(__file__).resolve().parents[1]\n\ndef test_language_switcher_is_compact_select():\n    js=(ROOT/"main.js").read_text(encoding="utf-8")\n    assert "language-select" in js\n    assert "document.createElement('select')" in js\n    assert "window.setLanguage(event.target.value)" in js\n\ndef test_mobile_nav_preserves_original_controls():\n    css=(ROOT/"style.css").read_text(encoding="utf-8")\n    block=css.split("/* Mobile nav reachability + compact locale selector v2 */",1)[1]\n    assert ".nav-links > a," in block\n    assert "#user-spirit-badge { display: flex !important; }" in block\n    assert "overflow-x: hidden !important" in block\n    assert ".language-select" in block\n''',encoding='utf-8')
