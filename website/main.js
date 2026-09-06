const APP_VERSION = "v45-EX-TURBO";
const BUILD_DATE = "2026-05-15-H10";
console.log(`%c ✨ LeopardCat Tarot ${APP_VERSION} | ${BUILD_DATE} `, "background: #d4af37; color: #000; font-weight: bold; padding: 4px; border-radius: 4px;");
window.appVersion = APP_VERSION;

// Global state
let revealObserver;
window.requestedLang = localStorage.getItem('leopard-lang') || navigator.language || 'zh';
window.currentLang = window.requestedLang;
window.localeMeta = {
    zh: { label: '中', htmlLang: 'zh-TW' },
    en: { label: 'EN', htmlLang: 'en' },
    ja: { label: '日本語', htmlLang: 'ja' },
    ko: { label: '한국어', htmlLang: 'ko' },
    es: { label: 'ES', htmlLang: 'es' }
};

function normalizeLocaleTag(lang) {
    return String(lang || '').trim().replace('_', '-').toLowerCase();
}

function getAvailableLocales() {
    return window.siteData && typeof window.siteData === 'object' ? Object.keys(window.siteData) : [];
}

function resolveLocale(requested) {
    const available = getAvailableLocales();
    if (!available.length) return normalizeLocaleTag(requested) || 'zh';

    const normalized = normalizeLocaleTag(requested);
    const exact = available.find(key => normalizeLocaleTag(key) === normalized);
    if (exact) return exact;

    const family = normalized.split('-')[0];
    const familyMatch = available.find(key => normalizeLocaleTag(key).split('-')[0] === family);
    if (familyMatch) return familyMatch;

    if (available.includes('zh')) return 'zh';
    if (available.includes('en')) return 'en';
    return available[0];
}

function getLocaleData(lang = window.currentLang) {
    const resolved = resolveLocale(lang);
    return (window.siteData && window.siteData[resolved]) || {};
}

function uiText(key, fallback = '', params = {}) {
    const common = getLocaleData()?.common || {};
    let value = common[key] ?? fallback;
    return String(value).replace(/\{(\w+)\}/g, (_, name) => params[name] ?? `{${name}}`);
}

function getAILanguageTag(lang = window.currentLang) {
    const resolved = resolveLocale(lang);
    return ({ zh: 'zh-TW', en: 'en', ja: 'ja', ko: 'ko', es: 'es' })[resolved] || resolved || 'en';
}

function detectQuestionLanguage(text, fallback = window.currentQuestionLanguage || getAILanguageTag()) {
    const value = String(text || '').trim();
    if (!value) return fallback || getAILanguageTag();
    if (/[ぁ-ゖァ-ヺー]/.test(value)) return 'ja';
    if (/[가-힣]/.test(value)) return 'ko';
    if (/[㐀-鿿]/.test(value)) return 'zh-TW';
    if (/[¿¡ñáéíóúü]/i.test(value) || /(?:que|qué|para|por|una|uno|como|cómo|cuando|cuándo|donde|dónde|gracias|quiero|puede|puedo|será|futuro)/i.test(value)) return 'es';
    if (/[A-Za-z]/.test(value)) return 'en';
    return fallback || getAILanguageTag();
}

function getQuestionLanguageTag(text) {
    const detected = detectQuestionLanguage(text);
    window.currentQuestionLanguage = detected;
    return detected;
}

function getLocalizedField(value, lang = window.currentLang) {
    if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
    const resolved = resolveLocale(lang);
    if (value[resolved] != null) return value[resolved];
    const family = normalizeLocaleTag(resolved).split('-')[0];
    const familyKey = Object.keys(value).find(key => normalizeLocaleTag(key).split('-')[0] === family);
    if (familyKey && value[familyKey] != null) return value[familyKey];
    if (value.zh != null) return value.zh;
    if (value.en != null) return value.en;
    const first = Object.keys(value)[0];
    return first ? value[first] : null;
}

function renderLanguageSwitcher() {
    const host = document.getElementById('lang-switcher');
    if (!host) return;
    const available = getAvailableLocales();
    host.innerHTML = '';

    const select = document.createElement('select');
    select.id = 'language-select';
    select.className = 'language-select';
    select.setAttribute('aria-label', 'Language selector');

    available.forEach(lang => {
        const meta = window.localeMeta[lang] || {};
        const option = document.createElement('option');
        option.value = lang;
        option.textContent = meta.label || lang.toUpperCase();
        option.selected = lang === window.currentLang;
        select.appendChild(option);
    });

    select.addEventListener('change', event => window.setLanguage(event.target.value));
    host.appendChild(select);
}

function initializeLocaleRuntime() {
    window.currentLang = resolveLocale(window.requestedLang || window.currentLang);
    localStorage.setItem('leopard-lang', window.currentLang);
    renderLanguageSwitcher();
    const meta = window.localeMeta[window.currentLang] || {};
    document.documentElement.lang = meta.htmlLang || window.currentLang;
}

window.siteData = null;
window.cardData = [];
window.currentDrawnCard = null;
window.currentReadingEnvelope = null;
window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck
window.activeSpread = 'auto'; // requested spread mode; auto resolves from the question
window.effectiveSpread = null; // concrete spread selected for the current reading
window.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic
window.currentShareReceipt = null; // read-only receipt identity; never grants follow-up authority
window.drawMode = 'auto';
window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
window.pendingDrawOptions = null; // preserves manual seed/indices until a reading receipt exists
window.currentQuestionSource = null; // explicit public source metadata; never sent as a raw URL to the Master
window.currentQuestionLanguage = null; // latest user/question language, independent from UI locale

const THREADS_POST_URL_RE = /^https:\/\/(?:www\.)?threads\.(?:com|net)\/(?:@[^/]+\/post\/[A-Za-z0-9_-]+|share\/[A-Za-z0-9_-]+)\/?(?:[?#].*)?$/i;

async function resolveQuestionInput(rawQuestion) {
    const raw = String(rawQuestion || '').trim();
    if (!THREADS_POST_URL_RE.test(raw)) return { question: raw, source: null };
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 55000);
    try {
        const response = await fetch('/api/v1/sources/threads', {
            method: 'POST', signal: controller.signal,
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({url: raw})
        });
        const payload = await response.json().catch(() => ({}));
        if (!response.ok || !payload?.source?.text) throw new Error(payload?.error || 'THREADS_SOURCE_UNAVAILABLE');
        return { question: String(payload.source.text).trim(), source: payload.source };
    } finally {
        clearTimeout(timeoutId);
    }
}

function automaticSpreadForQuestion(question) {
    const q = String(question || '').trim();
    if (!q) return 'three_card';
    const simple = /^(?:今天|現在|目前|是否|能不能|可不可以|適不適合|會不會|要不要|should\s+i|is\s+it|will\s+i|can\s+i)/i.test(q);
    const complex = /(?:關係|比較|選擇|原因|阻礙|建議|發展|未來|過去|工作|感情|對方|兩個|方案|影響|走向)/.test(q);
    return simple && !complex && q.length <= 36 ? 'single' : 'three_card';
}

function resolvedSpreadForQuestion(question) {
    const resolved = window.activeSpread === 'auto' ? automaticSpreadForQuestion(question) : (window.activeSpread || 'single');
    window.effectiveSpread = resolved;
    return resolved;
}

function requiredDrawCount() {
    const spread = window.effectiveSpread || (window.activeSpread === 'auto' ? 'three_card' : window.activeSpread);
    return spread === 'single' ? 1 : 3;
}

function freshShuffleSeed() {
    const bytes = new Uint32Array(4);
    crypto.getRandomValues(bytes);
    return Array.from(bytes, n => n.toString(16).padStart(8, '0')).join('');
}

function activeCardBack() {
    return window.activeDeckInfo?.card_back || '/art/card-back.svg';
}

function manualStatus() {
    const el = document.getElementById('manual-draw-status');
    if (!el) return;
    if (window.manualDrawState.phase === 'shuffling') {
        el.textContent = uiText('manual_draw_shuffling', '洗牌中…');
        return;
    }
    if (!window.manualDrawState.shuffled) {
        el.textContent = uiText('manual_draw_shuffle_first', 'Shuffle first, then choose your cards.');
        return;
    }
    const need = requiredDrawCount();
    const selected = window.manualDrawState.selected.length;
    el.textContent = uiText('manual_draw_progress', 'Selected {selected} / {need}', {selected, need});
}

function nearestManualFanButton(pool, clientX) {
    const cards = [...pool.querySelectorAll('.manual-card-back:not(:disabled)')];
    let best = null;
    let bestDistance = Number.POSITIVE_INFINITY;
    const poolRect = pool.getBoundingClientRect();
    const poolCenter = poolRect.left + poolRect.width / 2;
    cards.forEach(button => {
        const fanX = Number.parseFloat(button.style.getPropertyValue('--fan-x')) || 0;
        const center = poolCenter + fanX;
        const distance = Math.abs(clientX - center);
        if (distance < bestDistance) { best = button; bestDistance = distance; }
    });
    return best;
}

function bindManualFanPointer(pool) {
    if (!pool || pool.dataset.fanPointerBound === 'true') return;
    pool.dataset.fanPointerBound = 'true';
    const isDesktopFan = () => !window.matchMedia?.('(max-width: 620px)').matches;
    const clearHover = () => pool.querySelectorAll('.manual-card-back.fan-hover').forEach(card => card.classList.remove('fan-hover'));
    pool.addEventListener('pointermove', event => {
        if (!isDesktopFan() || window.manualDrawState.phase === 'shuffling') return;
        const button = nearestManualFanButton(pool, event.clientX);
        clearHover();
        button?.classList.add('fan-hover');
    });
    pool.addEventListener('pointerleave', clearHover);
    pool.addEventListener('click', event => {
        if (event.target.closest?.('.manual-card-back') || !isDesktopFan()) return;
        const button = nearestManualFanButton(pool, event.clientX);
        if (!button) return;
        const index = Number(button.dataset.drawIndex);
        if (Number.isInteger(index)) selectManualCard(index, button);
    });
}

function renderManualCardPool() {
    const pool = document.getElementById('manual-card-pool');
    if (!pool) return;
    pool.innerHTML = '';
    const total = Array.isArray(window.cardData) ? window.cardData.length : 0;
    const back = activeCardBack();
    const measuredPoolWidth = pool.getBoundingClientRect().width || pool.clientWidth || 720;
    const fanHalfWidth = Math.min(340, Math.max(120, measuredPoolWidth / 2 - 42));
    for (let i = 1; i <= total; i++) {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'manual-card-back';
        button.dataset.drawIndex = String(i);
        const fanPosition = total > 1 ? ((i - 1) / (total - 1)) * 2 - 1 : 0;
        const fanAngle = fanPosition * 31;
        const fanX = fanPosition * fanHalfWidth;
        const fanY = Math.pow(Math.abs(fanPosition), 1.65) * 72;
        button.style.setProperty('--fan-x', `${fanX.toFixed(1)}px`);
        button.style.setProperty('--fan-y', `${fanY.toFixed(1)}px`);
        button.style.setProperty('--fan-angle', `${fanAngle.toFixed(2)}deg`);
        button.style.setProperty('--fan-mobile-angle', `${(fanAngle * 0.18).toFixed(2)}deg`);
        button.style.setProperty('--fan-z', String(i));
        button.style.setProperty('--shuffle-shift', `${i % 2 ? 34 : -34}px`);
        button.style.setProperty('--shuffle-delay', `${(i % 9) * 16}ms`);
        button.setAttribute('aria-label', uiText('manual_card_aria', 'Choose card position {index}', {index:i}));
        const img = document.createElement('img');
        img.src = back;
        img.alt = '';
        img.draggable = false;
        button.appendChild(img);
        if (window.manualDrawState.selected.includes(i)) button.classList.add('selected');
        button.addEventListener('click', () => selectManualCard(i, button));
        pool.appendChild(button);
    }
    bindManualFanPointer(pool);
    manualStatus();
}

window.setDrawMode = function(mode) {
    window.drawMode = mode === 'manual' ? 'manual' : 'auto';
    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.classList.toggle('active', btn.dataset.drawMode === window.drawMode));
    const summary = document.getElementById('draw-mode-summary');
    if (summary) summary.textContent = window.drawMode === 'manual' ? uiText('draw_mode_manual', '手動') : uiText('draw_mode_auto', '自動');
    const stage = document.getElementById('manual-draw-stage');
    const primary = document.getElementById('btn-primary-draw');
    stage?.classList.toggle('hidden', window.drawMode !== 'manual');
    primary?.classList.toggle('hidden', window.drawMode === 'manual');
    if (window.drawMode === 'manual') {
        window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
        const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';
        manualStatus();
    }
};

