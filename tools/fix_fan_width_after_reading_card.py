from pathlib import Path
p=Path('website/main.js')
s=p.read_text(encoding='utf-8')
old="""    const total = Array.isArray(window.cardData) ? window.cardData.length : 0;\n    const back = activeCardBack();\n    for (let i = 1; i <= total; i++) {"""
new="""    const total = Array.isArray(window.cardData) ? window.cardData.length : 0;\n    const back = activeCardBack();\n    const measuredPoolWidth = pool.getBoundingClientRect().width || pool.clientWidth || 720;\n    const fanHalfWidth = Math.min(340, Math.max(120, measuredPoolWidth / 2 - 42));\n    for (let i = 1; i <= total; i++) {"""
if old not in s: raise SystemExit('pool width anchor missing')
s=s.replace(old,new,1)
old2="""        const fanX = fanPosition * Math.min(340, Math.max(180, total * 7));"""
new2="""        const fanX = fanPosition * fanHalfWidth;"""
if old2 not in s: raise SystemExit('fanX anchor missing')
s=s.replace(old2,new2,1)
p.write_text(s,encoding='utf-8')

style=Path('website/style.css')
css=style.read_text(encoding='utf-8')
marker='/* Reading setup intrinsic-width containment */'
if marker not in css:
    css += '''\n\n/* Reading setup intrinsic-width containment */\n.reading-config-card,\n.reading-config-group,\n.reading-config-card .legacy-spread-picker,\n.reading-config-card .manual-draw-stage,\n.reading-config-card .manual-card-pool {\n  min-width: 0 !important;\n  width: 100% !important;\n  max-width: 100% !important;\n  box-sizing: border-box !important;\n}\n.reading-config-card {\n  overflow: hidden;\n}\n'''
style.write_text(css,encoding='utf-8')

t=Path('website/tests/test_share_og_and_reading_controls.py')
ts=t.read_text(encoding='utf-8')
ts += '''\n\ndef test_manual_fan_width_tracks_available_control_surface_width():\n    js = (ROOT / 'main.js').read_text(encoding='utf-8')\n    css = (ROOT / 'style.css').read_text(encoding='utf-8')\n    assert 'const measuredPoolWidth = pool.getBoundingClientRect().width' in js\n    assert 'const fanHalfWidth = Math.min(340, Math.max(120, measuredPoolWidth / 2 - 42))' in js\n    assert 'const fanX = fanPosition * fanHalfWidth' in js\n    assert 'Reading setup intrinsic-width containment' in css\n    assert '.reading-config-card .manual-card-pool' in css\n    assert 'max-width: 100% !important' in css\n'''
t.write_text(ts,encoding='utf-8')
