#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
main = ROOT / 'website' / 'main.js'
src = main.read_text(encoding='utf-8')

if 'function threadsSourceAuthorLabel(source)' in src:
    raise SystemExit('threads author patch already applied')

helper = r'''function threadsSourceAuthorLabel(source) {
    if (!source || source.type !== 'threads') return '';
    const author = (source.author && typeof source.author === 'object') ? source.author : {};
    const displayName = String(
        author.display_name || author.name || source.author_name || source.display_name || ''
    ).trim();
    let rawHandle = String(
        author.username || author.handle || source.username || source.handle || ''
    ).trim();
    if (!rawHandle && source.url) {
        try {
            const match = new URL(source.url).pathname.match(/^\/@([^/]+)\/post\//i);
            if (match) rawHandle = match[1];
        } catch (_) {}
    }
    const handle = rawHandle ? `@${rawHandle.replace(/^@+/, '')}` : '';
    if (displayName && handle && displayName.toLowerCase() !== handle.slice(1).toLowerCase()) {
        return `${displayName}（${handle}）`;
    }
    return displayName || handle;
}

'''
anchor = 'function buildSocialShareText(shareMsg, shareUrl) {'
if src.count(anchor) != 1:
    raise SystemExit(f'expected one social share builder anchor, found {src.count(anchor)}')
src = src.replace(anchor, helper + anchor, 1)

old_threads_block = '''    if (source?.type === 'threads' && source.text && source.url) {
        parts.push(`${uiText('share_threads_question_heading', '該文作者提問：')}\\n${normalizeMasterShareText(source.text)}`);
        parts.push(`${uiText('share_source_heading', '原文：')}\\n${source.url}`);
        parts.push(`${uiText('share_master_heading', '大師解讀：')}\\n${answer}`);
'''
new_threads_block = '''    if (source?.type === 'threads' && source.text && source.url) {
        const authorLabel = threadsSourceAuthorLabel(source);
        const questionHeading = authorLabel
            ? uiText('share_threads_question_heading_with_author', '原文作者 {author} 提問：', {author: authorLabel})
            : uiText('share_threads_question_heading', '原文作者提問：');
        parts.push(`${questionHeading}\\n${normalizeMasterShareText(source.text)}`);
        parts.push(`${uiText('share_source_heading', '原文：')}\\n${source.url}`);
        parts.push(`${uiText('share_master_heading', '大師解讀：')}\\n${answer}`);
'''
if src.count(old_threads_block) != 1:
    raise SystemExit('threads source share block drifted; refusing patch')
src = src.replace(old_threads_block, new_threads_block, 1)

pattern = re.compile(r'''function threadsSharePlan\(text\) \{.*?\n\}\n\nwindow\.prepareThreadsShare = async function\(event\) \{.*?\n\};''', re.S)
match = pattern.search(src)
if not match:
    raise SystemExit('threads long share functions not found')
replacement = r'''function buildThreadsPrimaryPost(text, limit = THREADS_TEXT_LIMIT) {
    const full = String(text || '').trim();
    if (full.length <= limit) return full;
    const url = String(lastShareUrl || '').trim();
    const suffix = url ? `\n\n${uiText('threads_full_reading_link', '完整解讀：')} ${url}` : '';
    const ellipsis = '…';
    const budget = Math.max(40, limit - suffix.length - ellipsis.length);
    const lead = splitThreadsText(full, budget)[0] || full.slice(0, budget);
    return `${lead.slice(0, budget).trim()}${ellipsis}${suffix}`.slice(0, limit);
}

function threadsSharePlan(text) {
    const full = String(text || '').trim();
    const chunks = splitThreadsText(full);
    const isLong = full.length > THREADS_TEXT_LIMIT;
    const primaryText = buildThreadsPrimaryPost(full);
    return {
        text: full,
        primaryText,
        chunks,
        count: chunks.length,
        isLong,
        requiresTextAttachment: isLong,
        textAttachment: isLong ? {
            plaintext: full,
            link_attachment_url: String(lastShareUrl || '').trim() || undefined
        } : null
    };
}

window.prepareThreadsShare = async function(event) {
    const link = document.getElementById('share-threads');
    if (!link || !lastShareText) return true;
    const plan = threadsSharePlan(lastShareText);
    if (!plan.isLong) return true;

    // Threads intent only supports the <=500-character primary post. Never put the
    // full long interpretation into the composer and never fall back to clipboard
    // paste. The full text is represented as a typed text-attachment capability for
    // the OAuth publishing path; until connected, the primary post remains valid and
    // links back to the reading instead of showing a negative character counter.
    event?.preventDefault?.();
    window.pendingThreadsTextAttachment = plan.textAttachment;
    const composer = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.primaryText)}`;
    window.open(composer, '_blank', 'noopener');
    return false;
};'''
src = src[:match.start()] + replacement + src[match.end():]

