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

old_server = '''old = """PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)\ndef call_master_prompt(prompt):\n"""\nnew = """PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)\nTHREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\ndef call_master_prompt(prompt):\n"""\nif old not in server:\n    raise SystemExit('server config anchor missing')\nserver = server.replace(old, new, 1)'''
new_server = '''server_config_pattern = re.compile(r"PERSONA_PUBLISHER = PersonaPublisher\\(PERSONA_ROOT\\)\\n+def call_master_prompt\\(prompt\\):")\nserver_config_new = "PERSONA_PUBLISHER = PersonaPublisher(PERSONA_ROOT)\\nTHREADS_READER_URL = load_env_value('THREADS_READER_URL') or 'http://127.0.0.1:18766'\\n\\ndef call_master_prompt(prompt):"\nserver, count = server_config_pattern.subn(server_config_new, server, count=1)\nif count != 1:\n    raise SystemExit('server config boundary missing')'''
if old_server not in s:
    raise SystemExit('server patcher block missing')
s = s.replace(old_server, new_server, 1)

needle = '''s = s.replace("lang: window.currentLang,\\n                    history: currentChatHistory", "lang: getQuestionLanguageTag(q),\\n                    history: currentChatHistory", 1)'''
replacement_legacy = needle + r'''
legacy_initial_pattern = re.compile(r"(question:\s*q,\s*\n\s*cardTitle:.*?\n\s*cardMeaning:.*?\n\s*)lang:\s*window\.currentLang", re.S)
s, _legacy_initial_count = legacy_initial_pattern.subn(lambda m: m.group(1) + "lang: getQuestionLanguageTag(q)", s, count=1)
'''
if needle not in s:
    raise SystemExit('legacy language patcher anchor missing')
s = s.replace(needle, replacement_legacy, 1)
p.write_text(s, encoding='utf-8')
