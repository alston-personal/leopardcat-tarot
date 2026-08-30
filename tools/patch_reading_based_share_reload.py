from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]

# ---- sessions.py: private continuation token + read-only share token ----
sessions_path = root/'website/divination/sessions.py'
sessions_path.write_text(r'''from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import time
from pathlib import Path
from typing import Any

from .core import DivinationError


class ReadingSessionStore:
    """Stores only immutable symbolic state. Questions and answers are intentionally not persisted."""

    def __init__(self, db_path: str | Path, ttl_seconds: int = 86400) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS reading_sessions (
                    reading_id TEXT PRIMARY KEY,
                    token_hash TEXT NOT NULL,
                    share_token_hash TEXT,
                    method TEXT NOT NULL,
                    persona TEXT NOT NULL,
                    deck_id TEXT,
                    method_result TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    expires_at INTEGER NOT NULL
                )
                """
            )
            columns = {row[1] for row in con.execute("PRAGMA table_info(reading_sessions)")}
            if "share_token_hash" not in columns:
                con.execute("ALTER TABLE reading_sessions ADD COLUMN share_token_hash TEXT")
            con.execute("CREATE INDEX IF NOT EXISTS idx_reading_sessions_expiry ON reading_sessions(expires_at)")

    @staticmethod
    def _hash(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def purge_expired(self) -> None:
        now = int(time.time())
        with self._connect() as con:
            con.execute("DELETE FROM reading_sessions WHERE expires_at <= ?", (now,))

    def create(self, *, reading_id: str, method: str, persona: str, deck_id: str | None, method_result: dict[str, Any]) -> dict[str, Any]:
        self.purge_expired()
        token = secrets.token_urlsafe(32)
        share_token = secrets.token_urlsafe(24)
        now = int(time.time())
        expires_at = now + self.ttl_seconds
        with self._connect() as con:
            con.execute(
                "INSERT OR REPLACE INTO reading_sessions(reading_id,token_hash,share_token_hash,method,persona,deck_id,method_result,created_at,expires_at) VALUES (?,?,?,?,?,?,?,?,?)",
                (reading_id, self._hash(token), self._hash(share_token), method, persona, deck_id, json.dumps(method_result, ensure_ascii=False), now, expires_at),
            )
        return {"session_token": token, "share_token": share_token, "expires_at": expires_at}

    def _row(self, reading_id: str):
        self.purge_expired()
        with self._connect() as con:
            return con.execute(
                "SELECT token_hash,share_token_hash,method,persona,deck_id,method_result,expires_at FROM reading_sessions WHERE reading_id=?",
                (reading_id,),
            ).fetchone()

    @staticmethod
    def _public(reading_id: str, row) -> dict[str, Any]:
        return {
            "reading_id": reading_id,
            "method": row[2],
            "persona": row[3],
            "deck_id": row[4],
            "method_result": json.loads(row[5]),
            "expires_at": row[6],
        }

    def get(self, reading_id: str, token: str) -> dict[str, Any]:
        row = self._row(reading_id)
        if not row or not secrets.compare_digest(row[0], self._hash(token or "")):
            raise DivinationError("reading session not found or expired")
        return self._public(reading_id, row)

    def get_shared(self, reading_id: str, share_token: str) -> dict[str, Any]:
        row = self._row(reading_id)
        share_hash = row[1] if row else None
        if not row or not share_hash or not secrets.compare_digest(share_hash, self._hash(share_token or "")):
            raise DivinationError("shared reading not found or expired")
        return self._public(reading_id, row)
''', encoding='utf-8')