window.shuffleManualDeck = function() {
    const q = document.getElementById('fortune-question')?.value?.trim() || '';
    if (!q) return alert(uiText('err_empty_question', 'Please enter your question first.'));
    resolvedSpreadForQuestion(q);
    const seed = freshShuffleSeed();
    window.manualDrawState = { seed, selected: [], shuffled: false, submitting: false, phase: 'shuffling' };
    renderManualCardPool();
    const pool = document.getElementById('manual-card-pool');
    const shuffleButton = document.getElementById('btn-manual-shuffle');
    pool?.classList.remove('is-shuffling');
    void pool?.offsetWidth;
    pool?.classList.add('is-shuffling');
    if (shuffleButton) shuffleButton.disabled = true;
    manualStatus();
    const duration = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ? 240 : 1050;
    setTimeout(() => {
        if (window.manualDrawState.seed !== seed || window.drawMode !== 'manual') return;
        window.manualDrawState.shuffled = true;
        window.manualDrawState.phase = 'ready_to_draw';
        pool?.classList.remove('is-shuffling');
        if (shuffleButton) shuffleButton.disabled = false;
        manualStatus();
    }, duration);
};

async function selectManualCard(index, button) {
    const state = window.manualDrawState;
    if (!state.shuffled || state.submitting || state.selected.includes(index)) return;
    const need = requiredDrawCount();
    if (state.selected.length >= need) return;
    state.selected.push(index);
    button.classList.add('selected');
    button.disabled = true;
    manualStatus();
    if (state.selected.length === need) {
        state.submitting = true;
        const q = document.getElementById('fortune-question')?.value?.trim() || '';
        await new Promise(resolve => setTimeout(resolve, 320));
        await performReading(q, state.selected.slice(), state.seed);
    }
}

function bindDrawModePicker() {
    document.querySelectorAll('[data-draw-mode]').forEach(btn => btn.addEventListener('click', () => window.setDrawMode(btn.dataset.drawMode)));
    window.setDrawMode(window.drawMode);
}

const READING_SNAPSHOT_KEY = 'leopardcat.current-reading.v1';

function clearReadingSnapshot() {
    try { sessionStorage.removeItem(READING_SNAPSHOT_KEY); } catch (_) {}
}

function saveReadingSnapshot(data, question) {
    if (!data?.reading_id || !data?.method_result) return;
    const snapshot = {
        version: 1,
        saved_at: Date.now(),
        expires_at: data.expires_at,
        deck_id: window.activeDeckId,
        theme_id: window.activeThemeId,
        persona_id: data.persona || window.activePersonaId,
        question: question || '',
        envelope: data,
        reading_state: window.currentReadingState,
        chat_history: currentChatHistory,
        question_source: window.currentQuestionSource,
        question_language: window.currentQuestionLanguage,
    };
    try { sessionStorage.setItem(READING_SNAPSHOT_KEY, JSON.stringify(snapshot)); } catch (_) {}
    const u = new URL(location.href);
    u.searchParams.set('reading', data.reading_id);
    if (data.share_token) u.searchParams.set('share', data.share_token);
    else u.searchParams.delete('share');
    if (window.activeDeckId && window.activeDeckId !== 'leopardcat') u.searchParams.set('deck', window.activeDeckId); else u.searchParams.delete('deck');
    if (window.activeThemeId) u.searchParams.set('theme', window.activeThemeId);
    if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) u.searchParams.set('persona', window.activePersonaId);
    history.replaceState(null, '', u);
}

function buildReadingStateFromEnvelope(data) {
    const specs = data?.method_result?.cards || [];
    if (!specs.length) return null;
    const deckId = data.deck_id || data.method_result?.deck?.deck_id || window.activeDeckId || 'leopardcat';
    return {
        deck_id: deckId,
        theme_id: window.activeThemeId,
        persona_id: data.persona || window.activePersonaId,
        card_id: specs[0].card_id || specs[0].id,
        orientation: specs[0].orientation || 'upright',
        spread: data.method_result?.spread || 'single',
        draw_mode: data.method_result?.rules?.draw_mode || 'auto',
        draw_indices: data.method_result?.rules?.draw_indices || [],
        cards: specs.map(spec => ({card_id: spec.card_id || spec.id, orientation: spec.orientation || 'upright', draw_index: spec.draw_index, position: spec.position, position_label: spec.position_label}))
    };
}

async function restoreReadingAfterReload() {
    let snapshot = null;
    try {
        const raw = sessionStorage.getItem(READING_SNAPSHOT_KEY);
        if (raw) snapshot = JSON.parse(raw);
    } catch (_) {}
    if (snapshot?.expires_at && Number(snapshot.expires_at) * 1000 <= Date.now()) {
        clearReadingSnapshot(); snapshot = null;
    }
    const params = new URLSearchParams(location.search);
    const readingId = params.get('reading');
    const shareToken = params.get('share');
    let data = snapshot?.envelope || null;
    let question = snapshot?.question || '';
    let local = Boolean(data && (!readingId || data.reading_id === readingId));
    if ((!data || (readingId && data.reading_id !== readingId)) && readingId && shareToken) {
        try {
            const r = await fetch(`/api/v1/readings/${encodeURIComponent(readingId)}?shareToken=${encodeURIComponent(shareToken)}`, {cache:'no-store'});
            if (r.ok) { data = await r.json(); local = false; question = ''; }
        } catch (e) { console.warn('[Reading restore] shared reading unavailable', e); }
    }
    if (!data?.method_result?.cards?.length) return false;
    const deckId = data.deck_id || data.method_result?.deck?.deck_id || window.activeDeckId;
    if (deckId && deckId !== window.activeDeckId) return false; // URL carries deck so initialization should already match.
    const resolved = data.method_result.cards.map(spec => ({spec, card: window.cardData.find(c => c.id === (spec.card_id || spec.id)) || spec}));
    if (!resolved.length) return false;
    currentDrawnCard = resolved[0].card;
    window.currentDrawnCard = currentDrawnCard;
    window.currentReadingEnvelope = local ? data : null; // public share token never grants continuation authority.
    window.currentShareReceipt = data?.reading_id ? {reading_id: data.reading_id, share_token: data.share_token || shareToken || null} : null;
    window.currentReadingState = snapshot?.reading_state || buildReadingStateFromEnvelope(data);
    window.activeSpread = window.currentReadingState?.spread || window.activeSpread;
    window._lastQuestion = question;
    window.currentQuestionSource = local ? (snapshot?.question_source || null) : null;
    window.currentQuestionLanguage = local ? (snapshot?.question_language || (question ? detectQuestionLanguage(question) : null)) : null;
    window.pendingReadingSession = local && data.session_token ? {reading_id:data.reading_id, session_token:data.session_token} : null;
    currentChatHistory = local && Array.isArray(snapshot?.chat_history) ? snapshot.chat_history : [];

    const ritual = document.getElementById('fortune-ritual-area');
    const chat = document.getElementById('fortune-chat-area');
    if (ritual) ritual.classList.add('hidden');
    if (chat) chat.classList.remove('hidden');
    if (local && question) appendBubble('user', question);
    const pinnedArea = document.getElementById('pinned-card-area');
    const pinnedDisplay = document.getElementById('pinned-card-display');
    if (pinnedArea && pinnedDisplay) {
        pinnedArea.classList.remove('hidden');
        pinnedDisplay.innerHTML = `<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">${resolved.map(({spec,card}) => {
            const orientation = spec.orientation === 'reversed' ? uiText('orientation_reversed','Reversed') : uiText('orientation_upright','Upright');
            const pos = spec.position_label || spec.position || '';
            const title = getShareCardTitle(card);
            const rotate = spec.orientation === 'reversed' ? 'transform:rotate(180deg);' : '';
            const imageSrc = getShareCardImage(card, deckId);
            return `<div class="pinned-card-content" style="max-width:150px;"><img src="${imageSrc}" class="pinned-card-img" style="${rotate}"><div class="pinned-card-title">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;
        }).join('')}</div>`;
    }
    if (local && data.reading) {
        const spread = data.method_result?.spread || 'single';
        const bubble = appendBubble('assistant', `<strong>【${spread}】</strong><br>`);
        const body = document.createElement('div'); body.className='markdown-content';
        body.innerHTML = typeof marked !== 'undefined' ? marked.parse(data.reading) : String(data.reading).replace(/\n/g,'<br>');
        bubble?.appendChild(body);
    } else {
        appendBubble('assistant', uiText('shared_reading_restored', 'Shared reading restored. The original private question and Master answer are not stored; the immutable cards are shown below.'));
    }
    document.getElementById('fortune-actions')?.classList.remove('hidden');
    updateSocialLinks(currentDrawnCard);
    return true;
}

// ⚡ Restored to normal limit (5) for production
let chatQuota = 5;
let lastManaRegen = Date.now();

function checkAndRegenMana() {
    const now = Date.now();
    let quota = parseInt(localStorage.getItem('chatQuota'));
    if (isNaN(quota) || quota > 5) {
        quota = 5;
    }
    let lastRegen = parseInt(localStorage.getItem('lastManaRegen'));
    if (isNaN(lastRegen)) {
        lastRegen = now;
        localStorage.setItem('lastManaRegen', lastRegen);
    }

    if (quota >= 5) {
        lastRegen = now;
        localStorage.setItem('lastManaRegen', lastRegen);
        chatQuota = 5;
        lastManaRegen = lastRegen;
        return;
    }

    const msPassed = now - lastRegen;
    const regenInterval = 10 * 60 * 1000; // 10 minutes
    const pointsToRegen = Math.floor(msPassed / regenInterval);

    if (pointsToRegen > 0) {
        quota = Math.min(5, quota + pointsToRegen);
        if (quota === 5) {
            lastRegen = now;
        } else {
            lastRegen = lastRegen + (pointsToRegen * regenInterval);
        }
        localStorage.setItem('chatQuota', quota);
        localStorage.setItem('lastManaRegen', lastRegen);
    }
    
    chatQuota = quota;
    lastManaRegen = lastRegen;
}

// Perform initial offline regeneration calculation immediately
checkAndRegenMana();
let currentChatHistory = [];

// ⚡ Immediate assignment for global access
window.setLanguage = (lang) => {
    console.log("Setting language to:", lang);
    const resolved = resolveLocale(lang);
    if (!getAvailableLocales().includes(resolved)) return;
    if (resolved === window.currentLang) return;
    window.requestedLang = lang;
    window.currentLang = resolved;
    localStorage.setItem('leopard-lang', resolved);
    const meta = window.localeMeta[resolved] || {};
    document.documentElement.lang = meta.htmlLang || resolved;

    // Reset Dharma name for new language
    localStorage.removeItem('userDharmaName');
    initDharmaIdentity();

    applyLanguage();
};

// 🔱 Dharma Name Identity System
function initDharmaIdentity() {
    if (!window.siteData) return;
    const langData = getLocaleData();
    if (!langData || !langData.common) return;
    
    const common = langData.common;
    let name = localStorage.getItem('userDharmaName');
    
    // Only generate if none exists (prevents constant flickering)
    if (!name) {
        const prefixes = common.dharma_prefixes || [];
        const suffixes = common.dharma_suffixes || [];
        if (prefixes.length > 0 && suffixes.length > 0) {
            const p = prefixes[Math.floor(Math.random()*prefixes.length)];
            const s = suffixes[Math.floor(Math.random()*suffixes.length)];
            const id = Math.floor(Math.random() * 900) + 100; // 100-999
            name = `${p}${s} #${id}`;
            localStorage.setItem('userDharmaName', name);
        }
    }
    
    const nameElem = document.getElementById('user-dharma-name');
    if (nameElem) {
        nameElem.innerText = name;
        nameElem.title = uiText('dharma_redraw_title', 'Click to redraw name');
        nameElem.style.cursor = 'pointer';
        // 🔄 Allow redraw ritual
        nameElem.onclick = () => {
            if (confirm(uiText('dharma_redraw_confirm', 'Redraw your spiritual identity?'))) {
                localStorage.removeItem('userDharmaName');
                initDharmaIdentity();
            }
        };
    }
}

