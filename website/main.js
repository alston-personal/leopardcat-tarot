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
    en: { label: 'EN', htmlLang: 'en' }
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
    available.forEach(lang => {
        const meta = window.localeMeta[lang] || {};
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'lang-btn';
        button.id = `btn-${lang}`;
        button.dataset.locale = lang;
        button.textContent = meta.label || lang.toUpperCase();
        button.setAttribute('aria-label', `Language: ${lang}`);
        button.addEventListener('click', () => window.setLanguage(lang));
        host.appendChild(button);
    });
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
window.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic

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
        nameElem.title = window.currentLang === 'zh' ? '點擊重修法號' : 'Click to redraw name';
        nameElem.style.cursor = 'pointer';
        // 🔄 Allow redraw ritual
        nameElem.onclick = () => {
            if (confirm(window.currentLang === 'zh' ? '是否要重新洗滌靈魂，重修法號？' : 'Redraw your spiritual identity?')) {
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
    loadingOverlay.innerHTML = '<div class="spirit-thinking"><span></span><span></span><span></span></div><p style="color:var(--color-gold);margin-top:10px;font-size:0.8rem;letter-spacing:0.1em;">牌卡體驗載入中...</p>';
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
                <p style="color:#ff6b6b;font-size:0.8rem;">靈力連線不穩 (${errType})</p>
                <p style="color:#666;font-size:0.6rem;margin-top:5px;">${errMsg}</p>
                <button onclick="location.reload()" style="margin-top:15px;background:none;border:1px solid var(--color-gold);color:var(--color-gold);padding:5px 15px;border-radius:15px;font-size:0.7rem;">重新祈願</button>
            </div>
        `;
    }
}

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
                <div class="back-content" tabindex="0" aria-label="${title} 牌義，可上下捲動">
                    <button class="card-flip-back" type="button" aria-label="翻回牌面">↩ 翻回牌面</button>
                    <h3>${title}</h3>
                    <div class="meaning-box"><span class="label">${lM}</span><p class="content-text">${meaning}</p></div>
                    <div class="ecology-box"><span class="label">${lE}</span><p class="content-text">${formattedEcology}</p></div>
                </div>
            </div>
        </div>
    `;
    const cardInner = wrapper.querySelector('.card');
    
    // 🛡️ Interaction Isolation: Ensure Scroll > Flip on text areas
    const scrollableContent = wrapper.querySelector('.back-content');
    if (scrollableContent) {
        scrollableContent.addEventListener('touchstart', (e) => e.stopPropagation(), { passive: true });
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

            if (panelCanConsume) {
                e.preventDefault();
                e.stopPropagation();
                scrollableContent.scrollTop += e.deltaY;
            }
        }, { passive: false });
        scrollableContent.addEventListener('click', (e) => e.stopPropagation());
        const flipBack = scrollableContent.querySelector('.card-flip-back');
        flipBack?.addEventListener('click', (e) => { e.stopPropagation(); cardInner.classList.remove('is-flipped'); });
    }

    let touchStartY = 0;
    let touchStartTime = 0;

    cardInner.addEventListener('touchstart', (e) => {
        touchStartY = e.touches[0].clientY;
        touchStartTime = Date.now();
    }, { passive: true });

    cardInner.addEventListener('touchend', (e) => {
        const touchEndY = e.changedTouches[0].clientY;
        const touchDuration = Date.now() - touchStartTime;
        const scrollDiff = Math.abs(touchEndY - touchStartY);

        // Only flip if it's a quick tap and almost no vertical movement
        if (touchDuration < 250 && scrollDiff < 10) {
            e.stopPropagation();
            cardInner.classList.toggle('is-flipped');
        }
    }, { passive: true });

    // Desktop support
    cardInner.addEventListener('click', (e) => {
        // If clicking inside back-content, check if we're selecting text or just tapping
        if (window.getSelection().toString()) return; 
        cardInner.classList.toggle('is-flipped');
    });

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
    btn.innerText = window.currentLang === 'zh' ? '🪄 靈光匯聚中...' : '🪄 Gathering Mana...';
    btn.disabled = true;

    const template = document.getElementById('share-card-template');
    
    // Fill data
    const shareState = window.currentReadingState || {};
    const shareOrientation = shareState.orientation || 'upright';
    const shareImage = currentDrawnCard.image || `art/renders/${currentDrawnCard.id}.webp`;
    const shareImgEl = document.getElementById('share-card-img');
    shareImgEl.src = shareImage;
    shareImgEl.style.transform = shareOrientation === 'reversed' ? 'rotate(180deg)' : '';
    const titleZh = currentDrawnCard.title?.zh || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.en || currentDrawnCard.id;
    const titleEn = currentDrawnCard.title?.en || titleZh;
    const orientationLabel = shareOrientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');
    document.getElementById('share-card-title').innerText = `【${titleZh} / ${titleEn}】 · ${orientationLabel}`;
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
    const quote = bestQuote || window.brandText('default_quote', window.currentLang === 'zh' ? '聽見牌面，也聽見自己。' : 'Listen to the cards, and to yourself.');
    document.getElementById('share-quote').innerText = quote;

    // 🕵️ Stability: Wait for image load + small layout settling delay
    const shareCardImg = document.getElementById('share-card-img');
    await Promise.race([
        new Promise(resolve => {
            if (shareCardImg.complete) resolve();
            else {
                shareCardImg.onload = resolve;
                shareCardImg.onerror = resolve; // Don't hang
            }
        }),
        new Promise(resolve => setTimeout(resolve, 5000)) // Force continue after 5s
    ]);
    await new Promise(resolve => setTimeout(resolve, 300)); // Layout settling delay

    console.time('ManaGathering');
    try {
        const canvas = await Promise.race([
            html2canvas(template, {
                useCORS: true,
                allowTaint: true,
                logging: false,
                backgroundColor: '#0a0f0d',
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
        document.getElementById('share-memo-title').innerText = window.brandText('share_title', uiCommon.share_memo_title);
        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;
        document.getElementById('share-site-tag').innerText = window.brandText('share_site_tag', uiCommon.share_site_tag);
        document.getElementById('share-date').innerText = new Date().toLocaleDateString(window.currentLang === 'zh' ? 'zh-TW' : 'en-US');

        const shareTitle = currentDrawnCard.title?.[shareLang] || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.zh || currentDrawnCard.title?.en || currentDrawnCard.id;
        const orientationText = (window.currentReadingState?.orientation === 'reversed') ? (shareLang === 'zh' ? '（逆位）' : ' (Reversed)') : '';
        const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);
        const shareMsg = brandTemplate.replace('{card}', `${shareTitle}${orientationText}`);
        // Shared deep link preserves deck + theme + card + orientation.
        const shareU = new URL(window.location.origin + window.location.pathname);
        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);
        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);
        if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);
        shareU.searchParams.set('card', currentDrawnCard.id);
        if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');
        const shareUrl = shareU.toString();
        
        const fullShareText = `${shareMsg} ${shareUrl}`;
        lastShareText = fullShareText;

        const lineLink = document.getElementById('share-line');
        if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(fullShareText)}`;
        
        const fbRefresh = Date.now();
        const fbUrlSeparator = shareUrl.includes('?') ? '&' : '?';
        const fbShareUrl = `${shareUrl}${fbUrlSeparator}fbrefresh=${fbRefresh}`;
        document.getElementById('share-fb').href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(fbShareUrl)}&quote=${encodeURIComponent(shareMsg)}`;
        
        // 🐦 X (Twitter) unified format for best compatibility
        document.getElementById('share-x').href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;
        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(fullShareText)}`;
        
        document.getElementById('social-share-row').classList.remove('hidden');

        // 🔗 Sync Metadata immediately
        updateSocialLinks(currentDrawnCard, bestQuote);

        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/png'));
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
                alert(window.currentLang === 'zh' ? "✨ 靈山紀錄已下載！\n請手動上傳至社群分享。" : "✨ Spirit Memo downloaded!\nPlease upload it manually to share.");
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
    shareU.searchParams.set('card', card.id);
    if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');
    const shareUrl = shareU.toString();
    window.shareUrl = shareUrl; // Store for the copy button
    
    // Update button text to encourage the next step
    const shareBtn = document.getElementById('btn-share-image');
    if (shareBtn) {
        shareBtn.innerHTML = `✨ 靈光已存入剪貼簿`;
        setTimeout(() => {
            shareBtn.innerHTML = `再次生成分享卡`;
        }, 5000);
    }
    const fullShareText = `${shareMsg} ${shareUrl}`;
    
    lastShareText = fullShareText;

    const lineLink = document.getElementById('share-line');
    if (lineLink) lineLink.href = `https://social-plugins.line.me/lineit/share?url=${encodeURIComponent(shareUrl)}&text=${encodeURIComponent(fullShareText)}`;
    
    const fbLink = document.getElementById('share-fb');
    if (fbLink) fbLink.href = `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}&quote=${encodeURIComponent(fullShareText)}`;
    
    const xLink = document.getElementById('share-x');
    if (xLink) xLink.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(fullShareText)}`;
    
    const threadsLink = document.getElementById('share-threads');
    if (threadsLink) threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(fullShareText)}`;
    
    document.getElementById('social-share-row')?.classList.remove('hidden');
}