# ---- fortune_server.py ----
server_path = root/'website/fortune_server.py'
server = server_path.read_text(encoding='utf-8')
get_anchor = """        if path == '/api/v1/methods':\n            self.send_response(200)\n            self.send_header('Content-type', 'application/json; charset=utf-8')\n            self.send_header('Cache-Control', 'public, max-age=60')\n            self.end_headers()\n            self.wfile.write(json.dumps({'methods': method_catalog()}, ensure_ascii=False).encode('utf-8'))\n            return\n"""
get_insert = get_anchor + """        if path.startswith('/api/v1/readings/'):\n            reading_id = path.rsplit('/', 1)[-1]\n            params = urllib.parse.parse_qs(query)\n            share_token = (params.get('shareToken') or [''])[0]\n            try:\n                shared = SESSION_STORE.get_shared(reading_id, share_token)\n                body = {\n                    **shared,\n                    'privacy': {'question_stored': False, 'answer_stored': False, 'symbolic_state_ttl_hours': 24},\n                    'share_mode': 'symbolic-read-only',\n                }\n                self.send_response(200)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Cache-Control', 'private, no-store')\n                self.end_headers()\n                self.wfile.write(json.dumps(body, ensure_ascii=False).encode('utf-8'))\n            except DivinationError:\n                self.send_response(404)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Cache-Control', 'no-store')\n                self.end_headers()\n                self.wfile.write(json.dumps({'error':'shared_reading_not_found'}, ensure_ascii=False).encode('utf-8'))\n            return\n"""
if get_anchor not in server:
    raise SystemExit('GET methods anchor missing')
server = server.replace(get_anchor, get_insert, 1)
server = server.replace("""                    issued_token = session_token\n                    seed_fingerprint = None\n""", """                    issued_token = session_token\n                    issued_share_token = None\n                    seed_fingerprint = None\n""", 1)
server = server.replace("""                    issued_token = issued['session_token']\n                    expires_at = issued['expires_at']\n""", """                    issued_token = issued['session_token']\n                    issued_share_token = issued['share_token']\n                    expires_at = issued['expires_at']\n""", 1)
server = server.replace("'reading_id': reading_id, 'session_token': issued_token, 'expires_at': expires_at,", "'reading_id': reading_id, 'session_token': issued_token, 'share_token': issued_share_token, 'expires_at': expires_at,", 1)
server = server.replace("""                    'reading_id': reading_id,\n                    'session_token': issued_token,\n                    'expires_at': expires_at,\n""", """                    'reading_id': reading_id,\n                    'session_token': issued_token,\n                    'share_token': issued_share_token,\n                    'expires_at': expires_at,\n""", 1)
if "get_shared(reading_id, share_token)" not in server or "'share_token': issued_share_token" not in server:
    raise SystemExit('server share patch incomplete')
server_path.write_text(server, encoding='utf-8')

# ---- main.js ----
main_path = root/'website/main.js'
main = main_path.read_text(encoding='utf-8')
state_anchor = """window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck\nwindow.activeSpread = 'single'; // homepage spread selector; preserved across retries\nwindow.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic\n"""
state_insert = state_anchor + r'''
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
        cards: specs.map(spec => ({card_id: spec.card_id || spec.id, orientation: spec.orientation || 'upright', position: spec.position, position_label: spec.position_label}))
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
    window.currentReadingState = snapshot?.reading_state || buildReadingStateFromEnvelope(data);
    window.activeSpread = window.currentReadingState?.spread || window.activeSpread;
    window._lastQuestion = question;
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
'''
if state_anchor not in main:
    raise SystemExit('state anchor missing')
main = main.replace(state_anchor, state_insert, 1)

# Restore only after locale + deck are loaded.
init_anchor = """                }, 200);\n            }\n        }\n    } catch (err) {\n"""
init_repl = """                }, 200);\n            }\n        }\n        await restoreReadingAfterReload();\n    } catch (err) {\n"""
if init_anchor not in main:
    raise SystemExit('init restore anchor missing')
main = main.replace(init_anchor, init_repl, 1)

# Persist immediately after currentReadingState is composed; update once typewriter completes so chat history is included.
state_done = """    window._lastQuestion = q;\n    const pinnedArea = document.getElementById('pinned-card-area');\n"""
state_done_repl = """    window._lastQuestion = q;\n    saveReadingSnapshot(data, q);\n    const pinnedArea = document.getElementById('pinned-card-area');\n"""
if state_done not in main:
    raise SystemExit('reading state completion anchor missing')
