// Global state
let revealObserver;
let currentLang = localStorage.getItem('leopard-lang') || 'zh';
let siteData = null;
let cardData = [];
let chatQuota = parseInt(localStorage.getItem('chatQuota')) || 5;
let lastManaRegen = parseInt(localStorage.getItem('lastManaRegen')) || Date.now();
let currentChatHistory = [];
let currentDrawnCard = null;

// 🔱 Dharma Name Identity System
function initDharmaIdentity() {
    let name = localStorage.getItem('userDharmaName');
    if (!name) {
        const prefixes = ["山林", "雲霧", "古剎", "石虎", "冥想", "靜心"];
        const suffixes = ["行者", "求道貓", "徒兒", "隱士"];
        name = `${prefixes[Math.floor(Math.random()*prefixes.length)]}${suffixes[Math.floor(Math.random()*suffixes.length)]}`;
        localStorage.setItem('userDharmaName', name);
    }
    const nameElem = document.getElementById('user-dharma-name');
    if (nameElem) nameElem.innerText = name;
}

// Initialize Stats and Mana Regen
async function updateTempleStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        const vElem = document.getElementById('stat-visitors');
        const dElem = document.getElementById('stat-divinations');
        if (vElem) vElem.innerText = data.total_visitors;
        if (dElem) dElem.innerText = data.total_divinations;
    } catch(e) { console.error("Stats Error:", e); }
}

function startManaRegen() {
    setInterval(() => {
        const now = Date.now();
        const minutesPassed = (now - lastManaRegen) / (1000 * 60);
        
        if (minutesPassed >= 10 && chatQuota < 5) {
            chatQuota = Math.min(5, chatQuota + 1);
            lastManaRegen = now;
            localStorage.setItem('chatQuota', chatQuota);
            localStorage.setItem('lastManaRegen', lastManaRegen);
            updateUIQuota();
        }
    }, 60 * 1000); 
}

function updateUIQuota() {
    const manaDisplay = document.getElementById('user-mana-display');
    if (manaDisplay) manaDisplay.innerText = `⚡ ${chatQuota}/5`;
    localStorage.setItem('chatQuota', chatQuota);
}

// Initialize All Systems
async function initAllSystems() {
    console.log("System Initializing...");
    try {
        initDharmaIdentity();
        updateTempleStats();
        startManaRegen();
        updateUIQuota();

        // Emergency Fallback: If after 3s still invisible, force reveal
        setTimeout(() => {
            document.querySelectorAll('.section, .reveal-on-scroll').forEach(el => {
                if (!el.classList.contains('visible')) {
                    console.warn("Emergency reveal triggered for:", el);
                    el.classList.add('visible');
                }
            });
        }, 3000);

        // Load Content (Already moved to root by terminal scripts)
        let success = false;
        let cR = await fetch('content.json', { cache: 'no-cache' });
        let mR = await fetch('manifest.json', { cache: 'no-cache' });
        
        if (cR.ok && mR.ok) {
            siteData = await cR.json();
            cardData = await mR.json();
            success = true;
        } else {
            console.log("Trying fallback to public/...");
            cR = await fetch('public/content.json', { cache: 'no-cache' });
            mR = await fetch('public/manifest.json', { cache: 'no-cache' });
            if (cR.ok && mR.ok) {
                siteData = await cR.json();
                cardData = await mR.json();
                success = true;
            }
        }
        
        if (!success) throw new Error("Could not load content/manifest JSON.");

        applyLanguage();
        initScrollReveal(); 
        console.log("Systems ready.");
        
    } catch (err) {
        console.error('Initialization Failed:', err);
        const errDiv = document.createElement('div');
        errDiv.style = "position:fixed; bottom:0; padding:10px; background:red; color:white; z-index:10000; font-size:10px; width:100%;";
        errDiv.innerText = "🚨 渲染報錯: " + err.message;
        document.body.appendChild(errDiv);
    }
}

document.addEventListener('DOMContentLoaded', initAllSystems);

function setLanguage(lang) {
    if (lang === currentLang) return;
    currentLang = lang;
    localStorage.setItem('leopard-lang', lang);
    applyLanguage();
}

function applyLanguage() {
    if (!siteData || !cardData) return;
    const data = siteData[currentLang];
    
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        for (const section in data) {
            if (typeof data[section] === 'object' && data[section][key]) {
                if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                    el.placeholder = data[section][key];
                } else {
                    el.textContent = data[section][key];
                }
            }
        }
    });

    document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`btn-${currentLang}`);
    if (activeBtn) activeBtn.classList.add('active');

    if (data.introduction) renderIntro(data.introduction);
    if (data.events) renderEvents(data.events);
    if (data.groups) renderGallery(data.groups, cardData);
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
    container.innerHTML = '';

    // Master Sort: Absolute Guarantee of Numerical Order (Fixes 1, 10, 2 string sort mess)
    cards.sort((a, b) => {
        const nA = typeof a.number === 'number' ? a.number : parseInt(a.number);
        const nB = typeof b.number === 'number' ? b.number : parseInt(b.number);
        return nA - nB;
    });

    (groups || []).forEach(group => {
        const groupEl = document.createElement('div');
        groupEl.className = 'group-section section';
        groupEl.innerHTML = `
            <div class="group-info">
                <h3>${group.title}</h3>
                <p class="content-text">${group.description}</p>
            </div>
            <div class="gallery-grid" id="grid-${group.id}"></div>
        `;
        container.appendChild(groupEl);
        revealObserver?.observe(groupEl);

        const grid = groupEl.querySelector('.gallery-grid');
        let filtered = [];
        if (group.id === 'material') filtered = cards.filter(c => c.number >= 0 && c.number <= 7);
        else if (group.id === 'inner') filtered = cards.filter(c => c.number >= 8 && c.number <= 14);
        else if (group.id === 'cosmic') filtered = cards.filter(c => c.number >= 15 && c.number <= 21);
        else if (group.id === 'wands') filtered = cards.filter(c => c.number >= 101 && c.number <= 114);
        else if (group.id === 'cups') filtered = cards.filter(c => c.number >= 201 && c.number <= 214);
        else if (group.id === 'swords') filtered = cards.filter(c => c.number >= 301 && c.number <= 314);
        else filtered = cards.filter(c => (c.suit === group.id));

        if (filtered.length === 0) return;

        filtered.forEach(card => {
            const cardEl = createCardElement(card, group.id);
            grid.appendChild(cardEl);
            revealObserver?.observe(cardEl); 
        });
    });
}