function modularErrorMessage(e) {
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
    setText('#fortune .section-title h2', `${b.short_name || b.app_name}・塔羅占卜`);
    setText('#fortune .section-title .label', b.creator_line || 'Creator Tarot');
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
        box.innerHTML = '<label style="display:flex;gap:6px;align-items:center">解牌者 <select id="persona-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>';
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

window.activeThemeId = new URLSearchParams(window.location.search).get('theme') || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');

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
    box.innerHTML = '<label style="display:flex;gap:6px;align-items:center">頁面風格 <select id="theme-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>';
    document.body.appendChild(box);
    const sel = box.querySelector('select');
    try {
        const r = await fetch('/api/v1/themes'); const d = await r.json();
        for (const t of d.themes || []) { const o=document.createElement('option'); o.value=t.theme_id; o.textContent=t.name; sel.appendChild(o); }
        if (![...sel.options].some(o=>o.value===window.activeThemeId)) { const o=document.createElement('option'); o.value=window.activeThemeId; o.textContent='這副牌的自訂風格'; sel.appendChild(o); }
        sel.value = window.activeThemeId; sel.addEventListener('change', ()=>window.applyTheme(sel.value,true));
    } catch (_) {}
    await window.applyTheme(window.activeThemeId);
};

document.addEventListener('DOMContentLoaded', () => window.initThemeSwitcher());