main = main.replace(state_done, state_done_repl, 1)
callback_anchor = """        currentChatHistory.push({role:'user', content:q}, {role:'assistant', content:rawReply});\n        updateTempleStats();\n"""
callback_repl = """        currentChatHistory.push({role:'user', content:q}, {role:'assistant', content:rawReply});\n        saveReadingSnapshot(data, q);\n        updateTempleStats();\n"""
if callback_anchor not in main:
    raise SystemExit('typewriter callback anchor missing')
main = main.replace(callback_anchor, callback_repl, 1)

# Reading-based share URL, no card/orientation serialization.
legacy_share = """        // Shared deep link preserves deck + theme + card + orientation.\n        const shareU = new URL(window.location.origin + window.location.pathname);\n        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n        if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n        shareU.searchParams.set('card', currentDrawnCard.id);\n        if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');\n        const shareUrl = shareU.toString();\n"""
reading_share = """        // Reading-based deep link: deck/theme load the experience; immutable cards come from the read-only reading receipt.\n        const shareU = new URL(window.location.origin + window.location.pathname);\n        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n        if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n        const envelope = window.currentReadingEnvelope;\n        if (envelope?.reading_id && envelope?.share_token) {\n            shareU.searchParams.set('reading', envelope.reading_id);\n            shareU.searchParams.set('share', envelope.share_token);\n        }\n        const shareUrl = shareU.toString();\n"""
if legacy_share not in main:
    raise SystemExit('legacy generate share URL anchor missing')
main = main.replace(legacy_share, reading_share, 1)

legacy_social = """    const shareU = new URL(`${window.location.origin}${window.location.pathname}`);\n    if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n    if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n    shareU.searchParams.set('card', card.id);\n    if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');\n    const shareUrl = shareU.toString();\n"""
reading_social = """    const shareU = new URL(`${window.location.origin}${window.location.pathname}`);\n    if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n    if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n    const envelope = window.currentReadingEnvelope;\n    if (envelope?.reading_id && envelope?.share_token) {\n        shareU.searchParams.set('reading', envelope.reading_id);\n        shareU.searchParams.set('share', envelope.share_token);\n    }\n    const shareUrl = shareU.toString();\n"""
if legacy_social not in main:
    raise SystemExit('legacy social URL anchor missing')
main = main.replace(legacy_social, reading_social, 1)

reset_anchor = """window.resetRitual = function() {\n    currentChatHistory = [];\n"""
reset_repl = """window.resetRitual = function() {\n    clearReadingSnapshot();\n    const cleanUrl = new URL(location.href);\n    ['reading','share','card','orientation'].forEach(k => cleanUrl.searchParams.delete(k));\n    history.replaceState(null, '', cleanUrl);\n    currentChatHistory = [];\n"""
if reset_anchor not in main:
    raise SystemExit('reset anchor missing')
main = main.replace(reset_anchor, reset_repl, 1)

if "shareU.searchParams.set('card'" in main:
    raise SystemExit('card-based share serialization remains')
main_path.write_text(main, encoding='utf-8')