// Initialize Stats and Mana Regen
async function updateTempleStats() {
    try {
        const ts = Date.now();
        const res = await fetch(`/api/stats?t=${ts}`, { cache: 'no-cache' });
        const data = await res.json();
        const vElem = document.getElementById('stat-visitors');
        const dElem = document.getElementById('stat-divinations');
        if (vElem) vElem.innerText = data.total_visitors;
        if (dElem) dElem.innerText = data.total_divinations;
    } catch(e) { console.error("Stats Error:", e); }
}

function startManaRegen() {
    setInterval(() => {
        checkAndRegenMana();
        updateUIQuota();
    }, 30 * 1000); 
}

function updateUIQuota() {
    const manaDisplay = document.getElementById('user-mana-display');
    if (manaDisplay) manaDisplay.innerText = `⚡ ${chatQuota}/5`;
    localStorage.setItem('chatQuota', chatQuota);
}

// Initialize All Systems
async function initAllSystems() {
    console.log("Initializing Divination Platform...");
    const loadingOverlay = document.createElement('div');
    loadingOverlay.id = 'initial-loader';
    loadingOverlay.innerHTML = `<div class="spirit-thinking"><span></span><span></span><span></span></div><p style="color:var(--color-gold);margin-top:10px;font-size:0.8rem;letter-spacing:0.1em;">${uiText('loading_cards', 'Loading the card experience...')}</p>`;
    loadingOverlay.style = 'position:fixed;top:0;left:0;width:100%;height:100%;background:#030504;display:flex;flex-direction:column;justify-content:center;align-items:center;z-index:9999;transition:opacity 0.8s;';
    document.body.appendChild(loadingOverlay);

    try {
        const ts = Date.now();
        // ⚡ Stage 1: Load locales (Small) to get UI ready
        const cR = await fetch(`locales_v10.json?v=${ts}`, { cache: 'no-cache' });
        // Fade out loader regardless of success after 3 seconds as a safety net
        const hideLoader = () => {
            if (loadingOverlay.parentNode) {
                loadingOverlay.style.opacity = '0';
                setTimeout(() => loadingOverlay.remove(), 800);
            }
        };
        setTimeout(hideLoader, 3000); 

        if (cR.ok) {
            window.siteData = await cR.json();
            initializeLocaleRuntime();
            await window.loadActiveBrand();
            applyLanguage();
            initDharmaIdentity();
            updateTempleStats();
            checkAndRegenMana();
            startManaRegen();
            updateUIQuota();
            hideLoader(); // Success!
        }

        // ⚡ Stage 2: Bootstrap exactly one Deck Module.
        // Custom decks must never be overwritten by LeopardCat's built-in manifest.
        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') {
            await window.loadActiveDeckBranding();
            initScrollReveal();
        } else {
            const mR = await fetch(`manifest.json?v=${ts}`, { cache: 'no-cache' });
            if (mR.ok) {
                window.cardData = await mR.json();
                console.log("LeopardCat deck loaded, preparing gallery...");
                setTimeout(() => {
                    const groups = window.siteData[window.currentLang].groups;
                    renderGallery(groups, window.cardData);
                    initScrollReveal();
                }, 200);
            }
        }
        await restoreReadingAfterReload();
    } catch (err) {
        console.error('Initialization Failed:', err);
        const errType = err.name || "Error";
        const errMsg = err.message || "Unknown Failure";
        
        // 🛡️ Fail-Safe: If it's a transient DOM error, try one last time after a short delay
        setTimeout(() => {
            if (!window.siteData) return;
            applyLanguage();
            if (window.cardData && window.cardData.length > 0) {
                renderGallery(window.siteData[window.currentLang].groups, window.cardData);
            }
        }, 1000);

        loadingOverlay.innerHTML = `
            <div style="text-align:center; padding:20px;">
                <p style="color:#ff6b6b;font-size:0.8rem;">${uiText('init_connection_unstable', 'Spirit connection is unstable')} (${errType})</p>
                <p style="color:#666;font-size:0.6rem;margin-top:5px;">${errMsg}</p>
                <button onclick="location.reload()" style="margin-top:15px;background:none;border:1px solid var(--color-gold);color:var(--color-gold);padding:5px 15px;border-radius:15px;font-size:0.7rem;">${uiText('retry_ritual', 'Retry ritual')}</button>
            </div>
        `;
    }
}

function bindLegacySpreadPicker() {
    const selectEl = document.getElementById('spread-select');
    if (selectEl) {
        const select = spread => {
            window.activeSpread = ['auto', 'single', 'three_card'].includes(spread) ? spread : 'auto';
            window.effectiveSpread = null;
            selectEl.value = window.activeSpread;
            if (window.drawMode === 'manual') {
                window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
                const pool = document.getElementById('manual-card-pool'); if (pool) pool.innerHTML = '';
                manualStatus();
            }
        };
        selectEl.addEventListener('change', () => select(selectEl.value));
        select(window.activeSpread);
        return;
    }
    const buttons = Array.from(document.querySelectorAll('[data-spread-choice]'));
    if (!buttons.length) return;
    const choose = spread => {
        window.activeSpread = spread || 'single';
        buttons.forEach(btn => btn.classList.toggle('active', btn.dataset.spreadChoice === window.activeSpread));
    };
    buttons.forEach(btn => btn.addEventListener('click', () => choose(btn.dataset.spreadChoice)));
    choose(window.activeSpread);
}

document.addEventListener('DOMContentLoaded', bindLegacySpreadPicker);
document.addEventListener('DOMContentLoaded', bindDrawModePicker);
document.addEventListener('DOMContentLoaded', initAllSystems);

