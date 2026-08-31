from pathlib import Path
style=Path('website/style.css')
css=style.read_text(encoding='utf-8')
marker='/* Reading setup intrinsic-width containment */'
if marker not in css:
    css += '''\n\n/* Reading setup intrinsic-width containment */\n.reading-config-card,\n.reading-config-group,\n.reading-config-card .legacy-spread-picker,\n.reading-config-card .manual-draw-stage,\n.reading-config-card .manual-card-pool {\n  min-width: 0 !important;\n  width: 100% !important;\n  max-width: 100% !important;\n  box-sizing: border-box !important;\n}\n.reading-config-card { overflow: hidden; }\n'''
style.write_text(css,encoding='utf-8')