# Ensure direct Threads hrefs are also bounded after share text refresh/generation.
old_href = "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;"
new_href = "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildThreadsPrimaryPost(buildSocialShareText(lastShareBaseMessage, u.toString())))}`;"
if src.count(old_href) != 1:
    raise SystemExit(f'expected one refresh Threads href, found {src.count(old_href)}')
src = src.replace(old_href, new_href, 1)

old_generate = "document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;"
new_generate = "document.getElementById('share-threads').href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildThreadsPrimaryPost(threadsShareText))}`;"
if src.count(old_generate) != 1:
    raise SystemExit(f'expected one generated Threads href, found {src.count(old_generate)}')
src = src.replace(old_generate, new_generate, 1)

# The legacy helper also writes a Threads href; bound it too.
old_legacy = "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(threadsShareText)}`;"
new_legacy = "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildThreadsPrimaryPost(threadsShareText))}`;"
if src.count(old_legacy) != 1:
    raise SystemExit(f'expected one legacy Threads href, found {src.count(old_legacy)}')
src = src.replace(old_legacy, new_legacy, 1)

main.write_text(src, encoding='utf-8')

test = ROOT / 'website' / 'tests' / 'test_threads_author_long_share.py'
test.write_text(r'''from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'main.js').read_text(encoding='utf-8')


def test_threads_author_uses_metadata_and_url_handle_fallback():
    assert 'function threadsSourceAuthorLabel(source)' in JS
    assert "author.display_name || author.name || source.author_name || source.display_name" in JS
    assert "pathname.match(/^\\/@([^/]+)\\/post\\//i)" in JS
    assert "share_threads_question_heading_with_author" in JS


def test_long_threads_intent_is_bounded_and_never_manual_clipboard_fallback():
    assert 'function buildThreadsPrimaryPost(text, limit = THREADS_TEXT_LIMIT)' in JS
    assert 'requiresTextAttachment: isLong' in JS
    assert 'window.pendingThreadsTextAttachment = plan.textAttachment;' in JS
    assert "encodeURIComponent(plan.primaryText)" in JS
    block = JS[JS.index('window.prepareThreadsShare = async function'):JS.index('function refreshSocialShareText')]
    assert 'navigator.clipboard.writeText(plan.text)' not in block
    assert "threads_long_share_copied" not in block


def test_all_threads_intent_writers_use_bounded_primary_text():
    assert JS.count('buildThreadsPrimaryPost(') >= 4
    assert "encodeURIComponent(threadsShareText)}`" not in JS
    assert "encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`" not in JS
''', encoding='utf-8')

experience = ROOT / 'docs' / 'experience' / 'THREADS_LONG_SHARE_CAPABILITY.md'
experience.write_text('''# Threads long-share capability evidence\n\n## Failure signature\n\nA full Master interpretation longer than the Threads primary-post limit was copied wholesale into the composer. Real-device evidence showed a negative character counter (`-604`), forcing the user to manually cut/paste content. The share heading also omitted the source author even though the canonical Threads URL contained an `@handle`.\n\n## Falsified assumptions\n\n1. Threads intent would automatically split long text into a thread. False.\n2. Source author could be omitted when upstream reader metadata was incomplete. False: the canonical URL itself preserves an authority-preserving `@handle` fallback.\n\n## Canonical rules\n\n- Every Threads intent primary post MUST be <= 500 characters.\n- Full text MUST NOT be copied to clipboard as a hidden manual-work fallback.\n- Long text is represented as a typed `text_attachment` capability; full automatic publishing requires user-authorized Threads OAuth.\n- Source author resolution is monotonic: reader display-name/handle > canonical URL handle > generic heading.\n\n## Forbidden transitions\n\n- `full interpretation > 500` -> `intent text > 500`\n- `long share` -> `clipboard full text` -> `user manually edits/pastes`\n- `canonical source URL with @handle` -> `anonymous source heading`\n\n## Acceptance\n\n- No composer opens with a negative character budget.\n- `@handle` is preserved when available from the canonical URL.\n- OAuth publishing may later attach up to the platform-supported long-text payload without changing this bounded intent contract.\n''', encoding='utf-8')

print('threads author/long-share patch applied')
