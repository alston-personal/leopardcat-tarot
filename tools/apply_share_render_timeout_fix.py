from pathlib import Path

p = Path('website/main.js')
s = p.read_text(encoding='utf-8')
marker = "// 📸 Share Image Generator\nwindow.generateShareImage = async function() {"
helper = r'''function shareRenderBudgetMs() {
    // Mobile Safari can spend well over 20s decoding multiple high-resolution card faces
    // before html2canvas resolves. Keep a finite fail-closed budget, but do not kill a
    // healthy render at the old 20s desktop-oriented threshold.
    const mobileSafari = /iP(?:hone|ad|od)/i.test(navigator.userAgent);
    return mobileSafari ? 60000 : 35000;
}

async function renderShareCanvas(target, options, label = 'share') {
    const timeoutMs = shareRenderBudgetMs();
    let timer = null;
    try {
        return await Promise.race([
            html2canvas(target, {
                ...options,
                foreignObjectRendering: false,
                imageTimeout: Math.min(Number(options?.imageTimeout || 5000), 5000)
            }),
            new Promise((_, reject) => {
                timer = setTimeout(() => reject(new Error(`TIMEOUT:${label}:${timeoutMs}`)), timeoutMs);
            })
        ]);
    } finally {
        if (timer) clearTimeout(timer);
    }
}

// 📸 Share Image Generator
window.generateShareImage = async function() {'''
if helper not in s:
    if marker not in s:
        raise SystemExit('generator marker not found')
    s = s.replace(marker, helper, 1)

old = r'''        const canvas = await Promise.race([
            html2canvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: shareTheme.background,
                scale: 1.0, 
                width: 600,
                height: 600,
                imageTimeout: 5000, 
                removeContainer: true
            }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('TIMEOUT')), 20000))
        ]);'''
new = r'''        const canvas = await renderShareCanvas(template, {
            useCORS: true,
            allowTaint: true,
            logging: false,
            backgroundColor: shareTheme.background,
            scale: 1.0,
            width: 600,
            height: 600,
            imageTimeout: 5000,
            removeContainer: true
        }, 'square');'''
if old in s:
    s = s.replace(old, new, 1)
elif new not in s:
    raise SystemExit('square render block not found')

old_og = r'''            const ogCanvas = await html2canvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: shareTheme.background,
                scale: 1.0,
                width: 1200,
                height: 630,
                imageTimeout: 5000,
                removeContainer: true
            });'''
new_og = r'''            const ogCanvas = await renderShareCanvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: shareTheme.background,
                scale: 1.0,
                width: 1200,
                height: 630,
                imageTimeout: 5000,
                removeContainer: true
            }, 'og');'''
if old_og in s:
    s = s.replace(old_og, new_og, 1)
elif new_og not in s:
    raise SystemExit('OG render block not found')

p.write_text(s, encoding='utf-8')

# Focused source regression test. This intentionally guards the production failure mode:
# the old unconditional 20s race must never return.
t = Path('website/tests/test_share_render_timeout.py')
t.write_text(r'''from pathlib import Path


def test_mobile_share_render_has_safari_budget_and_shared_timeout_wrapper():
    src = Path(__file__).parents[1].joinpath('main.js').read_text(encoding='utf-8')
    assert 'function shareRenderBudgetMs()' in src
    assert 'mobileSafari ? 60000 : 35000' in src
    assert "renderShareCanvas(template, {" in src
    assert "}, 'square');" in src
    assert "}, 'og');" in src
    assert "reject(new Error('TIMEOUT')), 20000" not in src
''', encoding='utf-8')
