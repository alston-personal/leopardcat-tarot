from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'website' / 'main.js'
SERVER = ROOT / 'website' / 'fortune_server.py'
TEST = ROOT / 'website' / 'tests' / 'test_threads_share_autosplit.py'

main = MAIN.read_text(encoding='utf-8')
server = SERVER.read_text(encoding='utf-8')

old_re = "const THREADS_POST_URL_RE = /^https:\\/\\/(?:www\\.)?threads\\.(?:com|net)\\/@[^/]+\\/post\\/[A-Za-z0-9_-]+\\/?(?:[?#].*)?$/i;"
new_re = "const THREADS_POST_URL_RE = /^https:\\/\\/(?:www\\.)?threads\\.(?:com|net)\\/(?:@[^/]+\\/post\\/[A-Za-z0-9_-]+|share\\/[A-Za-z0-9_-]+)\\/?(?:[?#].*)?$/i;"
assert old_re in main
main = main.replace(old_re, new_re, 1)

# Initial modular reading and retry must follow question language, not UI locale.
needle = "            lang: getAILanguageTag()\n        } : {\n            method: 'tarot', persona: window.activePersonaId || undefined, question: q,"
assert needle in main
main = main.replace(needle, "            lang: getQuestionLanguageTag(q)\n        } : {\n            method: 'tarot', persona: window.activePersonaId || undefined, question: q,", 1)
needle2 = "            lang: getAILanguageTag()\n        };\n        resp = await fetch('/api/v1/readings',"
assert needle2 in main
main = main.replace(needle2, "            lang: getQuestionLanguageTag(q)\n        };\n        resp = await fetch('/api/v1/readings',", 1)
# Legacy follow-up path had an undefined q variable.
main = main.replace("lang: getQuestionLanguageTag(q), history: currentChatHistory", "lang: getQuestionLanguageTag(text), history: currentChatHistory", 1)

anchor = "function refreshSocialShareText() {\n"
assert anchor in main
threads_helpers = r'''const THREADS_TEXT_LIMIT = 500;

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

'''
main = main.replace(anchor, threads_helpers + anchor, 1)

# Ensure Threads links always use the handler. It will allow normal direct intent <=500 chars.
old_href = "        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;"
new_href = "        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;\n        threadsLink.onclick = window.prepareThreadsShare;"
assert old_href in main
main = main.replace(old_href, new_href, 1)
old_href2 = "        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;"
new_href2 = "        document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;\n        document.getElementById('share-threads').onclick = window.prepareThreadsShare;"
assert old_href2 in main
main = main.replace(old_href2, new_href2, 1)

# Backend: canonicalize Threads /share URLs before sending them to the governed reader.
insert_after = "THREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\n"
assert insert_after in server
helpers = r'''
THREADS_ALLOWED_HOSTS = {'threads.com','www.threads.com','threads.net','www.threads.net'}
THREADS_CANONICAL_PATH_RE = re.compile(r'/@[^/]+/post/[A-Za-z0-9_-]+/?$')
THREADS_SHARE_PATH_RE = re.compile(r'/share/[A-Za-z0-9_-]+/?$')

class ThreadsSafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in THREADS_ALLOWED_HOSTS:
            raise urllib.error.HTTPError(newurl, 403, 'threads_redirect_not_allowed', headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def canonicalize_threads_source_url(source_url):
    parsed = urllib.parse.urlsplit(str(source_url or '').strip())
    if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in THREADS_ALLOWED_HOSTS:
        raise ValueError('invalid_threads_post_url')
    if THREADS_CANONICAL_PATH_RE.fullmatch(parsed.path):
        return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ''))
    if not THREADS_SHARE_PATH_RE.fullmatch(parsed.path):
        raise ValueError('invalid_threads_post_url')
    opener = urllib.request.build_opener(ThreadsSafeRedirectHandler())
    request = urllib.request.Request(source_url, headers={
        'User-Agent': 'Mozilla/5.0 (compatible; LeopardCat-Tarot/1.0)',
        'Accept': 'text/html,application/xhtml+xml',
    })
    with opener.open(request, timeout=12) as response:
        final_url = response.geturl()
        response.read(1)
    final = urllib.parse.urlsplit(final_url)
    if final.scheme != 'https' or (final.hostname or '').lower() not in THREADS_ALLOWED_HOSTS or not THREADS_CANONICAL_PATH_RE.fullmatch(final.path):
        raise ValueError('threads_share_redirect_unresolved')
    return urllib.parse.urlunsplit((final.scheme, final.netloc, final.path, final.query, ''))
'''
server = server.replace(insert_after, insert_after + helpers, 1)

old_validation = "                parsed = urllib.parse.urlsplit(source_url)\n                allowed_hosts = {'threads.com','www.threads.com','threads.net','www.threads.net'}\n                if parsed.scheme != 'https' or (parsed.hostname or '').lower() not in allowed_hosts or not re.fullmatch(r'/@[^/]+/post/[A-Za-z0-9_-]+/?', parsed.path):\n                    raise ValueError('invalid_threads_post_url')\n                request = urllib.request.Request(\n                    THREADS_READER_URL.rstrip('/') + '/v1/threads/resolve',\n                    data=json.dumps({'url': source_url}).encode('utf-8'),"
assert old_validation in server
server = server.replace(old_validation, "                source_url = canonicalize_threads_source_url(source_url)\n                request = urllib.request.Request(\n                    THREADS_READER_URL.rstrip('/') + '/v1/threads/resolve',\n                    data=json.dumps({'url': source_url}).encode('utf-8'),", 1)

MAIN.write_text(main, encoding='utf-8')
SERVER.write_text(server, encoding='utf-8')

TEST.write_text(r'''from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = (ROOT / 'main.js').read_text(encoding='utf-8')
SERVER = (ROOT / 'fortune_server.py').read_text(encoding='utf-8')


def test_threads_share_short_url_is_accepted_and_canonicalized():
    assert "share\\/[A-Za-z0-9_-]+" in MAIN
    assert 'canonicalize_threads_source_url' in SERVER
    assert 'THREADS_SHARE_PATH_RE' in SERVER
    assert 'ThreadsSafeRedirectHandler' in SERVER
    assert 'threads_redirect_not_allowed' in SERVER
    assert "data=json.dumps({'url': source_url})" in SERVER


def test_threads_long_share_uses_native_paste_flow_not_overlong_intent():
    assert 'THREADS_TEXT_LIMIT = 500' in MAIN
    assert 'function splitThreadsText' in MAIN
    assert 'function threadsSharePlan' in MAIN
    assert 'navigator.clipboard.writeText(plan.text)' in MAIN
    assert "const blankComposer = 'https://www.threads.net/intent/post'" in MAIN
    assert 'threadsLink.onclick = window.prepareThreadsShare' in MAIN
    assert "document.getElementById('share-threads').onclick = window.prepareThreadsShare" in MAIN


def test_modular_reading_language_follows_question():
    block = MAIN[MAIN.index('window.getModularReading'):MAIN.index('window.getAIReading')]
    assert block.count('lang: getQuestionLanguageTag(q)') >= 2
    assert 'lang: getAILanguageTag()' not in block
    assert 'lang: getQuestionLanguageTag(text)' in MAIN
''', encoding='utf-8')

print('threads share/autosplit patch applied')