function applyLanguage() {
    if (!window.siteData || !window.cardData) {
        console.warn("[i18n] window.siteData or window.cardData not ready");
        return;
    }
    
    // Resolve against the locale bundle instead of a hard-coded language list.
    const lang = resolveLocale(window.currentLang || window.requestedLang);
    if (lang !== window.currentLang) window.currentLang = lang;
    const data = getLocaleData(lang);
    console.log(`[i18n] Applying language: ${lang}`, {
        available_langs: Object.keys(window.siteData),
        data_sample_keys: data ? Object.keys(data) : 'NULL'
    });

    // Recursive i18n lookup (Supports dot notation)
    const getI18nValue = (path, obj) => {
        if (!path || !obj) return null;
        const parts = path.split('.');
        let current = obj;
        for (const part of parts) {
            if (current && typeof current === 'object' && part in current) {
                current = current[part];
            } else {
                return null;
            }
        }
        return current;
    };

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const val = getI18nValue(key, data);
        
        if (val !== null && val !== undefined) {
            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                el.placeholder = val;
            } else {
                el.textContent = val;
            }
            // Success log (Optional/Debug)
            // console.log(`[i18n] Set ${key} -> ${val.toString().substring(0,20)}...`);
        } else {
            console.warn(`[i18n] Key not found in '${lang}': ${key}`);
        }
    });

    // Update active button state
    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-${lang}`);
    if (activeBtn) activeBtn.classList.add('active');
    const languageSelect = document.getElementById('language-select');
    if (languageSelect) languageSelect.value = lang;

    // Dynamic runtime states must change language too; static data-i18n alone is not enough.
    document.querySelectorAll('.persona-switcher-label').forEach(el => { el.textContent = uiText('persona_label', 'Reader'); });
    document.querySelectorAll('.theme-switcher-label').forEach(el => { el.textContent = uiText('theme_label', 'Theme'); });

    document.querySelectorAll('.modular-retry-bubble').forEach(bubble => {
        const code = bubble.dataset.errorCode || '';
        const status = Number(bubble.dataset.errorStatus || 0);
        const text = bubble.querySelector('.modular-error-text');
        const retry = bubble.querySelector('.retry-btn');
        if (text) text.textContent = modularErrorMessage({ code, status });
        if (retry) retry.textContent = uiText('retry', 'Retry');
    });

    // Update document title
    document.title = (data.hero && data.hero.title) ? `${data.hero.title} | LeopardCat Tarot` : 'LeopardCat Tarot';

    if (data.introduction) renderIntro(data.introduction);
    if (data.events) renderEvents(data.events);
    if (data.groups) renderGallery(data.groups, window.cardData);
}

function renderIntro(intro) {
    const desc = document.getElementById('intro-desc');
    if (desc) desc.textContent = intro.description;
    const statsContainer = document.getElementById('intro-stats');
    if (!statsContainer) return;
    statsContainer.innerHTML = (intro.stats || []).map(s => `
        <div class="stat-item reveal-on-scroll">
            <div class="stat-val">${s.value}</div>
            <div class="stat-lbl">${s.label}</div>
        </div>
    `).join('');
    statsContainer.querySelectorAll('.reveal-on-scroll').forEach(el => revealObserver?.observe(el));
}

function renderEvents(events) {
    const eventsList = document.getElementById('events-list');
    if (!eventsList) return;
    eventsList.innerHTML = (events || []).map(e => `
        <div class="event-card reveal-on-scroll">
            <div class="date">${e.date} | ${e.tag}</div>
            <h3>${e.title}</h3>
            <p class="content-text">${e.description}</p>
        </div>
    `).join('');
    eventsList.querySelectorAll('.reveal-on-scroll').forEach(el => revealObserver?.observe(el));
}

function renderGallery(groups, cards) {
    const container = document.getElementById('gallery-container');
    if (!container) return;
    container.innerHTML = `
        <div class="gallery-tabs-container">
            <div class="gallery-tabs">
                ${(groups || []).map((g, idx) => `<button class="tab-btn ${idx===0?'active':''}" data-group="${g.id}">${g.title.split('：')[0]}</button>`).join('')}
            </div>
        </div>
        <div id="active-group-content"></div>
    `;

    const tabScrollContainer = container.querySelector('.gallery-tabs-container');
    if (!tabScrollContainer) {
        console.warn("[Gallery] tabScrollContainer not found yet.");
        return;
    }

    // 🖱️ Definitive Desktop Scroll: Target the actual overflow container
    const handleWheel = (e) => {
        if (e.deltaY !== 0) {
            e.preventDefault();
            tabScrollContainer.scrollBy({
                left: e.deltaY * 1.5, 
                behavior: 'auto'
            });
        }
    };
    
    tabScrollContainer.addEventListener('wheel', handleWheel, { passive: false });
    const contentArea = container.querySelector('#active-group-content');

    const renderActiveGroup = (groupId) => {
        const group = groups.find(g => g.id === groupId);
        if (!group) return;

        contentArea.innerHTML = `
            <div class="group-info reveal-on-scroll">
                <h3>${group.title}</h3>
                <p class="content-text">${group.description}</p>
            </div>
            <div class="gallery-grid" id="grid-${group.id}"></div>
        `;

        const grid = contentArea.querySelector('.gallery-grid');
        let filtered = [];
        if (group.id === 'material') filtered = cards.filter(c => c.number >= 0 && c.number <= 7);
        else if (group.id === 'inner') filtered = cards.filter(c => c.number >= 8 && c.number <= 14);
        else if (group.id === 'cosmic') filtered = cards.filter(c => c.number >= 15 && c.number <= 21);
        else if (group.id === 'wands') filtered = cards.filter(c => c.number >= 101 && c.number <= 114);
        else if (group.id === 'cups') filtered = cards.filter(c => c.number >= 201 && c.number <= 214);
        else if (group.id === 'swords') filtered = cards.filter(c => c.number >= 301 && c.number <= 314);
        else if (group.id === 'pentacles') filtered = cards.filter(c => c.number >= 401 && c.number <= 414);
        else filtered = cards.filter(c => (c.suit === group.id));

        filtered.forEach(card => {
            const cardEl = createCardElement(card, group.id);
            grid.appendChild(cardEl);
            revealObserver?.observe(cardEl);
        });
        
        // window.scrollTo({ top: container.offsetTop - 100, behavior: 'smooth' });
    };

    tabScrollContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;
        tabScrollContainer.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        renderActiveGroup(btn.dataset.group);
    });

    // Initial render
    if (groups && groups.length > 0) renderActiveGroup(groups[0].id);
}

function formatEcologyText(text) {
    if (!text) return '';
    // Bold the tags and wrap them for styling
    return text.replace(/(Habitat:|Risk:|Note:|棲地:|風險:|備註:)/g, '<span class="ecology-tag">$1</span>');
}

function bindCardInteractions(cardInner, scrollableContent) {
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

function createCardElement(card, groupId) {
    if (!window.siteData) return document.createElement('div');
    const langData = getLocaleData();
    const common = langData.common || {};
    const wrapper = document.createElement('div');
    wrapper.className = `card-wrapper reveal-on-scroll theme-${groupId}`;
    
    const title = getLocalizedField(card.title) || 'TBD';
    const meaning = getLocalizedField(card.meaning) || 'TBD';
    const ecology = getLocalizedField(card.ecology) || 'TBD';

    const fallbackCommon = (window.siteData && (window.siteData.zh || window.siteData.en) || {}).common || {};
    const lM = common.label_tarot_meaning || fallbackCommon.label_tarot_meaning || 'Tarot Meaning';
    const lE = common.label_eco_connection || fallbackCommon.label_eco_connection || 'Eco-Connection';
    const formattedEcology = formatEcologyText(ecology);

    wrapper.innerHTML = `
        <div class="card" id="${card.id}">
            <div class="card-front" style="background: #111;">
                <img src="/art/renders/${card.id}.webp" alt="${title}" loading="lazy" style="width:100%; height:100%; object-fit:cover; display:block;">
            </div>
            <div class="card-back">
                <div class="back-content" tabindex="0" aria-label="${uiText('card_meaning_scroll_aria', `${title} meaning, scroll vertically`, {title})}">
                    <button class="card-flip-back" type="button" aria-label="${uiText('card_flip_back', 'Flip to card face')}">↩ ${uiText('card_flip_back', 'Flip to card face')}</button>
                    <h3>${title}</h3>
                    <div class="meaning-box"><span class="label">${lM}</span><p class="content-text">${meaning}</p></div>
                    <div class="ecology-box"><span class="label">${lE}</span><p class="content-text">${formattedEcology}</p></div>
                </div>
            </div>
        </div>
    `;
    const cardInner = wrapper.querySelector('.card');
    
    const scrollableContent = wrapper.querySelector('.back-content');
    bindCardInteractions(cardInner, scrollableContent);

    return wrapper;
}

function initScrollReveal() {
    if (!window.IntersectionObserver) return;
    revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target); 
            }
        });
    }, { threshold: 0.05 });
    document.querySelectorAll('.section, .reveal-on-scroll').forEach(el => {
        if (!el.closest('#share-card-container')) revealObserver.observe(el);
    });
}

// --- Fortune Logic ---
function appendBubble(role, text) {
    const historyDiv = document.getElementById('chat-history');
    if (!historyDiv) return null;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    // Remove individual quota badges to prevent confusion with global refill
    bubble.innerHTML = (role === 'assistant' ? text : text.replace(/\n/g, '<br>'));
    historyDiv.appendChild(bubble);
    historyDiv.scrollTop = historyDiv.scrollHeight;
    return bubble;
}

// 🖋️ Tag-safe Typewriter for HTML
function typeWriterHTML(element, html, speed = 20, onComplete) {
    let container = document.createElement('div');
    container.innerHTML = html;
    
    let nodes = [];
    function walk(node) {
        if (node.nodeType === 3) { // Text
            for (let char of node.nodeValue) {
                nodes.push({ type: 'char', value: char, parent: node.parentNode });
            }
        } else if (node.nodeType === 1) { // Element
            let clone = node.cloneNode(false);
            nodes.push({ type: 'tag-start', value: clone, parent: node.parentNode });
            for (let child of node.childNodes) walk(child);
            nodes.push({ type: 'tag-end' });
        }
    }
    for (let child of container.childNodes) walk(child);

    let i = 0;
    let currentTarget = element;
    let stack = [element];

    function step() {
        if (i < nodes.length) {
            let n = nodes[i++];
            if (n.type === 'char') {
                stack[stack.length - 1].innerHTML += n.value;
            } else if (n.type === 'tag-start') {
                let el = n.value;
                stack[stack.length - 1].appendChild(el);
                stack.push(el);
            } else if (n.type === 'tag-end') {
                stack.pop();
            }
            const historyDiv = document.getElementById('chat-history');
            if (historyDiv) historyDiv.scrollTop = historyDiv.scrollHeight;
            setTimeout(step, speed);
        } else if (onComplete) {
            onComplete();
        }
    }
    step();
}

// 📸 Share Image Generator
let lastShareFile = null;
let lastShareText = "";
let lastShareBaseMessage = "";
let lastShareUrl = "";
window.shareContentMode = 'quote';
window.shareIncludeQuestion = false;

function normalizeMasterShareText(value) {
    const raw = String(value || '');
    const holder = document.createElement('div');
    holder.innerHTML = raw;
    holder.querySelectorAll('.hidden-quote, [hidden], [aria-hidden="true"]').forEach(node => node.remove());
    holder.querySelectorAll('[style]').forEach(node => {
        const style = String(node.getAttribute('style') || '').replace(/\s+/g, '').toLowerCase();
        if (style.includes('display:none') || style.includes('visibility:hidden')) node.remove();
    });
    const plain = holder.textContent || holder.innerText || raw;
    return plain
        .replace(/^#{1,6}\s+/gm, '')
        .replace(/\*\*(.*?)\*\*/g, '$1')
        .replace(/__(.*?)__/g, '$1')
        .replace(/`([^`]+)`/g, '$1')
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1')
        .replace(/[ \t]+\n/g, '\n')
        .replace(/\n{3,}/g, '\n\n')
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

function latestMasterInterpretation() {
    for (let i = currentChatHistory.length - 1; i >= 0; i--) {
        const item = currentChatHistory[i];
        if (item?.role === 'assistant' && item.content) return normalizeMasterShareText(item.content);
    }
    return '';
}

function buildSocialShareText(shareMsg, shareUrl) {
    if (window.shareContentMode !== 'full') return `${shareMsg} ${shareUrl}`;
    const answer = latestMasterInterpretation();
    if (!answer) return `${shareMsg} ${shareUrl}`;
    const source = window.currentQuestionSource;
    const parts = [];
    if (source?.type === 'threads' && source.text && source.url) {
        parts.push(`${uiText('share_threads_question_heading', '該文作者提問：')}\n${normalizeMasterShareText(source.text)}`);
        parts.push(`${uiText('share_source_heading', '原文：')}\n${source.url}`);
        parts.push(`${uiText('share_master_heading', '大師解讀：')}\n${answer}`);
    } else {
        if (window.shareIncludeQuestion && window._lastQuestion) {
            parts.push(`${uiText('share_question_heading', '我的提問')}\n${normalizeMasterShareText(window._lastQuestion)}`);
        }
        parts.push(answer);
    }
    parts.push(shareUrl);
    return parts.join('\n\n');
}

function syncShareContentControls() {
    const host = document.getElementById('share-content-controls');
    if (host) host.dataset.shareContentMode = window.shareContentMode;
    document.querySelectorAll('[data-share-content-mode]').forEach(btn => {
        if (btn.matches('button')) btn.classList.toggle('active', btn.dataset.shareContentMode === window.shareContentMode);
    });
    const question = document.getElementById('share-include-question');
    if (question) question.checked = Boolean(window.shareIncludeQuestion);
}

const THREADS_TEXT_LIMIT = 500;

function splitThreadsText(text, limit = THREADS_TEXT_LIMIT) {
    const source = String(text || '').trim();
    if (!source) return [];
    if (source.length <= limit) return [source];
    const chunks = [];
    let rest = source;
    while (rest.length > limit) {
        const windowText = rest.slice(0, limit + 1);
        let cut = Math.max(
            windowText.lastIndexOf('\n\n', limit),
            windowText.lastIndexOf('\n', limit),
            windowText.lastIndexOf('。', limit),
            windowText.lastIndexOf('！', limit),
            windowText.lastIndexOf('？', limit),
            windowText.lastIndexOf('. ', limit),
            windowText.lastIndexOf('! ', limit),
            windowText.lastIndexOf('? ', limit),
            windowText.lastIndexOf(' ', limit)
        );
        if (cut < Math.floor(limit * 0.55)) cut = limit;
        else if ('。！？'.includes(rest[cut])) cut += 1;
        const chunk = rest.slice(0, cut).trim();
        if (!chunk) { cut = limit; }
        else chunks.push(chunk);
        rest = rest.slice(cut).trim();
    }
    if (rest) chunks.push(rest);
    return chunks;
}

function threadsSharePlan(text) {
    const chunks = splitThreadsText(text);
    return { text: String(text || '').trim(), chunks, count: chunks.length, requiresPaste: chunks.length > 1 };
}

window.prepareThreadsShare = async function(event) {
    const link = document.getElementById('share-threads');
    if (!link || !lastShareText) return true;
    const plan = threadsSharePlan(lastShareText);
    if (!plan.requiresPaste) return true;
    event?.preventDefault?.();
    try {
        await navigator.clipboard.writeText(plan.text);
    } catch (_) {
        return true;
    }
    const blankComposer = 'https://www.threads.net/intent/post';
    window.open(blankComposer, '_blank', 'noopener');
    const message = uiText(
        'threads_long_share_copied',
        '完整內容已複製。請在 Threads 貼上，Threads 會自動分成約 {count} 則串文。',
        {count: plan.count}
    );
    setTimeout(() => alert(message), 120);
    return false;
};

function refreshSocialShareText() {
    if (!lastShareUrl || !lastShareBaseMessage) return;
    const fullShareText = buildSocialShareText(lastShareBaseMessage, lastShareUrl);
    lastShareText = fullShareText;
    const lineLink = document.getElementById('share-line');
    if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(lastShareUrl)}&text=${encodeURIComponent(fullShareText)}`;
    const fbLink = document.getElementById('share-fb');
    if (fbLink) fbLink.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(lastShareUrl)}&quote=${encodeURIComponent(fullShareText)}`;
    const xLink = document.getElementById('share-x');
    if (xLink) xLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;
    const threadsLink = document.getElementById('share-threads');
    if (threadsLink) {
        const u = new URL(lastShareUrl);
        u.searchParams.set('preview', String(Date.now()));
        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;
        threadsLink.onclick = window.prepareThreadsShare;
    }
}

window.setShareContentMode = function(mode) {
    window.shareContentMode = mode === 'full' ? 'full' : 'quote';
    if (window.shareContentMode !== 'full') window.shareIncludeQuestion = false;
    syncShareContentControls();
    refreshSocialShareText();
};

window.setShareIncludeQuestion = function(include) {
    window.shareIncludeQuestion = window.shareContentMode === 'full' && Boolean(include);
    syncShareContentControls();
    refreshSocialShareText();
};

window.prepareFacebookShare = async function() {
    if (window.shareContentMode !== 'full' || !lastShareText) return;
    try { await navigator.clipboard?.writeText(lastShareText); } catch (_) {}
};

