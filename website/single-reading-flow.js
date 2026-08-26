// Runtime guard for the in-page Tarot experience.
// Keeps one modular reading request, one sensing bubble, and one retry state.
// Legacy /api/fortune must never be silently invoked after a modular failure.

const originalModularReading = window.getModularReading;

function clearReadingSensing() {
    document.querySelectorAll('#chat-history .spirit-thinking').forEach(el => {
        el.closest('.chat-bubble')?.remove();
    });
}

function retryMessage(error) {
    const zh = (window.currentLang || 'zh') === 'zh';
    if (error?.code === 'free_quota_exhausted' || error?.status === 429) {
        return zh
            ? '今天的免費 AI 額度暫時用完。牌局已保留，稍後重新祈請會沿用同一副牌。'
            : 'The free AI quota is temporarily exhausted. Your draw is preserved for retry.';
    }
    if (error?.status === 503 || error?.name === 'AbortError') {
        return zh
            ? '大師目前暫時無法回應。牌局已保留，重新祈請不會重抽。'
            : 'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.';
    }
    return error?.message || (zh ? '目前無法完成解讀，請稍後再試。' : 'Unable to complete the reading right now.');
}

function showSingleRetry(question, error) {
    clearReadingSensing();
    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());

    const history = document.getElementById('chat-history');
    if (!history) return;

    const bubble = document.createElement('div');
    bubble.className = 'chat-bubble assistant modular-retry-bubble';

    const text = document.createElement('p');
    text.style.color = 'var(--color-gold)';
    text.textContent = retryMessage(error);

    const btn = document.createElement('button');
    btn.className = 'retry-btn';
    btn.textContent = (window.currentLang || 'zh') === 'zh' ? '重新祈請' : 'Retry';
    btn.style.display = 'block';
    btn.style.margin = '10px auto 0';
    btn.addEventListener('click', async () => {
        btn.disabled = true;
        bubble.remove();
        try {
            await window.getModularReading(question);
        } catch (nextError) {
            showSingleRetry(question, nextError);
        }
    });

    bubble.append(text, btn);
    history.appendChild(bubble);
    history.scrollTop = history.scrollHeight;
}

if (typeof originalModularReading === 'function') {
    window.getModularReading = async function guardedModularReading(question) {
        try {
            return await originalModularReading(question);
        } catch (error) {
            clearReadingSensing();
            window.__lastModularReadingError = error;
            throw error;
        }
    };
}

// main.js currently calls getAIReading only as a legacy fallback after the
// modular path fails. Replace that fallback with the single retry state.
// This prevents a second sensing bubble and prevents extra /api/fortune calls.
window.getAIReading = async function disabledLegacyReadingFallback(question) {
    const error = window.__lastModularReadingError || new Error('MODULAR_READING_UNAVAILABLE');
    window.__lastModularReadingError = null;
    clearReadingSensing();
    showSingleRetry(question, error);
};

window.__singleReadingFlowGuard = true;
