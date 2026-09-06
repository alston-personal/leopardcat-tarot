from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / 'website' / 'main.js'
TEST = ROOT / 'website' / 'tests' / 'test_threads_first_post_preview.py'

src = MAIN.read_text(encoding='utf-8')
old = '''function threadsSharePlan(text) {
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
new = '''function fitThreadsLeadWithUrls(questionText, sourceUrl, readingUrl, limit = THREADS_TEXT_LIMIT) {
    const questionHeading = uiText('share_threads_question_heading', '該文作者提問：');
    const sourceHeading = uiText('share_source_heading', '原文：');
    const masterHeading = uiText('share_master_heading', '大師解讀：');
    const fixed = [
        sourceUrl ? `${sourceHeading}\\n${sourceUrl}` : '',
        masterHeading,
        readingUrl
    ].filter(Boolean).join('\\n\\n');
    const prefix = questionText ? `${questionHeading}\\n` : '';
    const separator = questionText ? '\\n\\n' : '';
    const room = Math.max(0, limit - fixed.length - prefix.length - separator.length);
    let question = String(questionText || '').trim();
    if (question.length > room) {
        question = `${question.slice(0, Math.max(0, room - 1)).trimEnd()}…`;
    }
    return [question ? `${prefix}${question}` : '', fixed].filter(Boolean).join('\\n\\n').slice(0, limit);
}

function threadsSharePlan(text, readingUrl = lastShareUrl) {
    const fullText = String(text || '').trim();
    const chunks = splitThreadsText(fullText);
    if (chunks.length <= 1) {
        return { text: fullText, chunks, count: chunks.length, requiresPaste: false, firstPost: fullText, remainderText: '' };
    }

    const source = window.currentQuestionSource;
    const answer = latestMasterInterpretation();
    let firstPost = '';
    let remainderText = '';

    if (window.shareContentMode === 'full' && answer) {
        if (source?.type === 'threads' && source.text) {
            firstPost = fitThreadsLeadWithUrls(source.text, source.url || '', readingUrl || '');
        } else {
            const question = window.shareIncludeQuestion ? normalizeMasterShareText(window._lastQuestion || '') : '';
            const heading = uiText('share_master_heading', '大師解讀：');
            const lead = question ? `${uiText('share_question_heading', '我的提問')}\\n${question}\\n\\n${heading}` : heading;
            const suffix = readingUrl ? `\\n\\n${readingUrl}` : '';
            const room = Math.max(0, THREADS_TEXT_LIMIT - suffix.length);
            firstPost = `${lead.slice(0, room)}${suffix}`;
        }
        remainderText = answer;
    } else {
        const url = String(readingUrl || '').trim();
        const withoutUrl = url ? fullText.replace(url, '').trim() : fullText;
        const suffix = url ? `\\n\\n${url}` : '';
        const room = Math.max(0, THREADS_TEXT_LIMIT - suffix.length);
        firstPost = `${withoutUrl.slice(0, room).trim()}${suffix}`.trim();
        remainderText = fullText.slice(firstPost.length).trim();
    }

    const remainderChunks = splitThreadsText(remainderText);
    return {
        text: fullText,
        chunks: [firstPost, ...remainderChunks].filter(Boolean),
        count: 1 + remainderChunks.length,
        requiresPaste: remainderChunks.length > 0,
        firstPost,
        remainderText
    };
}

window.prepareThreadsShare = async function(event) {
    const link = document.getElementById('share-threads');
    if (!link || !lastShareText) return true;
    const readingUrl = window._threadsShareUrl || lastShareUrl;
    const plan = threadsSharePlan(lastShareText, readingUrl);
    if (!plan.requiresPaste) return true;
    event?.preventDefault?.();
    try {
        await navigator.clipboard.writeText(plan.remainderText);
    } catch (_) {
        return true;
    }
    const firstComposer = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.firstPost)}`;
    window.open(firstComposer, '_blank', 'noopener');
    const message = uiText(
        'threads_long_share_copied',
        '第一則已帶入塔羅圖卡連結；剩餘大師解讀已複製。發布第一則後，在回覆中貼上即可由 Threads 自動分串（約 {count} 則）。',
        {count: plan.count}
    );
    setTimeout(() => alert(message), 120);
    return false;
};
'''
if old not in src:
    raise SystemExit('target Threads share block not found')
src = src.replace(old, new)
old2 = '''        const u = new URL(lastShareUrl);
        u.searchParams.set('preview', String(Date.now()));
        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(buildSocialShareText(lastShareBaseMessage, u.toString()))}`;
        threadsLink.onclick = window.prepareThreadsShare;
'''
new2 = '''        const u = new URL(lastShareUrl);
        u.searchParams.set('preview', String(Date.now()));
        window._threadsShareUrl = u.toString();
        const threadsText = buildSocialShareText(lastShareBaseMessage, window._threadsShareUrl);
        const plan = threadsSharePlan(threadsText, window._threadsShareUrl);
        threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.firstPost || threadsText)}`;
        threadsLink.onclick = window.prepareThreadsShare;
'''
if old2 not in src:
    raise SystemExit('target refresh Threads block not found')
src = src.replace(old2, new2)
MAIN.write_text(src, encoding='utf-8')

TEST.write_text('''from pathlib import Path\n\nROOT = Path(__file__).resolve().parents[1]\nMAIN = (ROOT / "main.js").read_text(encoding="utf-8")\n\ndef test_threads_long_share_keeps_reading_url_in_first_post():\n    assert "fitThreadsLeadWithUrls" in MAIN\n    assert "firstPost" in MAIN\n    assert "window._threadsShareUrl" in MAIN\n    assert "threadsLink.href = `https://www.threads.net/intent/post?text=${encodeURIComponent(plan.firstPost || threadsText)}`" in MAIN\n\ndef test_threads_long_share_only_copies_remainder():\n    assert "navigator.clipboard.writeText(plan.remainderText)" in MAIN\n    assert "navigator.clipboard.writeText(plan.text)" not in MAIN\n    assert "第一則已帶入塔羅圖卡連結" in MAIN\n\ndef test_threads_first_post_preserves_source_and_master_headings():\n    assert "share_threads_question_heading" in MAIN\n    assert "share_source_heading" in MAIN\n    assert "share_master_heading" in MAIN\n    assert "readingUrl" in MAIN\n''', encoding='utf-8')
print('threads_first_post_preview_patch=PASS')
