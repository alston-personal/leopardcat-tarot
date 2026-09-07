const SNAPSHOT_VERSION = 1;
const SNAPSHOT_HASH_KEY = 'lcshare';
const DEFAULT_MODE = 'highlight';
const DEFAULT_TTL_HOURS = 24 * 30;
const MAX_ANSWER_CHARS = 12000;

function bytesToB64Url(bytes) {
  let binary = '';
  bytes.forEach(b => { binary += String.fromCharCode(b); });
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
}

function b64UrlToBytes(text) {
  const normalized = String(text || '').replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized + '='.repeat((4 - normalized.length % 4) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, ch => ch.charCodeAt(0));
}

function latestAssistantText() {
  const bubbles = [...document.querySelectorAll('#chat-history .chat-bubble.assistant')];
  const last = bubbles[bubbles.length - 1];
  if (!last) return '';
  const content = last.querySelector('.markdown-content') || last;
  return String(content.innerText || content.textContent || '').trim();
}

function currentPublicQuestion() {
  const source = window.currentQuestionSource;
  if (source?.type === 'threads' && source.text) return String(source.text).trim();
  return String(window._lastQuestion || document.getElementById('fortune-question')?.value || '').trim();
}

function currentHighlight() {
  return String(document.getElementById('share-quote')?.innerText || '').trim();
}

function currentCards() {
  const state = window.currentReadingState || {};
  const cards = Array.isArray(state.cards) ? state.cards : [];
  return cards.map(card => ({
    card_id: card.card_id || card.id || '',
    orientation: card.orientation || 'upright',
    position: card.position || '',
    position_label: card.position_label || '',
  })).filter(card => card.card_id);
}

function getSnapshotMode() {
  return document.getElementById('share-snapshot-mode')?.value || DEFAULT_MODE;
}

function getSnapshotTTLHours() {
  const value = Number(document.getElementById('share-snapshot-ttl')?.value || DEFAULT_TTL_HOURS);
  return Number.isFinite(value) && value > 0 ? value : DEFAULT_TTL_HOURS;
}

function editablePublicQuestion() {
  const field = document.getElementById('share-public-question');
  return String(field?.value || currentPublicQuestion()).trim();
}

function buildSnapshotPlaintext() {
  const mode = getSnapshotMode();
  if (mode === 'cards') return null;
  const includeQuestion = mode === 'question' || Boolean(document.getElementById('share-include-question')?.checked);
  const now = Date.now();
  const ttlHours = getSnapshotTTLHours();
  const answer = latestAssistantText().slice(0, MAX_ANSWER_CHARS);
  const snapshot = {
    schema: 'leopardcat.share-snapshot/v1',
    version: SNAPSHOT_VERSION,
    created_at: now,
    expires_at: now + ttlHours * 60 * 60 * 1000,
    mode,
    deck_id: window.currentReadingState?.deck_id || window.activeDeckId || 'leopardcat',
    theme_id: window.currentReadingState?.theme_id || window.activeThemeId || null,
    persona_id: window.currentReadingState?.persona_id || window.activePersonaId || null,
    spread: window.currentReadingState?.spread || window.effectiveSpread || 'single',
    cards: currentCards(),
    question: includeQuestion ? editablePublicQuestion() : null,
    highlight: mode === 'highlight' || mode === 'full' ? currentHighlight() : null,
    answer: mode === 'full' ? answer : null,
    source: window.currentQuestionSource?.type === 'threads' ? {
      type: 'threads',
      url: String(window.currentQuestionSource.url || ''),
      author: window.currentQuestionSource.author || null,
    } : null,
  };
  return snapshot;
}

async function encryptSnapshot(snapshot) {
  const key = await crypto.subtle.generateKey({name: 'AES-GCM', length: 256}, true, ['encrypt', 'decrypt']);
  const rawKey = new Uint8Array(await crypto.subtle.exportKey('raw', key));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const plaintext = new TextEncoder().encode(JSON.stringify(snapshot));
  const ciphertext = new Uint8Array(await crypto.subtle.encrypt({name: 'AES-GCM', iv}, key, plaintext));
  return `${SNAPSHOT_VERSION}.${bytesToB64Url(rawKey)}.${bytesToB64Url(iv)}.${bytesToB64Url(ciphertext)}`;
}

async function decryptSnapshot(encoded) {
  const [versionText, keyText, ivText, cipherText] = String(encoded || '').split('.');
  if (Number(versionText) !== SNAPSHOT_VERSION || !keyText || !ivText || !cipherText) throw new Error('invalid_snapshot');
  const key = await crypto.subtle.importKey('raw', b64UrlToBytes(keyText), 'AES-GCM', false, ['decrypt']);
  const plaintext = await crypto.subtle.decrypt({name: 'AES-GCM', iv: b64UrlToBytes(ivText)}, key, b64UrlToBytes(cipherText));
  const snapshot = JSON.parse(new TextDecoder().decode(plaintext));
  if (snapshot?.schema !== 'leopardcat.share-snapshot/v1') throw new Error('invalid_snapshot_schema');
  if (Number(snapshot.expires_at || 0) <= Date.now()) throw new Error('snapshot_expired');
  return snapshot;
}