function getShareCardTitle(card, lang = window.currentLang) {
    if (!card) return '';
    return card.title?.[lang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id || '';
}

function getShareCardImage(card, deckId = window.activeDeckId || 'leopardcat') {
    if (!card) return '';
    return card.image || card.main_image || card.output || (deckId === 'leopardcat' && card.id ? `art/renders/${card.id}.webp` : '');
}

async function resolveShareCardsFromDeck() {
    const state = window.currentReadingState || {};
    const deckId = state.deck_id || window.activeDeckId || 'leopardcat';
    let deck = null;
    try {
        const response = await fetch(`/api/v1/decks/${encodeURIComponent(deckId)}`, { cache: 'no-cache' });
        if (response.ok) deck = await response.json();
    } catch (error) {
        console.warn('[Share] deck snapshot unavailable, using loaded deck data', error);
    }
    const deckCards = Array.isArray(deck?.cards) && deck.cards.length ? deck.cards : (Array.isArray(window.cardData) ? window.cardData : []);
    const specs = Array.isArray(state.cards) && state.cards.length
        ? state.cards
        : [{ card_id: state.card_id || currentDrawnCard?.id, orientation: state.orientation || 'upright' }];
    const cards = specs.map((spec, index) => {
        const id = spec.card_id || spec.id;
        const card = deckCards.find(item => item.id === id) || (index === 0 ? currentDrawnCard : null) || spec;
        return {
            card,
            card_id: id || card?.id,
            orientation: spec.orientation || 'upright',
            position: spec.position || '',
            position_label: spec.position_label || ''
        };
    }).filter(item => item.card && getShareCardImage(item.card, deckId));
    if (!cards.length && currentDrawnCard) {
        cards.push({ card: currentDrawnCard, card_id: currentDrawnCard.id, orientation: state.orientation || 'upright', position: '', position_label: '' });
    }
    return { deck: deck || { deck_id: deckId, name: window.activeBrand?.app_name || deckId, cards: deckCards }, deckId, cards };
}

function renderShareCards(frame, shareContext) {
    const entries = shareContext.cards;
    frame.classList.toggle('share-three-card', entries.length > 1);
    frame.innerHTML = '';
    entries.forEach((entry, index) => {
        const slot = document.createElement('div');
        slot.className = 'share-card-slot';
        const img = document.createElement('img');
        if (index === 0) img.id = 'share-card-img'; // compatibility for older selectors/tests
        img.className = 'share-card-image';
        img.src = getShareCardImage(entry.card, shareContext.deckId);
        img.alt = getShareCardTitle(entry.card);
        img.style.transform = entry.orientation === 'reversed' ? 'rotate(180deg)' : '';
        slot.appendChild(img);
        const caption = document.createElement('div');
        caption.className = 'share-card-caption';
        const position = entry.position_label || entry.position;
        const orientation = entry.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        caption.textContent = `${position ? position + ' · ' : ''}${getShareCardTitle(entry.card)} · ${orientation}`;
        slot.appendChild(caption);
        frame.appendChild(slot);
    });
}


function readThemeToken(name, fallback) {
    try {
        const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
        return value || fallback;
    } catch (_) {
        return fallback;
    }
}

function normalizeShareTheme(shareContext) {
    const deck = shareContext?.deck || {};
    const deckId = shareContext?.deckId || deck.deck_id || window.activeDeckId || 'leopardcat';
    const explicit = (deck.share_theme && typeof deck.share_theme === 'object') ? deck.share_theme : {};
    const hasExplicit = Object.keys(explicit).length > 0;
    const hasDeckTheme = Boolean(deck.default_theme || deck.theme_id || window.currentReadingState?.theme_id || window.activeThemeId);
    const isLeopardCat = deckId === 'leopardcat';
    const neutral = {
        background: '#171717', surface: 'rgba(255,255,255,.055)', accent: '#d7d2c8',
        text: '#f5f2ec', muted: 'rgba(245,242,236,.74)', line: 'rgba(215,210,200,.28)'
    };
    const themed = {
        background: readThemeToken('--color-bg', '#0a110e'),
        surface: readThemeToken('--color-card-bg', 'rgba(212,175,55,.05)'),
        accent: readThemeToken('--color-gold', '#d4af37'),
        text: readThemeToken('--color-text', '#ffffff'),
        muted: readThemeToken('--color-text-muted', 'rgba(244,241,234,.82)'),
        line: readThemeToken('--color-gold-glow', 'rgba(212,175,55,.28)')
    };
    const base = (isLeopardCat || hasDeckTheme) ? themed : neutral;
    const title = String(explicit.title || deck.name || (isLeopardCat ? window.brandText('share_title', '靈山靈貓 · 石虎塔羅') : 'Tarot Reading'));
    const siteTag = String(explicit.site_tag || (isLeopardCat ? window.brandText('share_site_tag', location.host) : location.host));
    return {
        source: hasExplicit ? 'deck' : ((isLeopardCat || hasDeckTheme) ? 'theme-derived' : 'neutral'),
        layout: String(explicit.layout || (isLeopardCat ? 'spirit-memo' : 'deck-memo')),
        title, site_tag: siteTag,
        background: String(explicit.background || base.background),
        surface: String(explicit.surface || base.surface),
        accent: String(explicit.accent || base.accent),
        text: String(explicit.text || base.text),
        muted: String(explicit.muted || base.muted),
        line: String(explicit.line || base.line)
    };
}

function applyShareTheme(template, shareContext) {
    const theme = normalizeShareTheme(shareContext);
    template.dataset.shareThemeSource = theme.source;
    template.dataset.shareLayout = theme.layout;
    template.style.setProperty('--share-bg', theme.background);
    template.style.setProperty('--share-surface', theme.surface);
    template.style.setProperty('--share-accent', theme.accent);
    template.style.setProperty('--share-text', theme.text);
    template.style.setProperty('--share-muted', theme.muted);
    template.style.setProperty('--share-line', theme.line);
    const memo = template.querySelector('#share-memo-title');
    const site = template.querySelector('#share-site-tag');
    if (memo) memo.textContent = theme.title;
    if (site) site.textContent = theme.site_tag;
    return theme;
}

async function persistReadingSharePreview(blob) {
    const envelope = window.currentReadingEnvelope;
    if (!blob || !envelope?.reading_id || !envelope?.session_token) return false;
    try {
        const image = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
        const response = await fetch(`/api/v1/readings/${encodeURIComponent(envelope.reading_id)}/share-image`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({session_token: envelope.session_token, image})
        });
        if (!response.ok) throw new Error(`share preview persist ${response.status}`);
        return true;
    } catch (error) {
        console.warn('[Share] OG preview persistence unavailable', error);
        return false;
    }
}

