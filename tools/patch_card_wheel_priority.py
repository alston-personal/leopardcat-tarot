from pathlib import Path
p=Path('website/main.js')
s=p.read_text(encoding='utf-8')
old="""        scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
        scrollableContent.addEventListener('touchend', (e) => e.stopPropagation(), { passive: true });
        scrollableContent.addEventListener('wheel', (e) => e.stopPropagation(), { passive: true });
        scrollableContent.addEventListener('click', (e) => e.stopPropagation());
"""
new="""        scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
        scrollableContent.addEventListener('touchend', (e) => e.stopPropagation(), { passive: true });
        // Desktop wheel priority: while the pointer is over card meanings, consume wheel
        // events whenever this panel can scroll in that direction. Only hand control back
        // to the page after the panel is already at the corresponding boundary.
        scrollableContent.addEventListener('wheel', (e) => {
            const maxScroll = Math.max(0, scrollableContent.scrollHeight - scrollableContent.clientHeight);
            const atTop = scrollableContent.scrollTop <= 0;
            const atBottom = scrollableContent.scrollTop >= maxScroll - 1;
            const wantsUp = e.deltaY < 0;
            const wantsDown = e.deltaY > 0;
            const panelCanConsume = maxScroll > 0 && !((wantsUp && atTop) || (wantsDown && atBottom));

            e.stopPropagation();
            if (panelCanConsume) {
                e.preventDefault();
                scrollableContent.scrollTop += e.deltaY;
            }
        }, { passive: false });
        scrollableContent.addEventListener('click', (e) => e.stopPropagation());
"""
if old not in s:
    raise SystemExit('target block not found')
p.write_text(s.replace(old,new,1),encoding='utf-8')
print('card_wheel_priority_patch=applied')