function withSnapshotFragment(baseUrl, encrypted) {
  const u = new URL(baseUrl, location.href);
  const params = new URLSearchParams(u.hash.replace(/^#/, ''));
  params.set(SNAPSHOT_HASH_KEY, encrypted);
  u.hash = params.toString();
  return u.toString();
}

function injectControls() {
  const host = document.getElementById('share-content-controls');
  if (!host || document.getElementById('share-snapshot-mode')) return;
  const box = document.createElement('div');
  box.id = 'share-snapshot-controls';
  box.style.cssText = 'margin-top:10px;padding-top:10px;border-top:1px solid rgba(212,175,55,.18);display:grid;gap:8px';
  box.innerHTML = `
    <label style="display:grid;gap:4px;font-size:.78rem">
      <span>分享頁內容</span>
      <select id="share-snapshot-mode" style="padding:7px;border-radius:8px;background:var(--color-panel,#111);color:inherit">
        <option value="cards">只分享牌卡</option>
        <option value="question">牌卡＋問題</option>
        <option value="highlight" selected>牌卡＋大師精華</option>
        <option value="full">完整占卜</option>
      </select>
    </label>
    <label style="display:grid;gap:4px;font-size:.78rem">
      <span>公開問題（可先匿名化／改寫）</span>
      <textarea id="share-public-question" rows="2" style="padding:7px;border-radius:8px;background:var(--color-panel,#111);color:inherit"></textarea>
    </label>
    <label style="display:grid;gap:4px;font-size:.78rem">
      <span>有效期限</span>
      <select id="share-snapshot-ttl" style="padding:7px;border-radius:8px;background:var(--color-panel,#111);color:inherit">
        <option value="24">24 小時</option>
        <option value="168">7 天</option>
        <option value="720" selected>30 天</option>
      </select>
    </label>
    <p style="margin:0;font-size:.7rem;line-height:1.55;opacity:.72">私人提問與大師答案仍不寫入伺服器資料庫；只有你選擇公開的內容會在瀏覽器端加密並放入分享連結的 URL fragment。伺服器與社群預覽爬蟲看不到解密金鑰。</p>`;
  host.appendChild(box);
  const q = box.querySelector('#share-public-question');
  q.value = currentPublicQuestion();
  box.querySelector('#share-snapshot-mode').addEventListener('change', () => {
    const mode = getSnapshotMode();
    q.disabled = mode === 'cards';
  });
}

function rewriteSocialLinks(snapshotUrl) {
  const encoded = encodeURIComponent(snapshotUrl);
  const line = document.getElementById('share-line');
  if (line) line.href = `https://social-plugins.line.me/lineit/share?url=${encoded}`;
  const fb = document.getElementById('share-fb');
  if (fb) fb.href = `https://www.facebook.com/sharer/sharer.php?u=${encoded}`;
  const x = document.getElementById('share-x');
  const summary = currentHighlight() || 'Tarot Reading';
  if (x) x.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(`${summary}\n\n${snapshotUrl}`)}`;
  const threads = document.getElementById('share-threads');
  if (threads) {
    const text = `${summary}\n\n${snapshotUrl}`;
    threads.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(text.slice(0, 500))}`;
  }
}

async function createSnapshotLinkFromCurrentReading(baseUrl) {
  const snapshot = buildSnapshotPlaintext();
  if (!snapshot) return baseUrl;
  const encrypted = await encryptSnapshot(snapshot);
  return withSnapshotFragment(baseUrl, encrypted);
}

function bestBaseShareUrl() {
  const fb = document.getElementById('share-fb')?.href;
  if (fb) {
    try {
      const u = new URL(fb);
      const value = u.searchParams.get('u');
      if (value) return value;
    } catch (_) {}
  }
  return location.href.split('#')[0];
}

function wrapShareGeneration() {
  const original = window.generateShareImage;
  if (typeof original !== 'function' || original.__privacySnapshotWrapped) return;
  const wrapped = async function(...args) {
    injectControls();
    const result = await original.apply(this, args);
    try {
      const mode = getSnapshotMode();
      if (mode !== 'cards') {
        const snapshotUrl = await createSnapshotLinkFromCurrentReading(bestBaseShareUrl());
        window.currentPublicShareSnapshotUrl = snapshotUrl;
        rewriteSocialLinks(snapshotUrl);
      } else {
        window.currentPublicShareSnapshotUrl = null;
      }
    } catch (error) {
      console.warn('[ShareSnapshot] encrypted share creation unavailable', error);
    }
    return result;
  };
  wrapped.__privacySnapshotWrapped = true;
  window.generateShareImage = wrapped;
}

async function loadDeckCards(deckId) {
  try {
    const response = await fetch(`/api/v1/decks/${encodeURIComponent(deckId)}`, {cache: 'no-store'});
    if (!response.ok) return [];
    const data = await response.json();
    return Array.isArray(data.cards) ? data.cards : [];
  } catch (_) {
    return [];
  }
}

