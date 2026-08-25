from pathlib import Path

root = Path(__file__).resolve().parents[1]
web = root / 'website'

p = web / 'main.js'
s = p.read_text(encoding='utf-8')

old = """        root.style.setProperty('--theme-background', c.background || '#030504');
        root.style.setProperty('--theme-surface', c.surface || '#111714');
        root.style.setProperty('--theme-accent', c.accent || '#d4af37');
        root.style.setProperty('--theme-text', c.text || '#f4efe4');
        document.body.style.backgroundColor = c.background || '#030504';
        document.body.style.color = c.text || '#f4efe4';
"""
new = """        root.style.setProperty('--theme-background', c.background || '#030504');
        root.style.setProperty('--theme-surface', c.surface || '#111714');
        root.style.setProperty('--theme-accent', c.accent || '#d4af37');
        root.style.setProperty('--theme-text', c.text || '#f4efe4');
        // Map Theme Contract onto the site's existing design tokens.
        root.style.setProperty('--color-bg', c.background || '#030504');
        root.style.setProperty('--color-panel', c.surface || '#111714');
        root.style.setProperty('--color-gold', c.accent || '#d4af37');
        root.style.setProperty('--color-gold-dim', c.accent || '#d4af37');
        root.style.setProperty('--color-text-pri', c.text || '#f4efe4');
        document.body.style.backgroundColor = c.background || '#030504';
        document.body.style.color = c.text || '#f4efe4';
"""
if old in s:
    s = s.replace(old, new, 1)

old_fetch = """        resp = await fetch('/api/v1/readings', {
            method: 'POST', signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                method: 'tarot', persona: window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'master', question: q,
                input: { spread: 'auto', deck_id: window.activeDeckId },
                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
            })
        });
"""
new_fetch = """        const pending = window.pendingReadingSession;
        const requestBody = pending ? {
            readingId: pending.reading_id,
            sessionToken: pending.session_token,
            question: q,
            lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
        } : {
            method: 'tarot', persona: window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'master', question: q,
            input: { spread: 'auto', deck_id: window.activeDeckId },
            lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
        };
        resp = await fetch('/api/v1/readings', {
            method: 'POST', signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
"""
if old_fetch not in s:
    raise SystemExit('reading fetch anchor not found')
s = s.replace(old_fetch, new_fetch, 1)

old_status = """    if (!resp.ok) throw new Error(`DIVINATION_V1_${resp.status}`);
    const data = await resp.json();
"""
new_status = """    if (!resp.ok) {
        let errData = {};
        try { errData = await resp.json(); } catch (_) {}
        if (errData.reading_id && errData.session_token) {
            window.pendingReadingSession = {reading_id: errData.reading_id, session_token: errData.session_token};
        }
        const err = new Error(errData.message || `DIVINATION_V1_${resp.status}`);
        err.status = resp.status;
        err.code = errData.code || errData.error;
        throw err;
    }
    const data = await resp.json();
    window.pendingReadingSession = null;
"""
if old_status not in s:
    raise SystemExit('reading status anchor not found')
s = s.replace(old_status, new_status, 1)

old_custom_catch = """        if (window.activeDeckId !== 'leopardcat') { alert(e?.message?.includes('503') ? 'AI 大師目前忙碌。你的牌組沒有問題，請稍後再按一次占卜。' : '這副牌目前無法完成占卜，請稍後再試。'); return; }
"""
new_custom_catch = """        if (window.activeDeckId !== 'leopardcat') {
            const msg = e?.code === 'free_quota_exhausted'
                ? '今天的免費 AI 額度暫時用完。你的牌局已保留，稍後再按一次就會沿用原牌，不會重新抽。'
                : (e?.status === 503 ? 'AI 大師目前忙碌。你的牌局已保留，稍後再按一次就會沿用原牌。' : (e?.message || '這副牌目前無法完成占卜，請稍後再試。'));
            alert(msg);
            document.getElementById('fortune-ritual-area')?.classList.remove('hidden');
            document.getElementById('fortune-chat-area')?.classList.add('hidden');
            return;
        }
"""
if old_custom_catch not in s:
    raise SystemExit('custom catch anchor not found')
s = s.replace(old_custom_catch, new_custom_catch, 1)

p.write_text(s, encoding='utf-8')
print('theme_zero_cost_refinement=applied')
