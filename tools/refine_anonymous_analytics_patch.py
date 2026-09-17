from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if text.count(old) != 1:
        raise SystemExit(f'anchor mismatch in {path}: {text.count(old)} matches')
    path.write_text(text.replace(old, new, 1), encoding='utf-8')

analytics = Path('website/divination/analytics.py')
decision_line = '        ("decision", ("哪個", "二選一", "兩個選擇", "選擇 a", "選擇 b", "比較", "該選", "vs", " or ", "which", "choose", "decision", "elegir", "decisión", "どちら", "選ぶ", "선택")),\n'
replace_once(analytics, decision_line, '')
replace_once(
    analytics,
    '    keyword_groups = (\n        ("money",',
    '    keyword_groups = (\n' + decision_line + '        ("money",'
)

tests = Path('website/tests/test_anonymous_reading_analytics.py')
replace_once(
    tests,
    "        self.assertEqual(classify_question('Should I take job A or B?', {'spread_plan': {'intent': 'decision'}}), 'career_study')",
    "        self.assertEqual(classify_question('Should I take job A or B?', {'spread_plan': {'intent': 'decision'}}), 'decision')"
)

main = Path('website/main.js')
anchor = "document.addEventListener('DOMContentLoaded', initStandaloneUpdateControls);\n"
visit = """document.addEventListener('DOMContentLoaded', initStandaloneUpdateControls);\n\nfunction recordAnonymousVisitOnce() {\n    const key = 'leopardcat.visit-recorded.v1';\n    try {\n        if (sessionStorage.getItem(key) === '1') return;\n        sessionStorage.setItem(key, '1');\n    } catch (_) {}\n    fetch('/api/v1/analytics/visit', { method: 'POST', keepalive: true }).catch(() => {});\n}\n\ndocument.addEventListener('DOMContentLoaded', recordAnonymousVisitOnce);\n"""
replace_once(main, anchor, visit)

server = Path('website/fortune_server.py')
server_text = server.read_text(encoding='utf-8')
post_anchor = "    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n"
post_new = """    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n        if path == '/api/v1/analytics/visit':\n            update_stats(divination=False)\n            self._send_api_json(200, {'recorded': True})\n            return\n"""
if server_text.count(post_anchor) != 1:
    raise SystemExit(f'do_POST anchor mismatch: {server_text.count(post_anchor)}')
server.write_text(server_text.replace(post_anchor, post_new, 1), encoding='utf-8')

print('anonymous analytics refinements applied')
