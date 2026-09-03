from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]

def test_full_master_share_is_explicit_and_question_opt_in():
    html=(ROOT/'index.html').read_text(encoding='utf-8')
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    assert 'data-share-content-mode="quote"' in html
    assert 'data-share-content-mode="full"' in html
    assert 'id="share-include-question"' in html
    assert "window.shareContentMode = 'quote'" in js
    assert 'window.shareIncludeQuestion = false' in js
    assert "window.shareContentMode !== 'full'" in js

def test_full_master_share_uses_browser_chat_without_server_persistence():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    assert 'function latestMasterInterpretation()' in js
    assert 'currentChatHistory.length - 1' in js
    assert "item?.role === 'assistant'" in js
    assert 'function buildSocialShareText' in js
    assert "parts.push(answer)" in js
    assert "window._lastQuestion" in js

def test_full_share_drives_native_and_social_text():
    js=(ROOT/'main.js').read_text(encoding='utf-8')
    assert 'buildSocialShareText(shareMsg, shareUrl)' in js
    assert 'buildSocialShareText(shareMsg, threadsShareU.toString())' in js
    assert 'text: lastShareText' in js
    assert 'window.prepareFacebookShare' in js
    assert 'navigator.clipboard?.writeText(lastShareText)' in js

def test_capability_protects_privacy_default():
    cap=json.loads((ROOT.parent/'governance/capabilities.json').read_text(encoding='utf-8'))
    c=cap['protected_capabilities']['sharing.full-master-text']['contract']
    joined=' '.join(c)
    assert 'explicit user choice' in joined
    assert 'MUST NOT introduce server-side persistence' in joined
    assert 'excluded' in joined and 'opt-in' in joined