function cardTitle(card) {
  if (!card) return '';
  const title = card.title;
  if (typeof title === 'string') return title;
  return title?.zh || title?.['zh-TW'] || title?.en || card.id || '';
}

function cardImage(card, deckId) {
  return card?.image || card?.main_image || card?.output || (deckId === 'leopardcat' && card?.id ? `art/renders/${card.id}.webp` : '');
}

async function renderSharedSnapshot(snapshot) {
  const fortune = document.getElementById('fortune-panel') || document.getElementById('fortune');
  if (!fortune) return;
  let host = document.getElementById('shared-reading-content');
  if (!host) {
    host = document.createElement('section');
    host.id = 'shared-reading-content';
    host.className = 'sacred-panel';
    host.style.cssText = 'margin:18px 0;padding:20px;display:grid;gap:16px';
    const chat = document.getElementById('fortune-chat-area');
    (chat || fortune).prepend(host);
  }
  const deckCards = await loadDeckCards(snapshot.deck_id || 'leopardcat');
  const cards = (snapshot.cards || []).map(spec => ({spec, card: deckCards.find(card => card.id === spec.card_id) || {id: spec.card_id}}));
  const cardHtml = cards.map(({spec, card}) => {
    const src = cardImage(card, snapshot.deck_id);
    const rotate = spec.orientation === 'reversed' ? 'transform:rotate(180deg);' : '';
    const pos = spec.position_label || spec.position || '';
    return `<div style="width:120px;text-align:center"><img src="${src}" alt="${cardTitle(card)}" style="width:100%;border-radius:10px;${rotate}"><div style="font-size:.72rem;margin-top:6px">${pos ? pos + ' · ' : ''}${cardTitle(card)}${spec.orientation === 'reversed' ? ' · 逆位' : ''}</div></div>`;
  }).join('');
  const questionHtml = snapshot.question ? `<section><div style="font-size:.72rem;opacity:.65;margin-bottom:4px">公開提問</div><div style="font-size:1.05rem;line-height:1.7">${escapeHtml(snapshot.question)}</div></section>` : '';
  const highlightHtml = snapshot.highlight ? `<section><div style="font-size:.72rem;opacity:.65;margin-bottom:4px">大師精華</div><blockquote style="margin:0;padding-left:14px;border-left:2px solid var(--color-gold,#d4af37);line-height:1.75">${escapeHtml(snapshot.highlight)}</blockquote></section>` : '';
  const answerHtml = snapshot.answer ? `<section><div style="font-size:.72rem;opacity:.65;margin-bottom:4px">大師解讀</div><div style="white-space:pre-wrap;line-height:1.8">${escapeHtml(snapshot.answer)}</div></section>` : '';
  host.innerHTML = `<div><div style="font-size:.72rem;letter-spacing:.08em;opacity:.65">SHARED READING · ${escapeHtml(snapshot.spread || '')}</div><h3 style="margin:.25rem 0 0">石虎塔羅分享占卜</h3></div>${questionHtml}<div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap">${cardHtml}</div>${highlightHtml}${answerHtml}<div style="font-size:.68rem;opacity:.58">此頁只顯示分享者主動公開的加密快照；原始私人牌局不會因此公開。</div>`;
  document.querySelectorAll('#chat-history .chat-bubble').forEach(node => {
    const text = String(node.textContent || '');
    if (text.includes('Shared reading restored') && text.includes('private question')) node.remove();
  });
  document.getElementById('fortune-chat-area')?.classList.remove('hidden');
  host.scrollIntoView({block: 'start'});
}

function escapeHtml(value) {
  return String(value || '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
}

async function restoreEncryptedSnapshotFromUrl() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ''));
  const encoded = params.get(SNAPSHOT_HASH_KEY);
  if (!encoded) return false;
  try {
    const snapshot = await decryptSnapshot(encoded);
    await renderSharedSnapshot(snapshot);
    return true;
  } catch (error) {
    console.warn('[ShareSnapshot] unable to restore encrypted share', error);
    const fortune = document.getElementById('fortune-panel');
    if (fortune) {
      const notice = document.createElement('div');
      notice.style.cssText = 'margin:12px 0;padding:12px;border:1px solid rgba(212,175,55,.25);border-radius:10px;font-size:.78rem';
      notice.textContent = error?.message === 'snapshot_expired' ? '這個分享占卜已過有效期限。' : '這個分享連結無法解密或內容已損壞。';
      fortune.prepend(notice);
    }
    return false;
  }
}

window.LeopardCatShareSnapshot = {
  buildSnapshotPlaintext,
  encryptSnapshot,
  decryptSnapshot,
  createSnapshotLinkFromCurrentReading,
};

window.addEventListener('DOMContentLoaded', () => {
  injectControls();
  wrapShareGeneration();
  restoreEncryptedSnapshotFromUrl();
});
setTimeout(() => {
  injectControls();
  wrapShareGeneration();
  restoreEncryptedSnapshotFromUrl();
}, 800);
