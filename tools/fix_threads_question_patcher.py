from pathlib import Path

p = Path('tools/apply_threads_question_language.py')
s = p.read_text(encoding='utf-8')
start = s.index('old = """function buildSocialShareText(shareMsg, shareUrl) {')
end = s.index("\n# Resolve a Threads URL before charging mana/drawing.", start)
replacement = r'''share_pattern = re.compile(r"function buildSocialShareText\(shareMsg, shareUrl\) \{.*?\n\}\n\nfunction syncShareContentControls", re.S)
share_new = """function buildSocialShareText(shareMsg, shareUrl) {
    if (window.shareContentMode !== 'full') return `${shareMsg} ${shareUrl}`;
    const answer = latestMasterInterpretation();
    if (!answer) return `${shareMsg} ${shareUrl}`;
    const source = window.currentQuestionSource;
    const parts = [];
    if (source?.type === 'threads' && source.text && source.url) {
        parts.push(`${uiText('share_threads_question_heading', '該文作者提問：')}\\n${normalizeMasterShareText(source.text)}`);
        parts.push(`${uiText('share_source_heading', '原文：')}\\n${source.url}`);
        parts.push(`${uiText('share_master_heading', '大師解讀：')}\\n${answer}`);
    } else {
        if (window.shareIncludeQuestion && window._lastQuestion) {
            parts.push(`${uiText('share_question_heading', '我的提問')}\\n${normalizeMasterShareText(window._lastQuestion)}`);
        }
        parts.push(answer);
    }
    parts.push(shareUrl);
    return parts.join('\\n\\n');
}

function syncShareContentControls"""
s, count = share_pattern.subn(lambda _: share_new, s, count=1)
if count != 1:
    raise SystemExit('share function boundary missing')
'''
s = s[:start] + replacement + s[end:]
p.write_text(s, encoding='utf-8')