// 📸 Share Image Generator
window.generateShareImage = async function() {
    if (!currentDrawnCard) return;
    
    const btn = document.getElementById('btn-share-image');
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    // ⚡ Optimization: If we already generated this card's memo, just share it
    if (lastShareFile && isMobile && navigator.share) {
        try {
            await navigator.share({ title: window.brandText('share_title', 'Tarot Reading'), text: lastShareText, files: [lastShareFile] });
            return;
        } catch(e) { console.log("Re-share failed", e); }
    }

    const originalText = btn.innerText;
    btn.innerText = uiText('share_gathering', '🪄 Gathering Mana...');
    btn.disabled = true;

    const template = document.getElementById('share-card-template');
    
    // Deck-driven share composition: resolve this reading against the authoritative active deck.
    const shareState = window.currentReadingState || {};
    const shareContext = await resolveShareCardsFromDeck();
    const shareEntries = shareContext.cards;
    if (!shareEntries.length) throw new Error('SHARE_CARDS_NOT_FOUND');
    const shareFrame = template.querySelector('.share-card-frame');
    renderShareCards(shareFrame, shareContext);
    const shareTheme = applyShareTheme(template, shareContext);
    const titleParts = shareEntries.map(entry => getShareCardTitle(entry.card));
    if (shareEntries.length === 1) {
        const entry = shareEntries[0];
        const titleZh = entry.card.title?.zh || entry.card.title?.['zh-TW'] || entry.card.title?.en || entry.card_id;
        const titleEn = entry.card.title?.en || titleZh;
        const orientationLabel = entry.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        document.getElementById('share-card-title').innerText = `【${titleZh} / ${titleEn}】 · ${orientationLabel}`;
    } else {
        document.getElementById('share-card-title').innerText = `【${uiText('spread_three_short', 'Three Cards')}】 ${titleParts.join(' · ')}`;
    }
    document.getElementById('share-seeker-name').innerText = localStorage.getItem('userDharmaName') || 'Seeker';
    document.getElementById('share-date').innerText = new Date().toLocaleDateString();
    
    // 🔱 Extract Pre-selected "Golden Quote" from Hidden Div
    const historyDiv = document.getElementById('chat-history');
    const bubbles = Array.from(historyDiv.querySelectorAll('.chat-bubble.assistant'));
    const lastBubble = bubbles[bubbles.length - 1];
    
    let bestQuote = '';
    if (lastBubble) {
        const hiddenDiv = lastBubble.querySelector('.hidden-quote');
        if (hiddenDiv) {
            bestQuote = hiddenDiv.innerText.replace(/[\[\]]/g, '').trim();
        }
    }
    
    // Fallback to heuristic if hidden quote is missing (e.g. old session)
    if (!bestQuote) {
        for (const b of bubbles) {
            const text = b.innerText;
            const sentences = text.split(/[。！？.!?\n]/).filter(s => {
                const ts = s.trim();
                return ts.length > 15 && !ts.includes('旅人') && !ts.includes('來到');
            });
            if (sentences.length > 0) {
                bestQuote = sentences[sentences.length - 1].trim(); // Try last sentence as insight
                break;
            }
        }
    }
    
    if (!bestQuote && bubbles.length > 0) bestQuote = bubbles[0].innerText.substring(0, 60) + '...';
    const quote = bestQuote || window.brandText('default_quote', uiText('default_quote', 'Listen to the cards, and to yourself.'));
    document.getElementById('share-quote').innerText = quote;

    // 🕵️ Stability: wait for every card face in the spread, not only the first card.
    const shareCardImages = Array.from(template.querySelectorAll('.share-card-frame img'));
    await Promise.race([
        Promise.all(shareCardImages.map(img => new Promise(resolve => {
            if (img.complete) resolve();
            else {
                img.onload = resolve;
                img.onerror = resolve; // Don't hang; html2canvas still renders the remaining deck faces.
            }
        }))),
        new Promise(resolve => setTimeout(resolve, 5000))
    ]);
    await new Promise(resolve => setTimeout(resolve, 300)); // Layout settling delay

    console.time('ManaGathering');
    try {
        const canvas = await Promise.race([
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
        ]);
        console.timeEnd('ManaGathering');
        
        // 🕵️ Smart Language Detection for Share Message
        // If the quote has Chinese characters, use 'zh' template even if UI is 'en'
        const hasChinese = /[\u4e00-\u9fa5]/.test(bestQuote);
        const shareLang = hasChinese ? 'zh' : window.currentLang;
        const common = window.siteData[shareLang].common;

        // 🔗 Update Share Card Labels (Always follows UI Language for frame consistency)
        const uiCommon = window.siteData[window.currentLang].common;
        applyShareTheme(template, shareContext); // locale refresh must not restore LeopardCat branding.
        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;
        document.getElementById('share-date').innerText = new Date().toLocaleDateString(getAILanguageTag());

        const shareCardText = shareEntries.map(entry => {
            const title = getShareCardTitle(entry.card, shareLang);
            const reversed = entry.orientation === 'reversed' ? (shareLang === 'zh' ? '（逆位）' : ' (Reversed)') : '';
            return `${title}${reversed}`;
        }).join(shareLang === 'zh' ? '、' : ', ');
        const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);
        const shareMsg = brandTemplate.replace('{card}', shareCardText);
        // Reading-based deep link: deck/theme load the experience; immutable cards come from the read-only reading receipt.
        const shareU = new URL(window.location.origin + window.location.pathname);
        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);
        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);
        if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);
        const envelope = window.currentShareReceipt || window.currentReadingEnvelope;
        if (envelope?.reading_id && envelope?.share_token) {
            shareU.searchParams.set('reading', envelope.reading_id);
            shareU.searchParams.set('share', envelope.share_token);
        }
        applySingleCardShareFallback(shareU);
        const shareUrl = shareU.toString();
        
        lastShareBaseMessage = shareMsg;
        lastShareUrl = shareUrl;
        const fullShareText = buildSocialShareText(shareMsg, shareUrl);
        lastShareText = fullShareText;

        const lineLink = document.getElementById('share-line');
        if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(fullShareText)}`;
        
        const fbRefresh = Date.now();
        const fbUrlSeparator = shareUrl.includes('?') ? '&' : '?';
        const fbShareUrl = `${shareUrl}${fbUrlSeparator}fbrefresh=${fbRefresh}`;
        document.getElementById('share-fb').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(fbShareUrl)}&quote=${encodeURIComponent(fullShareText)}`;
        
        // 🐦 X (Twitter) unified format for best compatibility
        document.getElementById('share-x').href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;
        const threadsShareU = new URL(shareUrl);
        threadsShareU.searchParams.set('preview', String(Date.now()));
        const threadsShareText = buildSocialShareText(shareMsg, threadsShareU.toString());
        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;
        document.getElementById('share-threads').onclick = window.prepareThreadsShare;
        
        document.getElementById('social-share-row').classList.remove('hidden');

        // 🔗 Sync Metadata immediately
        updateSocialLinks(currentDrawnCard, bestQuote);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));

        // Social crawlers need a landscape Open Graph asset. Keep the downloadable/native
        // share memo square, but reflow the same deck-owned content into 1200x630 for OG.
        let ogBlob = blob;
        template.classList.add('share-og-mode');
        try {
            const ogCanvas = await html2canvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: shareTheme.background,
                scale: 1.0,
                width: 1200,
                height: 630,
                imageTimeout: 5000,
                removeContainer: true
            });
            const renderedOgBlob = await new Promise(resolve => ogCanvas.toBlob(resolve, 'image/png'));
            if (renderedOgBlob) ogBlob = renderedOgBlob;
        } finally {
            template.classList.remove('share-og-mode');
        }
        await persistReadingSharePreview(ogBlob); // OG receives the landscape asset; private text is still excluded.
        const filePrefix = window.activeBrand?.file_prefix || 'tarot';
        const file = new File([blob], `${filePrefix}-${Date.now()}.png`, { type: 'image/png' });
        
        // 🎨 Ritual Result: Native Share (Mobile) or Clipboard Copy (Desktop)
        if (navigator.share && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent)) {
            btn.disabled = false;
            btn.innerHTML = originalText;
            try {
                await navigator.share({
                    files: [file],
                    title: window.brandText('share_title', window.siteData[window.currentLang].common.share_memo_title),
                    text: lastShareText
                });
            } catch (shareErr) {
                if (shareErr.name !== 'AbortError') console.error("Share Failed:", shareErr);
            }
        } else {
            // 🖱️ Desktop Savior: Attempt Clipboard Image Copy
            try {
                if (window.ClipboardItem) {
                    const item = new ClipboardItem({ "image/png": blob });
                    await navigator.clipboard.write([item]);
                    btn.disabled = false;
                    btn.innerHTML = originalText;
                    // Simplified sharing, no alert needed.
                } else {
                    throw new Error("ClipboardItem not supported");
                }
            } catch (err) {
                console.warn("Clipboard Copy Failed:", err);
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `${window.activeBrand?.file_prefix || 'tarot'}-${Date.now()}.png`;
                link.click();
                btn.disabled = false;
                btn.innerHTML = originalText;
                alert(uiText('share_downloaded_manual', '✨ Spirit Memo downloaded!\nPlease upload it manually to share.'));
            }
        }
    } catch (error) {
        console.error('Spirit Rendering Error:', error);
        alert(`[RENDER_ERR] ${error.message}`);
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function updateSocialLinks(card, customQuote = null) {
    if (!card) return;
    const shareLang = window.currentLang;
    const common = window.siteData[shareLang].common;
    
    // Use quote if provided, else generic template
    const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);
    const cardTitle = card.title?.[shareLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id;
    const shareMsg = customQuote ? `「${customQuote}」` : brandTemplate.replace('{card}', cardTitle);
    const shareU = new URL(`${window.location.origin}${window.location.pathname}`);
    if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);
    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);
    if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);
    const envelope = window.currentShareReceipt || window.currentReadingEnvelope;
    if (envelope?.reading_id && envelope?.share_token) {
        shareU.searchParams.set('reading', envelope.reading_id);
        shareU.searchParams.set('share', envelope.share_token);
    }
    applySingleCardShareFallback(shareU);
    const shareUrl = shareU.toString();
    window.shareUrl = shareUrl; // Store for the copy button
    
    // Update button text to encourage the next step
    const shareBtn = document.getElementById('btn-share-image');
    if (shareBtn) {
        shareBtn.innerHTML = uiText('share_clipboard_saved', '✨ Spirit memo copied');
        setTimeout(() => {
            shareBtn.innerHTML = uiText('share_generate_again', 'Generate share card again');
        }, 5000);
    }
    lastShareBaseMessage = shareMsg;
    lastShareUrl = shareUrl;
    const fullShareText = buildSocialShareText(shareMsg, shareUrl);
    
    lastShareText = fullShareText;

    const lineLink = document.getElementById('share-line');
    if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(fullShareText)}`;
    
    const fbLink = document.getElementById('share-fb');
    if (fbLink) fbLink.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(fullShareText)}`;
    
    const xLink = document.getElementById('share-x');
    if (xLink) xLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;
    
    const threadsLink = document.getElementById('share-threads');
    if (threadsLink) {
        const threadsShareU = new URL(shareUrl);
        threadsShareU.searchParams.set('preview', String(Date.now()));
        const threadsShareText = buildSocialShareText(shareMsg, threadsShareU.toString());
        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;
    }
    
    document.getElementById('social-share-row')?.classList.remove('hidden');
}

function modularErrorMessage(e) {
    if (e?.code === 'provider_429_billing_or_quota_state' || e?.status === 429) {
        return uiText('provider_429_error', 'Gemini is currently reporting a provider quota or billing-state issue. Your draw is preserved for retry.');
    }
    if (e?.code === 'free_quota_exhausted') {
        return uiText('err_free_ai_unavailable', 'Free AI capacity is currently unavailable. Your draw is preserved for retry.');
    }
    if (e?.status === 503 || e?.name === 'AbortError') {
        return uiText('err_master_unavailable', 'The Master is temporarily unavailable. Your draw is preserved and will not be redrawn.');
    }
    return e?.message || uiText('err_reading_unavailable', 'Unable to complete the reading right now.');
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
    errBubble.dataset.errorCode = error?.code || '';
    errBubble.dataset.errorStatus = String(error?.status || '');
    const text = document.createElement('p');
    text.className = 'modular-error-text';
    text.style.color = 'var(--color-gold)';
    text.textContent = modularErrorMessage(error);
    const btn = document.createElement('button');
    btn.className = 'retry-btn';
    btn.textContent = uiText('retry', 'Retry');
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
            await window.getModularReading(q, window.pendingDrawOptions || {});
        } catch (e) {
            refundLocalMana();
            showModularRetry(q, e);
        }
    });
    errBubble.append(text, btn);
}

async function performReading(q, drawIndices = null, seed = null) {
    const common = window.siteData[window.currentLang].common;
    if (!q.trim()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_empty_question);
    }
    try {
        const resolvedInput = await resolveQuestionInput(q);
        q = resolvedInput.question;
        window.currentQuestionSource = resolvedInput.source;
        window.currentQuestionLanguage = getQuestionLanguageTag(q);
    } catch (error) {
        console.warn('[Threads source] unable to resolve public post', error);
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(uiText('err_threads_source_unavailable', '無法讀取這則 Threads 公開貼文，請確認網址與公開狀態後再試。'));
    }
    const debug = q.toUpperCase() === 'DEBUG' || q.toUpperCase() === 'FORCE_DEBUG';
    if (!debug && !chargeLocalMana()) {
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        return alert(common.err_mana_depleted);
    }

    document.querySelectorAll('.modular-retry-bubble').forEach(el => el.remove());
    document.getElementById('fortune-ritual-area').classList.add('hidden');
    document.getElementById('fortune-chat-area').classList.remove('hidden');
    appendBubble('user', q);
    window.pendingDrawOptions = Array.isArray(drawIndices) ? {drawIndices: drawIndices.slice(), seed} : {};
    try {
        await window.getModularReading(q, window.pendingDrawOptions);
    } catch (e) {
        console.warn('[Divination v1] modular reading unavailable; preserving the same reading for retry:', e);
        if (!debug) refundLocalMana();
        if (window.drawMode === 'manual') window.manualDrawState.submitting = false;
        showModularRetry(q, e);
    }
}

window.drawFortune = async function() {
    if (window.drawMode === 'manual') return window.shuffleManualDeck();
    const q = document.getElementById('fortune-question').value;
    return performReading(q);
};

window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';
window.activePersonaId = new URLSearchParams(window.location.search).get('persona') || null;
window.defaultPersonaId = null;

window.updatePrimaryReadingLinks = function() {
    // Tarot's primary experience stays inside the active deck page. The focused
    // /read.html surface remains available for other methods or explicit entry,
    // but “開始占卜／詢問大師” must not feel like leaving the deck's website.
    document.querySelectorAll('[data-primary-reading]').forEach(el => {
        el.setAttribute('href', '#fortune');
    });
};
document.addEventListener('DOMContentLoaded', window.updatePrimaryReadingLinks);


window.brandText = function(field, fallback = '') {
    const value = window.activeBrand?.[field];
    if (value && typeof value === 'object') return value[window.currentLang] || value.zh || value.en || fallback;
    return value || fallback;
};

window.applyActiveBrand = function() {
    const b = window.activeBrand;
    if (!b || window.activeDeckId === 'leopardcat') return;
    document.title = b.app_name || b.short_name || 'Tarot';
    const setText = (selector, text) => {
        const el = document.querySelector(selector);
        if (!el || !text) return;
        el.removeAttribute('data-i18n');
        el.textContent = text;
    };
    setText('.nav-logo', b.short_name || b.app_name);
    setText('#hero h1', b.app_name);
    setText('#hero .subtitle', b.description || b.creator_line);
    setText('#fortune .section-title h2', uiText('brand_fortune_template', '{name} · Tarot Reading', {name: b.short_name || b.app_name}));
    setText('#fortune .section-title .label', b.creator_line || uiText('creator_tarot', 'Creator Tarot'));
    setText('#share-memo-title', window.brandText('share_title', b.app_name));
    setText('#share-site-tag', window.brandText('share_site_tag', b.creator_line || ''));
};

window.loadActiveBrand = async function() {
    try {
        const r = await fetch(`/api/v1/brands/${encodeURIComponent(window.activeDeckId || 'leopardcat')}`, {cache:'no-cache'});
        if (!r.ok) throw new Error(`BRAND_${r.status}`);
        window.activeBrand = await r.json();
        window.applyActiveBrand();
    } catch (e) {
        console.warn('[Brand Pack] load failed', e);
        window.activeBrand = {
            brand_id: `fallback:${window.activeDeckId || 'leopardcat'}`,
            app_name: window.activeDeckId || 'Tarot', short_name: window.activeDeckId || 'Tarot',
            share_title: {zh:'塔羅指引', en:'Tarot Reading'},
            share_site_tag: {zh:'線上塔羅', en:'Online Tarot'},
            share_copy_template: {zh:'我抽到了：{card}', en:'I drew {card}'},
            default_quote: {zh:'聽見牌面，也聽見自己。', en:'Listen to the cards, and to yourself.'},
            file_prefix: window.activeDeckId || 'tarot'
        };
    }
};



