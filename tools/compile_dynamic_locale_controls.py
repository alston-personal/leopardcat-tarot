from pathlib import Path
ROOT=Path('.')
p=ROOT/'website/main.js'
s=p.read_text(encoding='utf-8')
s=s.replace("box.innerHTML = `<label style=\\\"display:flex;gap:6px;align-items:center\\\">${uiText('persona_label', 'Reader')} <select id=\\\"persona-switcher-select\\\" style=\\\"border-radius:999px;padding:4px 8px\\\"></select></label>`;","box.innerHTML = `<label style=\\\"display:flex;gap:6px;align-items:center\\\"><span class=\\\"persona-switcher-label\\\">${uiText('persona_label', 'Reader')}</span> <select id=\\\"persona-switcher-select\\\" style=\\\"padding:4px 8px\\\"></select></label>`;")
s=s.replace("box.innerHTML = `<label style=\\\"display:flex;gap:6px;align-items:center\\\">${uiText('theme_label', 'Theme')} <select id=\\\"theme-switcher-select\\\" style=\\\"border-radius:999px;padding:4px 8px\\\"></select></label>`;","box.innerHTML = `<label style=\\\"display:flex;gap:6px;align-items:center\\\"><span class=\\\"theme-switcher-label\\\">${uiText('theme_label', 'Theme')}</span> <select id=\\\"theme-switcher-select\\\" style=\\\"padding:4px 8px\\\"></select></label>`;")
marker="    document.querySelectorAll('.modular-retry-bubble').forEach(bubble => {"
insert="""    document.querySelectorAll('.persona-switcher-label').forEach(el => { el.textContent = uiText('persona_label', 'Reader'); });\n    document.querySelectorAll('.theme-switcher-label').forEach(el => { el.textContent = uiText('theme_label', 'Theme'); });\n\n"""
if insert not in s:
    s=s.replace(marker,insert+marker,1)
p.write_text(s,encoding='utf-8')

t=ROOT/'website/tests/test_public_ui_integrity.py'
ts=t.read_text(encoding='utf-8')
extra='''\n\ndef test_dynamic_persona_and_theme_labels_retranslate():\n    js=(ROOT/'main.js').read_text(encoding='utf-8')\n    assert 'persona-switcher-label' in js\n    assert 'theme-switcher-label' in js\n    assert "el.textContent = uiText('persona_label'" in js\n    assert "el.textContent = uiText('theme_label'" in js\n'''
if 'test_dynamic_persona_and_theme_labels_retranslate' not in ts:
    ts += extra
t.write_text(ts,encoding='utf-8')