# ---- governance ----
cap_path = root/'governance/capabilities.json'
caps = json.loads(cap_path.read_text(encoding='utf-8'))
caps['protected_capabilities']['sharing.reading-receipt-reload'] = {
    'status':'protected','owner':'divination',
    'contract':[
        'Share URLs identify an immutable reading receipt with a dedicated read-only share token instead of serializing a single card as the source of truth.',
        'The private continuation session token must never be placed in a share URL; the share token grants only access to immutable symbolic state.',
        'Questions and AI answers remain absent from server-side persistent storage; same-tab reload continuity may keep them only in browser sessionStorage until the reading expires or the user resets.',
        'Reloading the same reading must preserve spread, complete card order, positions, and each upright/reversed orientation without redrawing.',
        'Custom decks remain resolved through the Deck Module referenced by the reading receipt.'
    ],
    'evidence':['website/divination/sessions.py','website/fortune_server.py','website/main.js','website/tests/test_reading_based_share_reload.py']
}
cap_path.write_text(json.dumps(caps,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

# ---- tests ----
test_path = root/'website/tests/test_reading_based_share_reload.py'
test_path.write_text(r'''import json
import sqlite3
from pathlib import Path

import pytest

from divination.core import DivinationError
from divination.sessions import ReadingSessionStore

ROOT=Path(__file__).resolve().parents[2]
JS=(ROOT/'website/main.js').read_text(encoding='utf-8')
SERVER=(ROOT/'website/fortune_server.py').read_text(encoding='utf-8')
CAP=json.loads((ROOT/'governance/capabilities.json').read_text(encoding='utf-8'))


def test_session_store_issues_separate_readonly_share_token(tmp_path):
    store=ReadingSessionStore(tmp_path/'r.sqlite3',ttl_seconds=60)
    issued=store.create(reading_id='r1',method='tarot',persona='leopardcat',deck_id='deck-x',method_result={'spread':'three_card','cards':[{'card_id':'a'},{'card_id':'b'},{'card_id':'c'}]})
    assert issued['session_token'] != issued['share_token']
    private=store.get('r1',issued['session_token'])
    shared=store.get_shared('r1',issued['share_token'])
    assert private['method_result']==shared['method_result']
    with pytest.raises(DivinationError): store.get('r1',issued['share_token'])
    with pytest.raises(DivinationError): store.get_shared('r1',issued['session_token'])


def test_existing_database_migrates_share_token_column(tmp_path):
    db=tmp_path/'old.sqlite3'
    with sqlite3.connect(db) as con:
        con.execute('CREATE TABLE reading_sessions (reading_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, method TEXT NOT NULL, persona TEXT NOT NULL, deck_id TEXT, method_result TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL)')
    ReadingSessionStore(db)
    with sqlite3.connect(db) as con:
        cols={row[1] for row in con.execute('PRAGMA table_info(reading_sessions)')}
    assert 'share_token_hash' in cols


def test_public_shared_reading_api_is_symbolic_only():
    assert "path.startswith('/api/v1/readings/')" in SERVER
    assert 'SESSION_STORE.get_shared(reading_id, share_token)' in SERVER
    assert "'share_mode': 'symbolic-read-only'" in SERVER
    endpoint=SERVER.split("if path.startswith('/api/v1/readings/'):",1)[1].split("if path.startswith('/api/v1/manage/decks/'):",1)[0]
    assert 'question' not in endpoint
    assert 'answer' not in endpoint


def test_share_url_is_reading_based_not_single_card_based():
    assert "shareU.searchParams.set('reading', envelope.reading_id)" in JS
    assert "shareU.searchParams.set('share', envelope.share_token)" in JS
    assert "shareU.searchParams.set('card'" not in JS
    assert "shareU.searchParams.set('orientation'" not in JS
    assert 'session_token' not in JS.split('function updateSocialLinks',1)[1].split('function modularErrorMessage',1)[0]


def test_reload_snapshot_is_session_scoped_and_preserves_full_reading_state():
    assert "const READING_SNAPSHOT_KEY = 'leopardcat.current-reading.v1'" in JS
    assert 'sessionStorage.setItem(READING_SNAPSHOT_KEY' in JS
    assert 'async function restoreReadingAfterReload()' in JS
    assert 'buildReadingStateFromEnvelope(data)' in JS
    assert "cards: specs.map(spec =>" in JS
    assert "await restoreReadingAfterReload();" in JS
    assert "clearReadingSnapshot();" in JS


def test_governance_protects_reading_receipt_reload():
    c=CAP['protected_capabilities']['sharing.reading-receipt-reload']
    assert c['status']=='protected'
    assert any('read-only share token' in x for x in c['contract'])
    assert any('sessionStorage' in x for x in c['contract'])
''',encoding='utf-8')
print('reading-based share + reload patch applied')