window.initPersonaSwitcher = async function() {
    try {
        const r = await fetch(`/api/v1/personas?deck=${encodeURIComponent(window.activeDeckId)}`, {cache:'no-cache'});
        if (!r.ok) throw new Error(`PERSONAS_${r.status}`);
        const data = await r.json();
        window.defaultPersonaId = data.default_persona || 'master';
        if (!window.activePersonaId) window.activePersonaId = window.defaultPersonaId;

        const box = document.createElement('div');
        box.id = 'persona-switcher';
        box.style.cssText = 'position:fixed;right:12px;bottom:58px;z-index:1200;background:#111c;border:1px solid #ffffff22;border-radius:999px;padding:6px 10px;backdrop-filter:blur(8px);font-size:12px';
        box.innerHTML = `<label style="display:flex;gap:6px;align-items:center">${uiText('persona_label', 'Reader')} <select id="persona-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>`;
        document.body.appendChild(box);
        const sel = box.querySelector('select');
        for (const p of data.personas || []) {
            const o = document.createElement('option');
            o.value = p.persona_id;
            o.textContent = p.name || p.persona_id;
            sel.appendChild(o);
        }
        if (![...sel.options].some(o => o.value === window.activePersonaId)) window.activePersonaId = window.defaultPersonaId;
        sel.value = window.activePersonaId;
        sel.addEventListener('change', () => {
            window.activePersonaId = sel.value;
            const u = new URL(location.href);
            if (window.activePersonaId === window.defaultPersonaId) u.searchParams.delete('persona');
            else u.searchParams.set('persona', window.activePersonaId);
            history.replaceState(null, '', u);
        });
    } catch (e) {
        console.warn('[Persona Pack] load failed', e);
    }
};

document.addEventListener('DOMContentLoaded', () => window.initPersonaSwitcher());

window.explicitThemeId = new URLSearchParams(window.location.search).get('theme');
window.activeThemeId = window.explicitThemeId || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');

window.applyTheme = async function(themeId, updateUrl = false) {
    try {
        const resp = await fetch(`/api/v1/themes/${encodeURIComponent(themeId)}`, {cache:'no-cache'});
        if (!resp.ok) throw new Error(`THEME_${resp.status}`);
        const t = await resp.json();
        const c = t.colors || {};
        const root = document.documentElement;
        root.style.setProperty('--theme-background', c.background || '#030504');
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
        if (t.background_image) {
            document.body.style.backgroundImage = `linear-gradient(#0006,#0006),url("${t.background_image}")`;
            document.body.style.backgroundSize = 'cover'; document.body.style.backgroundAttachment = 'fixed';
        } else document.body.style.backgroundImage = '';
        window.activeThemeId = t.theme_id;
        if (updateUrl) { const u = new URL(location.href); u.searchParams.set('theme', t.theme_id); history.replaceState(null,'',u); }
        const sel = document.getElementById('theme-switcher-select'); if (sel) sel.value = t.theme_id;
    } catch (e) { console.warn('Theme load failed', e); }
};

window.initThemeSwitcher = async function() {
    const box = document.createElement('div');
    box.id = 'theme-switcher';
    box.style.cssText = 'position:fixed;right:12px;bottom:12px;z-index:1200;background:#111c;border:1px solid #ffffff22;border-radius:999px;padding:6px 10px;backdrop-filter:blur(8px);font-size:12px';
    box.innerHTML = `<label style="display:flex;gap:6px;align-items:center">${uiText('theme_label', 'Theme')} <select id="theme-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>`;
    document.body.appendChild(box);
    const sel = box.querySelector('select');
    try {
        const r = await fetch('/api/v1/themes'); const d = await r.json();
        for (const t of d.themes || []) { const o=document.createElement('option'); o.value=t.theme_id; o.textContent=t.name; sel.appendChild(o); }
        if (![...sel.options].some(o=>o.value===window.activeThemeId)) { const o=document.createElement('option'); o.value=window.activeThemeId; o.textContent=uiText('custom_theme_label', 'Custom deck theme'); sel.appendChild(o); }
        sel.value = window.activeThemeId; sel.addEventListener('change', ()=>window.applyTheme(sel.value,true));
    } catch (_) {}
    await window.applyTheme(window.activeThemeId);
};

document.addEventListener('DOMContentLoaded', () => window.initThemeSwitcher());

