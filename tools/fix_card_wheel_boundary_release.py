from pathlib import Path
p=Path('website/main.js')
s=p.read_text(encoding='utf-8')
old="""            e.stopPropagation();
            if (panelCanConsume) {
                e.preventDefault();
                scrollableContent.scrollTop += e.deltaY;
            }
"""
new="""            if (panelCanConsume) {
                e.preventDefault();
                e.stopPropagation();
                scrollableContent.scrollTop += e.deltaY;
            }
"""
if old not in s:
    raise SystemExit('wheel boundary block not found')
p.write_text(s.replace(old,new,1), encoding='utf-8')
print('card_wheel_boundary_release=applied')
