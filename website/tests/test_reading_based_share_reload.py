import json
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
    assert "'question':" not in endpoint
    assert "'reading':" not in endpoint
    assert "'session_token':" not in endpoint


def test_share_url_is_reading_based_not_single_card_based():
    assert "shareU.searchParams.set('reading', envelope.reading_id)" in JS
    assert "shareU.searchParams.set('share', envelope.share_token)" in JS
    assert "shareU.searchParams.set('card'" not in JS
    assert "shareU.searchParams.set('orientation'" not in JS
    assert 'session_token' not in JS.split('function updateSocialLinks',1)[1].split('function modularErrorMessage',1)[0]
    assert JS.count('window.currentShareReceipt || window.currentReadingEnvelope') == 2


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