window.getModularReading = async function(q, drawOptions = {}) {
    const common = window.siteData[window.currentLang].common;
    const historyDiv = document.getElementById('chat-history');
    const sensingId = 'sensing-' + Date.now();
    appendBubble('assistant', `<div id="${sensingId}" class="spirit-thinking">${common.msg_sensing}</div>`);
    const removeSensing = () => {
        const el = document.getElementById(sensingId);
        el?.closest('.chat-bubble')?.remove();
    };
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);
    let resp;
    try {
        const pending = window.pendingReadingSession;
        const requestBody = pending ? {
            readingId: pending.reading_id,
            sessionToken: pending.session_token,
            question: q,
            lang: getQuestionLanguageTag(q)
        } : {
            method: 'tarot', persona: window.activePersonaId || undefined, question: q,
            input: {
                spread: resolvedSpreadForQuestion(q),
                deck_id: window.activeDeckId,
                ...(Array.isArray(drawOptions.drawIndices) ? {draw_indices: drawOptions.drawIndices} : {})
            },
            ...(drawOptions.seed ? {seed: drawOptions.seed} : {}),
            lang: getQuestionLanguageTag(q)
        };
        resp = await fetch('/api/v1/readings', {
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
    window.pendingDrawOptions = null;
    window.activePersonaId = data.persona || window.activePersonaId || window.defaultPersonaId;
    removeSensing();
    const specs = data.method_result?.cards || [];
    if (!specs.length) throw new Error('DIVINATION_V1_EMPTY_RESULT');
    const resolved = specs.map(spec => ({spec, card: window.cardData.find(c => c.id === spec.card_id) || spec})).filter(x => x.card);
    if (!resolved.length) throw new Error('DIVINATION_V1_CARD_NOT_FOUND');
    currentDrawnCard = resolved[0].card;
    window.currentDrawnCard = currentDrawnCard;
    window.currentReadingEnvelope = data;
    window.currentShareReceipt = data?.reading_id ? {reading_id: data.reading_id, share_token: data.share_token || null} : null;
    window.currentReadingState = {
        deck_id: window.activeDeckId,
        theme_id: window.activeThemeId,
        persona_id: window.activePersonaId,
        card_id: resolved[0].spec.card_id || currentDrawnCard.id,
        orientation: resolved[0].spec.orientation || 'upright',
        spread: data.method_result?.spread || 'single',
        draw_mode: data.method_result?.rules?.draw_mode || 'auto',
        draw_indices: data.method_result?.rules?.draw_indices || [],
        cards: resolved.map(({spec, card}) => ({ card_id: spec.card_id || card.id, orientation: spec.orientation || 'upright', draw_index: spec.draw_index, position: spec.position, position_label: spec.position_label }))
    };
    window._lastQuestion = q;
    saveReadingSnapshot(data, q);
    const pinnedArea = document.getElementById('pinned-card-area');
    const pinnedDisplay = document.getElementById('pinned-card-display');
    if (pinnedArea && pinnedDisplay) {
        pinnedArea.classList.remove('hidden');
        pinnedDisplay.innerHTML = `<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">${resolved.map(({spec, card}) => {
            const orientation = spec.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
            const pos = spec.position_label || spec.position || '';
            const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id;
            const rotate = spec.orientation === 'reversed' ? 'transform:rotate(180deg);' : '';
            const imageSrc = card.image || `art/renders/${card.id}.webp`; return `<div class="pinned-card-content" style="max-width:150px;"><img src="${imageSrc}" class="pinned-card-img" style="${rotate}"><div class="pinned-card-title">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;
        }).join('')}</div>`;
    }
    const spreadNames = {
        single: uiText('spread_single', 'Single Guidance'),
        three_card: uiText('spread_three', 'Three-card Timeline'),
        decision: uiText('spread_decision', 'Decision Spread')
    };
    const spread = data.method_result?.spread || 'single';
    const summary = resolved.map(({spec, card}) => {
        const orientation = spec.orientation === 'reversed' ? uiText('orientation_reversed', 'Reversed') : uiText('orientation_upright', 'Upright');
        const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id; return `${spec.position_label || spec.position}: ${title}（${orientation}）`;
    }).join(' / ');
    const prefix = `${uiText('master_opens', 'The Master opens')} <strong>【${spreadNames[spread] || spread}】</strong><br><small>${summary}</small><br>`;
    const bubble = appendBubble('assistant', prefix);
    const textContainer = document.createElement('div');
    textContainer.className = 'markdown-content';
    bubble.appendChild(textContainer);
    const rawReply = data.reading || '';
    const htmlReply = typeof marked !== 'undefined' ? marked.parse(rawReply) : rawReply.replace(/\n/g, '<br>');
    typeWriterHTML(textContainer, htmlReply, 35, () => {
        currentChatHistory.push({role:'user', content:q}, {role:'assistant', content:rawReply});
        saveReadingSnapshot(data, q);
        updateTempleStats();
        const actions = document.getElementById('fortune-actions');
        actions.classList.remove('hidden');
        setTimeout(() => actions.scrollIntoView({ behavior: 'smooth', block: 'center' }), 300);
    });
    historyDiv.scrollTop = historyDiv.scrollHeight;
};

window.getAIReading = async function(q, card) {
    const common = window.siteData[window.currentLang].common;
    const historyDiv = document.getElementById('chat-history');
    if (!historyDiv || !card) return;

    // Store for retry
    window.currentDrawnCard = card;
    window._lastQuestion = q;

    const sensingId = 'sensing-' + Date.now();
    appendBubble('assistant', `<div id="${sensingId}" class="spirit-thinking">${common.msg_sensing}</div>`);
    historyDiv.scrollTop = historyDiv.scrollHeight;

    // 30-second timeout via AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);

    const removeSensing = () => {
        const el = document.getElementById(sensingId);
        if (el && el.closest('.chat-bubble')) el.closest('.chat-bubble').remove();
    };

    const showRetry = () => {
        const errText = uiText('legacy_retry_error', 'Connection lost, mana insufficient...');
        const btnText = uiText('retry', 'Retry');
        const errBubble = appendBubble('assistant', `<p style="color:var(--color-gold)">${errText}</p>`);
        if (!errBubble) return;
        
        const btn = document.createElement('button');
        btn.className = 'retry-btn';
        btn.textContent = btnText;
        btn.style.display = 'block';
        btn.style.margin = '10px auto 0';
        btn.addEventListener('click', () => {
            errBubble.remove();
            window.getAIReading(window._lastQuestion, window.currentDrawnCard);
        });
        errBubble.appendChild(btn);
    };

    // 🛡️ Internal Retry Logic
    let attempts = 0;
    const maxAttempts = 3;
    let success = false;
    let data = null;

    while (attempts < maxAttempts && !success) {
        attempts++;
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            
            const apiResp = await fetch('/api/fortune', {
                method: 'POST',
                signal: controller.signal,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question: q,
                    cardTitle: getLocalizedField(card.title),
                    cardMeaning: getLocalizedField(card.meaning),
                    lang: getQuestionLanguageTag(q),
                    history: currentChatHistory
                })
            });
            clearTimeout(timeoutId);

            if (!apiResp.ok) throw new Error('API_ERROR');
            data = await apiResp.json();
            success = true;
        } catch (e) {
            console.warn(`Divination Attempt ${attempts} failed:`, e);
            if (attempts < maxAttempts) {
                // Wait 1.5s before retry
                await new Promise(r => setTimeout(r, 1500));
            } else {
                removeSensing();
                showRetry();
                return;
            }
        }
    }

    removeSensing();
    const rawReply = data.reading || getLocalizedField(card.meaning);
        
        // Render Markdown to HTML
        const htmlReply = typeof marked !== 'undefined' ? marked.parse(rawReply) : rawReply.replace(/\n/g, '<br>');

        // 🎯 Update Pinned Card Display
        const pinnedArea = document.getElementById('pinned-card-area');
        const pinnedDisplay = document.getElementById('pinned-card-display');
        if (pinnedArea && pinnedDisplay) {
            pinnedArea.classList.remove('hidden');
            pinnedDisplay.innerHTML = `
                <div class="pinned-card-content">
                    <img src="art/renders/${card.id}.webp" class="pinned-card-img">
                    <div class="pinned-card-title">【${getLocalizedField(card.title)}】</div>
                </div>
            `;
        }

        const prefix = `${common.msg_draw_prefix} <strong>【${getLocalizedField(card.title)}】</strong>。<br>`;
        const bubble = appendBubble('assistant', prefix);
        const textContainer = document.createElement('div');
        textContainer.className = 'markdown-content';
        bubble.appendChild(textContainer);

        typeWriterHTML(textContainer, htmlReply, 50, () => {
            currentChatHistory.push({role:'user',content:q},{role:'assistant',content:rawReply});
            // ⚡ Real-time update stats
            updateTempleStats();
            // ⚡ Show share and reset buttons
            const actions = document.getElementById('fortune-actions');
            actions.classList.remove('hidden');
            setTimeout(() => {
                actions.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }, 300);
        });

};

window.sendChatMessage = async function() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || chatQuota <= 0) return;

    const btn = document.querySelector('#fortune-chat-area .btn-gold');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = uiText('seeking', 'Seeking...');

    input.value = '';
    appendBubble('user', text);
    if (text.toUpperCase() !== 'DEBUG' && text.toUpperCase() !== 'FORCE_DEBUG') {
        if (chatQuota === 5) {
            lastManaRegen = Date.now();
            localStorage.setItem('lastManaRegen', lastManaRegen);
        }
        chatQuota--; 
        updateUIQuota();
    }

    try {
        const bubble = appendBubble('assistant', '<div class="spirit-thinking"><span></span><span></span><span></span></div>');

        const modular = window.currentReadingEnvelope;
        const apiResp = await fetch(modular ? '/api/v1/readings' : '/api/fortune', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: modular ? JSON.stringify({
                method: modular.method || 'tarot', persona: modular.persona || 'leopardcat',
                readingId: modular.reading_id, sessionToken: modular.session_token, question: text,
                lang: getQuestionLanguageTag(text), history: currentChatHistory
            }) : JSON.stringify({
                question: text, cardTitle: getLocalizedField(currentDrawnCard.title),
                cardMeaning: getLocalizedField(currentDrawnCard.meaning),
                lang: getQuestionLanguageTag(text), history: currentChatHistory
            })
        });
        if (apiResp.ok) {
            const data = await apiResp.json();
            const rawReply = data.reading;
            const htmlReply = typeof marked !== 'undefined' ? marked.parse(rawReply) : rawReply.replace(/\n/g, '<br>');
            
            const textContainer = document.createElement('div');
            textContainer.className = 'markdown-content';
            bubble.innerHTML = '';
            bubble.appendChild(textContainer);
            
            typeWriterHTML(textContainer, htmlReply, 15, () => {
                currentChatHistory.push({role:'user', content:text}, {role:'assistant', content:rawReply});
                updateTempleStats();
                document.getElementById('fortune-actions').classList.remove('hidden');
                btn.disabled = false;
                btn.innerText = originalText;
            });
        } else {
            throw new Error("API_ERROR");
        }
    } catch(e) {
        btn.disabled = false;
        btn.innerText = originalText;
    }
};

window.resetRitual = function() {
    clearReadingSnapshot();
    const cleanUrl = new URL(location.href);
    ['reading','share','card','orientation'].forEach(k => cleanUrl.searchParams.delete(k));
    history.replaceState(null, '', cleanUrl);
    currentChatHistory = [];
    window.currentReadingEnvelope = null;
    window.currentShareReceipt = null;
    window.currentReadingState = null;
    window.currentQuestionSource = null;
    window.currentQuestionLanguage = null;
    window.manualDrawState = { seed: null, selected: [], shuffled: false, submitting: false, phase: 'idle' };
    window.pendingDrawOptions = null;
    lastShareFile = null;
    lastShareText = "";
    lastShareBaseMessage = "";
    lastShareUrl = "";
    window.shareContentMode = 'quote';
    window.shareIncludeQuestion = false;
    syncShareContentControls();
    
    const historyDiv = document.getElementById('chat-history');
    if (historyDiv) historyDiv.innerHTML = '';
    
    const pinnedArea = document.getElementById('pinned-card-area');
    const pinnedDisplay = document.getElementById('pinned-card-display');
    if (pinnedArea) pinnedArea.classList.add('hidden');
    if (pinnedDisplay) pinnedDisplay.innerHTML = '';
    
    document.getElementById('fortune-chat-area').classList.add('hidden');
    document.getElementById('fortune-actions').classList.add('hidden');
    document.getElementById('social-share-row').classList.add('hidden');
    document.getElementById('fortune-ritual-area').classList.remove('hidden');
    document.getElementById('fortune-question').value = '';
    
    const btn = document.getElementById('btn-share-image');
    if (btn) {
        btn.innerText = uiText('share_generate', 'Generate Spirit Memo');
        btn.disabled = false;
    }
};

window.mintNFT = () => alert(uiText('coming_soon', 'Coming Soon'));

// 📋 Copy Ritual URL Helper
window.copyRitualUrl = function() {
    if (!window.shareUrl) {
        // Fallback to home if no card drawn
        window.shareUrl = window.location.origin + window.location.pathname;
    }
    navigator.clipboard.writeText(window.shareUrl).then(() => {
        const btn = document.getElementById('btn-copy-url');
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = uiText('copied_link', 'Link copied');
            setTimeout(() => { btn.innerHTML = originalText; }, 2000);
        }
    }).catch(err => {
        console.error('URL Copy Failed:', err);
    });
};



window.renderCustomDeckGallery = function(deck) {
    const section = document.getElementById('gallery');
    const container = document.getElementById('gallery-container');
    if (!section || !container) return;
    section.classList.remove('hidden');

    const sectionLabel = section.querySelector('.section-title .label');
    const sectionTitle = section.querySelector('.section-title h2');
    if (sectionLabel) { sectionLabel.removeAttribute('data-i18n'); sectionLabel.textContent = uiText('deck_gallery_label', 'Deck Gallery'); }
    if (sectionTitle) { sectionTitle.removeAttribute('data-i18n'); sectionTitle.textContent = uiText('deck_gallery_title', '{name} · Card Gallery', {name: deck.name}); }

    const cards = Array.isArray(deck.cards) ? deck.cards : [];
    container.innerHTML = `<div class="gallery-grid custom-deck-gallery"></div>`;
    const grid = container.querySelector('.gallery-grid');

    cards.forEach((card, index) => {
        const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || `Card ${index + 1}`;
        const upright = card.meanings?.upright || card.meaning?.[window.currentLang] || card.meaning || '';
        const reversed = card.meanings?.reversed || upright;
        const wrapper = document.createElement('div');
        wrapper.className = 'card-wrapper reveal-on-scroll theme-custom';
        wrapper.innerHTML = `
            <div class="card" id="gallery-${card.id || index}">
                <div class="card-front" style="background:#111;">
                    <img src="${card.image || ''}" alt="${title}" loading="lazy" style="width:100%;height:100%;object-fit:cover;display:block;">
                </div>
                <div class="card-back">
                    <div class="back-content" tabindex="0" aria-label="${uiText('card_meaning_scroll_aria', `${title} meaning, scroll vertically`, {title})}">
                        <button class="card-flip-back" type="button" aria-label="${uiText('card_flip_back', 'Flip to card face')}">↩ ${uiText('card_flip_back', 'Flip to card face')}</button>
                        <h3>${title}</h3>
                        <div class="meaning-box"><span class="label">${uiText('upright_meaning', 'Upright Meaning')}</span><p class="content-text"></p></div>
                        ${deck.reversals ? `<div class="ecology-box reversed-meaning"><span class="label">${uiText('reversed_meaning', 'Reversed Meaning')}</span><p class="content-text"></p></div>` : ''}
                    </div>
                </div>
            </div>`;
        wrapper.querySelector('.meaning-box .content-text').textContent = upright;
        const reversedText = wrapper.querySelector('.reversed-meaning .content-text');
        if (reversedText) reversedText.textContent = reversed;

        const cardInner = wrapper.querySelector('.card');
        const scrollable = wrapper.querySelector('.back-content');
        bindCardInteractions(cardInner, scrollable);
        grid.appendChild(wrapper);
        revealObserver?.observe(wrapper);
    });
};

window.loadActiveDeckBranding = async function() {
    if (!window.activeDeckId || window.activeDeckId === 'leopardcat') return;
    try {
        const resp = await fetch(`/api/v1/decks/${encodeURIComponent(window.activeDeckId)}`);
        if (!resp.ok) throw new Error('DECK_NOT_FOUND');
        const deck = await resp.json();
        window.activeDeckInfo = deck;
        if (window.drawMode === 'manual' && window.manualDrawState.shuffled) renderManualCardPool();
        if (!window.explicitThemeId && deck.default_theme && deck.default_theme !== window.activeThemeId) {
            window.activeThemeId = deck.default_theme;
            await window.applyTheme(deck.default_theme);
        }
        document.title = uiText('deck_page_title', '{name} · Online Tarot Reading', {name: deck.name});

        const logo = document.querySelector('.nav-logo');
        if (logo) { logo.removeAttribute('data-i18n'); logo.textContent = deck.name; }
        const heroTitle = document.querySelector('#hero h1');
        if (heroTitle) { heroTitle.removeAttribute('data-i18n'); heroTitle.textContent = deck.name; }
        const heroSubtitle = document.querySelector('#hero .subtitle');
        if (heroSubtitle) {
            heroSubtitle.removeAttribute('data-i18n');
            heroSubtitle.textContent = deck.description || (deck.creator ? uiText('deck_creator_summary', 'Created by {creator} · {count} cards', {creator: deck.creator, count: deck.card_count}) : uiText('deck_count_summary', '{count} cards', {count: deck.card_count}));
        }
        const fortuneTitle = document.querySelector('#fortune .section-title h2');
        if (fortuneTitle) { fortuneTitle.removeAttribute('data-i18n'); fortuneTitle.textContent = uiText('brand_fortune_template', '{name} · Tarot Reading', {name: deck.name}); }
        const fortuneLabel = document.querySelector('#fortune .section-title .label');
        if (fortuneLabel) { fortuneLabel.removeAttribute('data-i18n'); fortuneLabel.textContent = deck.creator ? `by ${deck.creator}` : uiText('creator_tarot', 'Creator Tarot'); }

        // LeopardCat-specific ecology/history stay hidden, but a creator deck gets its own card gallery.
        ['intro','chronicle'].forEach(id => document.getElementById(id)?.classList.add('hidden'));
        document.querySelector('a[href="#intro"]')?.classList.add('hidden');
        const galleryNav = document.querySelector('a[href="#gallery"]');
        if (galleryNav) { galleryNav.classList.remove('hidden'); galleryNav.removeAttribute('data-i18n'); galleryNav.textContent = uiText('gallery_nav', 'Card Gallery'); }
        window.cardData = Array.isArray(deck.cards) ? deck.cards : window.cardData;
        window.renderCustomDeckGallery(deck);

        const shareTitle = document.getElementById('share-memo-title');
        if (shareTitle) shareTitle.textContent = deck.name;
        const shareTag = document.getElementById('share-site-tag');
        if (shareTag) shareTag.textContent = deck.creator ? uiText('share_creator', 'Cards by {creator}', {creator: deck.creator}) : uiText('share_exclusive', 'Exclusive online reading');
        window.applyActiveBrand();
    } catch (err) {
        console.error('[Custom Deck] Unable to load deck:', err);
        const area = document.getElementById('fortune-ritual-area');
        if (area) area.innerHTML = `<p style="padding:24px;text-align:center">${uiText('deck_not_found', 'This deck could not be found.')}</p>`;
    }
};

// Custom deck bootstrap is owned by initAllSystems() to prevent manifest races.
