from pathlib import Path
import re

p = Path('website/main.js')
s = p.read_text(encoding='utf-8')

m = re.search(r"function normalizeMasterShareText\(value\) \{.*?\n\}\n\nfunction latestMasterInterpretation", s, re.S)
if not m:
    raise SystemExit('normalizeMasterShareText block not found')
replacement = '''function normalizeMasterShareText(value) {
    const raw = String(value || '');
    const holder = document.createElement('div');
    holder.innerHTML = raw;
    holder.querySelectorAll('.hidden-quote, [hidden], [aria-hidden="true"]').forEach(node => node.remove());
    holder.querySelectorAll('[style]').forEach(node => {
        const style = String(node.getAttribute('style') || '').replace(/\\s+/g, '').toLowerCase();
        if (style.includes('display:none') || style.includes('visibility:hidden')) node.remove();
    });
    const plain = holder.textContent || holder.innerText || raw;
    return plain
        .replace(/^#{1,6}\\s+/gm, '')
        .replace(/\\*\\*(.*?)\\*\\*/g, '$1')
        .replace(/__(.*?)__/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\\[([^\\]]+)\\]\\([^\\)]+\\)/g, '$1')
        .replace(/[ \\t]+\\n/g, '\\n')
        .replace(/\\n{3,}/g, '\\n\\n')
        .trim();
}

function applySingleCardShareFallback(shareU) {
    const state = window.currentReadingState;
    const cards = Array.isArray(state?.cards) ? state.cards : [];
    const first = cards[0] || null;
    const spread = state?.spread || window.currentReadingEnvelope?.method_result?.spread || 'single';
    if (spread !== 'single') return;
    const cardId = first?.card_id || state?.card_id || window.currentDrawnCard?.id || null;
    const orientation = first?.orientation || state?.orientation || 'upright';
    if (cardId) shareU.searchParams.set('card', cardId);
    if (orientation) shareU.searchParams.set('orientation', orientation);
}

function latestMasterInterpretation'''
s = s[:m.start()] + replacement + s[m.end():]

pattern = re.compile(
    r"(?P<indent>^[ \t]*)if \(envelope\?\.reading_id && envelope\?\.share_token\) \{\n"
    r"(?P=indent)    shareU\.searchParams\.set\('reading', envelope\.reading_id\);\n"
    r"(?P=indent)    shareU\.searchParams\.set\('share', envelope\.share_token\);\n"
    r"(?P=indent)\}\n",
    re.M,
)

def inject(match):
    block = match.group(0)
    indent = match.group('indent')
    return block + f"{indent}applySingleCardShareFallback(shareU);\n"

s, count = pattern.subn(inject, s)
if count < 2:
    raise SystemExit(f'expected at least 2 share receipt blocks, got {count}')

p.write_text(s, encoding='utf-8')
print(f'patched share receipt blocks: {count}')