window.getModularReading = async function(q) {
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
            lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
        } : {
            method: 'tarot', persona: window.activePersonaId || undefined, question: q,
            input: { spread: 'auto', deck_id: window.activeDeckId },
            lang: window.currentLang === 'zh' ? 'zh-TW' : 'en'
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
    window.activePersonaId = data.persona || window.activePersonaId || window.defaultPersonaId;
    removeSensing();
    const specs = data.method_result?.cards || [];
    if (!specs.length) throw new Error('DIVINATION_V1_EMPTY_RESULT');
    const resolved = specs.map(spec => ({spec, card: window.cardData.find(c => c.id === spec.card_id) || spec})).filter(x => x.card);
    if (!resolved.length) throw new Error('DIVINATION_V1_CARD_NOT_FOUND');
    currentDrawnCard = resolved[0].card;
    window.currentDrawnCard = currentDrawnCard;
    window.currentReadingEnvelope = data;
    window.currentReadingState = {
        deck_id: window.activeDeckId,
        theme_id: window.activeThemeId,
        persona_id: window.activePersonaId,
        card_id: resolved[0].spec.card_id || currentDrawnCard.id,
        orientation: resolved[0].spec.orientation || 'upright',
        spread: data.method_result?.spread || 'single',
        cards: resolved.map(({spec, card}) => ({ card_id: spec.card_id || card.id, orientation: spec.orientation || 'upright', position: spec.position, position_label: spec.position_label }))
    };
    window._lastQuestion = q;
    const pinnedArea = document.getElementById('pinned-card-area');
    const pinnedDisplay = document.getElementById('pinned-card-display');
    if (pinnedArea && pinnedDisplay) {
        pinnedArea.classList.remove('hidden');
        pinnedDisplay.innerHTML = `<div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">${resolved.map(({spec, card}) => {
            const orientation = spec.orientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');
            const pos = spec.position_label || spec.position || '';
            const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id;
            const rotate = spec.orientation === 'reversed' ? 'transform:rotate(180deg);' : '';
            const imageSrc = card.image || `art/renders/${card.id}.webp`; return `<div class="pinned-card-content" style="max-width:150px;"><img src="${imageSrc}" class="pinned-card-img" style="${rotate}"><div class="pinned-card-title">【${title}】<br><small>${pos} · ${orientation}</small></div></div>`;
        }).join('')}</div>`;
    }
    const spreadNames = {
        single: window.currentLang === 'zh' ? '單牌指引' : 'Single Guidance',
        three_card: window.currentLang === 'zh' ? '三牌時間流' : 'Three-card Timeline',
        decision: window.currentLang === 'zh' ? '抉擇三牌' : 'Decision Spread'
    };
    const spread = data.method_result?.spread || 'single';
    const summary = resolved.map(({spec, card}) => {
        const orientation = spec.orientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');
        const title = card.title?.[window.currentLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id; return `${spec.position_label || spec.position}: ${title}（${orientation}）`;
    }).join(' / ');
    const prefix = `${window.currentLang === 'zh' ? '大師展開' : 'The Master opens'} <strong>【${spreadNames[spread] || spread}】</strong><br><small>${summary}</small><br>`;
    const bubble = appendBubble('assistant', prefix);
    const textContainer = document.createElement('div');
    textContainer.className = 'markdown-content';
    bubble.appendChild(textContainer);
    const rawReply = data.reading || '';
    const htmlReply = typeof marked !== 'undefined' ? marked.parse(rawReply) : rawReply.replace(/\n/g, '<br>');
    typeWriterHTML(textContainer, htmlReply, 35, () => {
        currentChatHistory.push({role:'user', content:q}, {role:'assistant', content:rawReply});
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
        const errText = window.currentLang === 'zh' ? '大師暫時斷了聯繫，靈氣不足...' : 'Connection lost, mana insufficient...';
        const btnText = window.currentLang === 'zh' ? '重新祈請' : 'Retry';
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
                    cardTitle: card.title[window.currentLang],
                    cardMeaning: card.meaning[window.currentLang],
                    lang: window.currentLang,
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
    const rawReply = data.reading || card.meaning[window.currentLang];
        
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
                    <div class="pinned-card-title">【${card.title[window.currentLang]}】</div>
                </div>
            `;
        }

        const prefix = `${common.msg_draw_prefix} <strong>【${card.title[window.currentLang]}】</strong>。<br>`;
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
    btn.innerText = window.currentLang === 'zh' ? '祈請中...' : 'Seeking...';

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
                lang: window.currentLang === 'zh' ? 'zh-TW' : 'en', history: currentChatHistory
            }) : JSON.stringify({
                question: text, cardTitle: currentDrawnCard.title[window.currentLang],
                cardMeaning: currentDrawnCard.meaning[window.currentLang],
                lang: window.currentLang, history: currentChatHistory
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
    currentChatHistory = [];
    window.currentReadingEnvelope = null;
    window.currentReadingState = null;
    lastShareFile = null;
    lastShareText = "";
    
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
        btn.innerText = window.currentLang === 'zh' ? '生成靈山分享卡' : 'Generate Spirit Memo';
        btn.disabled = false;
    }
};

window.mintNFT = () => alert(window.currentLang === 'zh' ? "即將開放" : "Coming Soon");

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
            btn.innerHTML = "已複製連結";
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
    if (sectionLabel) { sectionLabel.removeAttribute('data-i18n'); sectionLabel.textContent = 'Deck Gallery'; }
    if (sectionTitle) { sectionTitle.removeAttribute('data-i18n'); sectionTitle.textContent = `${deck.name}・牌卡展示`; }

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
                    <div class="back-content" tabindex="0" aria-label="${title} 牌義，可上下捲動">
                        <button class="card-flip-back" type="button" aria-label="翻回牌面">↩ 翻回牌面</button>
                        <h3>${title}</h3>
                        <div class="meaning-box"><span class="label">正位牌義</span><p class="content-text"></p></div>
                        ${deck.reversals ? '<div class="ecology-box reversed-meaning"><span class="label">逆位牌義</span><p class="content-text"></p></div>' : ''}
                    </div>
                </div>
            </div>`;
        wrapper.querySelector('.meaning-box .content-text').textContent = upright;
        const reversedText = wrapper.querySelector('.reversed-meaning .content-text');
        if (reversedText) reversedText.textContent = reversed;

        const cardInner = wrapper.querySelector('.card');
        const scrollable = wrapper.querySelector('.back-content');
        scrollable.addEventListener('wheel', (e) => {
            const maxScroll = Math.max(0, scrollable.scrollHeight - scrollable.clientHeight);
            const atTop = scrollable.scrollTop <= 0;
            const atBottom = scrollable.scrollTop >= maxScroll - 1;
            const canConsume = maxScroll > 0 && !((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom));
            if (canConsume) {
                e.preventDefault();
                e.stopPropagation();
                scrollable.scrollTop += e.deltaY;
            }
        }, { passive:false });
        scrollable.addEventListener('click', e => e.stopPropagation());
        scrollable.addEventListener('touchstart', e => e.stopPropagation(), { passive:true });
        scrollable.addEventListener('touchend', e => e.stopPropagation(), { passive:true });
        scrollable.querySelector('.card-flip-back')?.addEventListener('click', e => {
            e.stopPropagation();
            cardInner.classList.remove('is-flipped');
        });
        cardInner.addEventListener('click', () => cardInner.classList.toggle('is-flipped'));
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
        document.title = `${deck.name}・線上塔羅占卜`;

        const logo = document.querySelector('.nav-logo');
        if (logo) { logo.removeAttribute('data-i18n'); logo.textContent = deck.name; }
        const heroTitle = document.querySelector('#hero h1');
        if (heroTitle) { heroTitle.removeAttribute('data-i18n'); heroTitle.textContent = deck.name; }
        const heroSubtitle = document.querySelector('#hero .subtitle');
        if (heroSubtitle) {
            heroSubtitle.removeAttribute('data-i18n');
            heroSubtitle.textContent = deck.description || (deck.creator ? `由 ${deck.creator} 創作・${deck.card_count} 張牌` : `${deck.card_count} 張牌`);
        }
        const fortuneTitle = document.querySelector('#fortune .section-title h2');
        if (fortuneTitle) { fortuneTitle.removeAttribute('data-i18n'); fortuneTitle.textContent = `${deck.name}・塔羅占卜`; }
        const fortuneLabel = document.querySelector('#fortune .section-title .label');
        if (fortuneLabel) { fortuneLabel.removeAttribute('data-i18n'); fortuneLabel.textContent = deck.creator ? `by ${deck.creator}` : 'Creator Tarot'; }

        // LeopardCat-specific ecology/history stay hidden, but a creator deck gets its own card gallery.
        ['intro','chronicle'].forEach(id => document.getElementById(id)?.classList.add('hidden'));
        document.querySelector('a[href="#intro"]')?.classList.add('hidden');
        const galleryNav = document.querySelector('a[href="#gallery"]');
        if (galleryNav) { galleryNav.classList.remove('hidden'); galleryNav.removeAttribute('data-i18n'); galleryNav.textContent = '牌卡展示'; }
        window.cardData = Array.isArray(deck.cards) ? deck.cards : window.cardData;
        window.renderCustomDeckGallery(deck);

        const shareTitle = document.getElementById('share-memo-title');
        if (shareTitle) shareTitle.textContent = deck.name;
        const shareTag = document.getElementById('share-site-tag');
        if (shareTag) shareTag.textContent = deck.creator ? `牌卡創作：${deck.creator}` : '專屬線上占卜';
        window.applyActiveBrand();
    } catch (err) {
        console.error('[Custom Deck] Unable to load deck:', err);
        const area = document.getElementById('fortune-ritual-area');
        if (area) area.innerHTML = '<p style="padding:24px;text-align:center">找不到這副牌，可能已下架或網址有誤。</p>';
    }
};

// Custom deck bootstrap is owned by initAllSystems() to prevent manifest races.
