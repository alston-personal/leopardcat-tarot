from pathlib import Path
import re

js_path = Path('website/main.js')
css_path = Path('website/style.css')
js = js_path.read_text(encoding='utf-8')
css = css_path.read_text(encoding='utf-8')

marker = 'function createCardElement(card, groupId) {'
assert marker in js
helper = r'''function bindCardInteractions(cardInner, scrollableContent) {
    if (!cardInner || !scrollableContent || scrollableContent.dataset.cardInteractionsBound === '1') return;
    scrollableContent.dataset.cardInteractionsBound = '1';

    // One interaction contract for built-in and creator decks.
    // The meaning panel owns vertical gestures while it can scroll; card flipping
    // only happens from the non-scrollable card surface or the explicit back button.
    const consumeWheel = (e) => {
        const maxScroll = Math.max(0, scrollableContent.scrollHeight - scrollableContent.clientHeight);
        const atTop = scrollableContent.scrollTop <= 0;
        const atBottom = scrollableContent.scrollTop >= maxScroll - 1;
        const wantsUp = e.deltaY < 0;
        const wantsDown = e.deltaY > 0;
        const canScroll = maxScroll > 0 && !((wantsUp && atTop) || (wantsDown && atBottom));
        e.stopPropagation();
        if (canScroll) {
            e.preventDefault();
            scrollableContent.scrollTop += e.deltaY;
        }
    };

    scrollableContent.addEventListener('wheel', consumeWheel, { passive: false });
    scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
    scrollableContent.addEventListener('touchmove', (e) => e.stopPropagation(), { passive: true });
    scrollableContent.addEventListener('touchend', (e) => e.stopPropagation(), { passive: true });
    scrollableContent.addEventListener('click', (e) => e.stopPropagation());
    scrollableContent.addEventListener('mouseenter', () => {
        try { scrollableContent.focus({ preventScroll: true }); } catch (_) { scrollableContent.focus(); }
    });

    scrollableContent.querySelector('.card-flip-back')?.addEventListener('click', (e) => {
        e.stopPropagation();
        cardInner.classList.remove('is-flipped');
    });

    let touchStartY = 0;
    let touchStartTime = 0;
    cardInner.addEventListener('touchstart', (e) => {
        if (e.target.closest('.back-content')) return;
        touchStartY = e.touches[0].clientY;
        touchStartTime = Date.now();
    }, { passive: true });
    cardInner.addEventListener('touchend', (e) => {
        if (e.target.closest('.back-content')) return;
        const touchEndY = e.changedTouches[0].clientY;
        const touchDuration = Date.now() - touchStartTime;
        const scrollDiff = Math.abs(touchEndY - touchStartY);
        if (touchDuration < 250 && scrollDiff < 10) {
            e.stopPropagation();
            cardInner.classList.toggle('is-flipped');
        }
    }, { passive: true });
    cardInner.addEventListener('click', (e) => {
        if (e.target.closest('.back-content') || window.getSelection().toString()) return;
        cardInner.classList.toggle('is-flipped');
    });
}

'''
if 'function bindCardInteractions(' not in js:
    js = js.replace(marker, helper + marker, 1)

built_in_pattern = re.compile(r'''\n    // 🛡️ Interaction Isolation: Ensure Scroll > Flip on text areas\n    const scrollableContent = wrapper\.querySelector\('\.back-content'\);\n    if \(scrollableContent\) \{.*?\n    // Desktop support\n    cardInner\.addEventListener\('click', \(e\) => \{.*?\n    \}\);\n''', re.S)
replacement = "\n    const scrollableContent = wrapper.querySelector('.back-content');\n    bindCardInteractions(cardInner, scrollableContent);\n"
js, n = built_in_pattern.subn(replacement, js, count=1)
assert n == 1, f'built-in interaction block replacement count={n}'

custom_pattern = re.compile(r'''\n        const cardInner = wrapper\.querySelector\('\.card'\);\n        const scrollable = wrapper\.querySelector\('\.back-content'\);\n        scrollable\.addEventListener\('wheel'.*?\n        cardInner\.addEventListener\('click', \(\) => cardInner\.classList\.toggle\('is-flipped'\)\);\n''', re.S)
custom_replacement = "\n        const cardInner = wrapper.querySelector('.card');\n        const scrollable = wrapper.querySelector('.back-content');\n        bindCardInteractions(cardInner, scrollable);\n"
js, n = custom_pattern.subn(custom_replacement, js, count=1)
assert n == 1, f'custom interaction block replacement count={n}'

css_pattern = re.compile(r'''/\* Card Back Content Polish - DEFINITIVE FIX for Readability and Hierarchy \*/\n\.back-content \{.*?\n\.back-content::-webkit-scrollbar \{''', re.S)
css_block = r'''/* Card back scrolling: one contract for built-in and creator decks. */
.card-back {
  min-height: 0;
}
.back-content {
  flex: 1 1 auto;
  min-height: 0;
  height: 100%;
  max-height: 100%;
  display: flex;
  flex-direction: column;
  gap: 25px;
  overflow-y: auto;
  overflow-x: hidden;
  padding-right: 15px;
  padding-bottom: 18px;
  cursor: auto;
  touch-action: pan-y;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
  scrollbar-gutter: stable;
  scrollbar-width: thin;
  scrollbar-color: var(--color-gold) transparent;
  pointer-events: auto;
  position: relative;
  z-index: 10;
}

.back-content::-webkit-scrollbar {'''
css, n = css_pattern.subn(css_block, css, count=1)
assert n == 1, f'primary CSS consolidation count={n}'

tail_pattern = re.compile(r'''\n/\* Long card meanings: keep the back readable and independently scrollable\. \*/\n\.card-back \{ min-height: 0; \}\n\.back-content \{.*?\n\}\n(?=\.card-flip-back \{)''', re.S)
css, n = tail_pattern.subn('\n', css, count=1)
assert n == 1, f'tail duplicate CSS removal count={n}'

js_path.write_text(js, encoding='utf-8')
css_path.write_text(css, encoding='utf-8')

Path('website/tests/test_card_interaction_contract.py').write_text('''from pathlib import Path\n\n\ndef test_card_scroll_contract_is_unified():\n    js = Path(\"website/main.js\").read_text(encoding=\"utf-8\")\n    css = Path(\"website/style.css\").read_text(encoding=\"utf-8\")\n    assert js.count(\"function bindCardInteractions(\") == 1\n    assert js.count(\"bindCardInteractions(cardInner, scrollableContent)\") == 1\n    assert js.count(\"bindCardInteractions(cardInner, scrollable)\") == 1\n    assert js.count(\"scrollableContent.addEventListener('wheel'\") == 1\n    assert \"touchmove\" in js\n    assert css.count(\"/* Card back scrolling: one contract for built-in and creator decks. */\") == 1\n    assert css.count(\"Long card meanings: keep the back readable\") == 0\n''', encoding='utf-8')