function createCardElement(card, groupId) {
    const wrapper = document.createElement('div');
    wrapper.className = `card-wrapper reveal-on-scroll theme-${groupId}`;
    const title = (card.title && typeof card.title === 'object' ? card.title[currentLang] : card.title) || 'TBD';
    const meaning = (card.meaning && typeof card.meaning === 'object' ? card.meaning[currentLang] : card.meaning) || 'TBD';
    const ecology = (card.ecology && typeof card.ecology === 'object' ? card.ecology[currentLang] : card.ecology) || 'TBD';
    const lM = currentLang === 'zh' ? '塔羅牌義' : 'Tarot Meaning';
    const lE = currentLang === 'zh' ? '石虎生態' : 'Eco-Connection';

    wrapper.innerHTML = `
        <div class="card" id="${card.id}">
            <div class="card-front"><img src="art/renders/${card.id}.png" alt="${title}" loading="lazy" onerror="this.src='https://placehold.co/1400x2420/0a110e/d4af37?text=${title}'"></div>
            <div class="card-back">
                <div class="back-content">
                    <h3>${title}</h3>
                    <div class="meaning-box"><span class="label">${lM}</span><p class="content-text">${meaning}</p></div>
                    <div class="ecology-box"><span class="label">${lE}</span><p class="content-text">${ecology}</p></div>
                </div>
            </div>
        </div>
    `;
    wrapper.addEventListener('click', () => wrapper.querySelector('.card').classList.toggle('is-flipped'));
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
    // Observe all initial sections AND dynamic elements
    document.querySelectorAll('.section, .reveal-on-scroll').forEach(el => revealObserver.observe(el));
}

// --- Fortune Logic ---
function appendBubble(role, text) {
    const historyDiv = document.getElementById('chat-history');
    if (!historyDiv) return;
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;
    let q = role === 'assistant' ? `<div style="font-size:0.6rem; opacity:0.6; margin-top:5px;">⚡ ${chatQuota}/5</div>` : '';
    bubble.innerHTML = text.replace(/\n/g, '<br>') + q;
    historyDiv.appendChild(bubble);
    historyDiv.scrollTop = historyDiv.scrollHeight;
}

window.drawFortune = async function() {
    if (chatQuota <= 0) return alert("⚡ 靈氣已耗盡。");
    const q = document.getElementById('fortune-question').value;
    if (!q.trim()) return alert("大師需要聽見你心中的疑惑！");
    
    try {
        const card = cardData[Math.floor(Math.random() * cardData.length)];
        chatQuota--;
        updateUIQuota();
        
        document.getElementById('fortune-ritual-area').classList.add('hidden');
        document.getElementById('fortune-chat-area').classList.remove('hidden');
        
        appendBubble('user', q);
        appendBubble('assistant', "大師正在感應中...");

        const apiResp = await fetch('/api/fortune', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: q, cardTitle: card.title[currentLang], cardMeaning: card.meaning[currentLang], lang: currentLang })
        });
        
        const historyDiv = document.getElementById('chat-history');
        historyDiv.lastChild.remove(); // Remove loading bubble
        
        let reply = card.meaning[currentLang];
        if (apiResp.ok) {
            const data = await apiResp.json();
            reply = data.reading;
        }

        const replyMsg = `大師為你抽出了 <strong>【${card.title[currentLang]}】</strong>。<br>
            <img src="art/renders/${card.id}.png" style="width:100%; max-width:240px; margin:15px auto; border-radius:12px; display:block; border:1px solid rgba(212,175,55,0.4); box-shadow:0 0 20px rgba(0,0,0,0.5);">
            ${reply}`;
        
        appendBubble('assistant', replyMsg);
        currentDrawnCard = card;
        currentChatHistory.push({role: 'user', content: q}, {role: 'assistant', content: reply});

    } catch (e) { console.error(e); }
};

window.sendChatMessage = async function() {
    const input = document.getElementById('chat-input');
    const text = input.value.trim();
    if (!text || chatQuota <= 0) return;
    input.value = '';
    appendBubble('user', text);
    chatQuota--; updateUIQuota();

    try {
        const apiResp = await fetch('/api/fortune', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: text, cardTitle: currentDrawnCard.title[currentLang], cardMeaning: currentDrawnCard.meaning[currentLang], lang: currentLang, history: currentChatHistory })
        });
        if (apiResp.ok) {
            const data = await apiResp.json();
            appendBubble('assistant', data.reading);
            currentChatHistory.push({role:'user', content:text}, {role:'assistant', content:data.reading});
        }
    } catch(e) {}
};

window.resetRitual = function() {
    currentChatHistory = [];
    document.getElementById('chat-history').innerHTML = '';
    document.getElementById('fortune-chat-area').classList.add('hidden');
    document.getElementById('fortune-ritual-area').classList.remove('hidden');
};

window.setLanguage = setLanguage;
