from pathlib import Path

path = Path('website/main.js')
s = path.read_text(encoding='utf-8')

old1 = """    const sensingId = 'sensing-' + Date.now();
    appendBubble('assistant', `<div id=\"${sensingId}\" class=\"spirit-thinking\">${common.msg_sensing}</div>`);
    const controller = new AbortController();
"""
new1 = """    const sensingId = 'sensing-' + Date.now();
    appendBubble('assistant', `<div id=\"${sensingId}\" class=\"spirit-thinking\">${common.msg_sensing}</div>`);
    const removeSensing = () => {
        const el = document.getElementById(sensingId);
        el?.closest('.chat-bubble')?.remove();
    };
    const controller = new AbortController();
"""

old2 = """        resp = await fetch('/api/v1/readings', {
            method: 'POST', signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
    } finally { clearTimeout(timeoutId); }
    if (!resp.ok) {
"""
new2 = """        resp = await fetch('/api/v1/readings', {
            method: 'POST', signal: controller.signal,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestBody)
        });
    } catch (e) {
        removeSensing();
        throw e;
    } finally { clearTimeout(timeoutId); }
    if (!resp.ok) {
        removeSensing();
"""

old3 = """    document.getElementById(sensingId)?.closest('.chat-bubble')?.remove();
    const specs = data.method_result?.cards || [];
"""
new3 = """    removeSensing();
    const specs = data.method_result?.cards || [];
"""

old4 = """window.drawFortune = async function() {
    const common = window.siteData[window.currentLang].common;
    if (chatQuota <= 0) return alert(common.err_mana_depleted);
    const q = document.getElementById('fortune-question').value;
    if (!q.trim()) return alert(common.err_empty_question);
    if (q.toUpperCase() !== 'DEBUG' && q.toUpperCase() !== 'FORCE_DEBUG') {
        if (chatQuota === 5) {
            lastManaRegen = Date.now();
            localStorage.setItem('lastManaRegen', lastManaRegen);
        }
        chatQuota--;
        updateUIQuota();
    }
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    try {
        await window.getModularReading(q);
    } catch (e) {
        console.warn('[Divination v1] Falling back to legacy fortune API:', e);
        if (window.activeDeckId !== 'leopardcat') {
            const msg = e?.code === 'free_quota_exhausted'
                ? '今天的免費 AI 額度暫時用完。你的牌局已保留，稍後再按一次就會沿用原牌，不會重新抽。'
                : (e?.status === 503 ? 'AI 大師目前忙碌。你的牌局已保留，稍後再按一次就會沿用原牌。' : (e?.message || '這副牌目前無法完成占卜，請稍後再試。'));
            alert(msg);
            document.getElementById('fortune-ritual-area')?.classList.remove('hidden');
            document.getElementById('fortune-chat-area')?.classList.add('hidden');
            return;
        }
        const card = window.cardData[Math.floor(Math.random() * window.cardData.length)];
        currentDrawnCard = card;
        window.currentDrawnCard = card;
        window.currentReadingEnvelope = null;
        await window.getAIReading(q, card);
    }
};
"""

new4 = """function modularErrorMessage(e) {
    if (e?.code === 'free_quota_exhausted' || e?.status === 429) {
        return window.currentLang === 'zh'
            ? '今天的免費 AI 額度暫時用完。牌局已保留，稍後可沿用同一副牌重新祈請。'
            : 'The free AI quota is temporarily exhausted. Your draw is preserved for retry.';
    }
    if (e?.status === 503 || e?.name === 'AbortError') {
        return window.currentLang === 'zh'
            ? '大師目前暫時無法回應。牌局已保留，重新祈請不會重抽。'
            : 'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.';
    }
    return e?.message || (window.currentLang === 'zh' ? '目前無法完成解讀，請稍後再試。' : 'Unable to complete the reading right now.');
}

function refundLocalMana() {
    chatQuota = Math.min(5, chatQuota + 1);
    updateUIQuota();
}

function chargeLocalMana() {
    if (chatQuota <= 0) return false;
    if (chatQuota === 5) {
        lastManaRegen = Date.now();
        localStorage.setItem('lastManaRegen', lastManaRegen);
    }
    chatQuota--;
    updateUIQuota();
    return true;
}

function showModularRetry(q, error) {
    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    const errBubble = appendBubble('assistant', '');
    if (!errBubble) return;
    errBubble.classList.add('modular-retry-bubble');
    const text = document.createElement('p');
    text.style.color = 'var(--color-gold)';
    text.textContent = modularErrorMessage(error);
    const btn = document.createElement('button');
    btn.className = 'retry-btn';
    btn.textContent = window.currentLang === 'zh' ? '重新祈請' : 'Retry';
    btn.style.display = 'block';
    btn.style.margin = '10px auto 0';
    btn.addEventListener('click', async () => {
        if (!chargeLocalMana()) {
            alert(window.siteData[window.currentLang].common.err_mana_depleted);
            return;
        }
        btn.disabled = true;
        errBubble.remove();
        try {
            await window.getModularReading(q);
        } catch (e) {
            refundLocalMana();
            showModularRetry(q, e);
        }
    });
    errBubble.append(text, btn);
}

window.drawFortune = async function() {
    const common = window.siteData[window.currentLang].common;
    const q = document.getElementById('fortune-question').value;
    if (!q.trim()) return alert(common.err_empty_question);
    const debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
    if (!debug && !chargeLocalMana()) return alert(common.err_mana_depleted);

    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    try {
        await window.getModularReading(q);
    } catch (e) {
        console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
        if (!debug) refundLocalMana();
        showModularRetry(q, e);
    }
};
"""

replacements = [(old1,new1),(old2,new2),(old3,new3),(old4,new4)]
for i,(old,new) in enumerate(replacements,1):
    if new in s:
        continue
    if old not in s:
        raise SystemExit(f'patch anchor {i} not found')
    s = s.replace(old,new,1)

path.write_text(s, encoding='utf-8')
print('single reading request flow patch applied')
