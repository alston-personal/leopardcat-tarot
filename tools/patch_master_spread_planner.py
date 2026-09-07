from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 exact match, got {count}')
    return text.replace(old, new, 1)


def patch_server() -> None:
    p = Path('website/fortune_server.py')
    s = p.read_text(encoding='utf-8')
    s = replace_once(
        s,
        'from divination.threads_publishing import ThreadsPublishingService, ThreadsPublishingError\n',
        'from divination.threads_publishing import ThreadsPublishingService, ThreadsPublishingError\nfrom divination.tarot import plan_spread, spread_catalog\n',
        'server tarot planner import',
    )
    old_catalog = """            'spreads': [\n                {'id':'single','name':'單張指引','card_count':1},\n                {'id':'three_card','name':'過去・現在・未來','card_count':3},\n                {'id':'decision','name':'選擇題','card_count':3},\n            ],\n"""
    s = replace_once(s, old_catalog, "            'spreads': spread_catalog(),\n", 'server spread catalog')
    marker = """    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n"""
    addition = """    def do_POST(self):\n        path = self.path.split('?', 1)[0]\n        if path == '/api/v1/spread-plan':\n            content_length = int(self.headers.get('Content-Length', 0))\n            if content_length <= 0 or content_length > 16 * 1024:\n                self._send_api_json(413, {'error': 'spread_plan_payload_too_large'})\n                return\n            try:\n                payload = json.loads(self.rfile.read(content_length).decode('utf-8') or '{}')\n                question = str(payload.get('question') or '').strip()\n                if not question or len(question) > 4000:\n                    raise ValueError('spread_plan_question_invalid')\n                self._send_api_json(200, {'plan': plan_spread(question)})\n            except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:\n                self._send_api_json(400, {'error': str(exc) or 'spread_plan_payload_invalid'})\n            return\n"""
    s = replace_once(s, marker, addition, 'server spread plan endpoint')
    p.write_text(s, encoding='utf-8')


def patch_index() -> None:
    p = Path('website/index.html')
    s = p.read_text(encoding='utf-8')
    old = """                                    <option value=\"auto\" selected>自動</option>\n                                    <option value=\"single\" data-i18n=\"common.spread_single_short\">單牌</option>\n                                    <option value=\"three_card\" data-i18n=\"common.spread_three_short\">三牌</option>\n"""
    new = """                                    <option value=\"auto\" selected>大師自動選牌陣</option>\n                                    <option value=\"single\" data-card-count=\"1\">單張指引</option>\n                                    <option value=\"clarifier\" data-card-count=\"1\">補充牌</option>\n                                    <option value=\"three_card\" data-card-count=\"3\">時間流三牌</option>\n                                    <option value=\"situation_advice\" data-card-count=\"3\">現況・阻礙・建議</option>\n                                    <option value=\"decision\" data-card-count=\"3\">選擇分析</option>\n                                    <option value=\"relationship\" data-card-count=\"5\">關係五牌</option>\n                                    <option value=\"career\" data-card-count=\"5\">職涯五牌</option>\n                                    <option value=\"path\" data-card-count=\"5\">道路五牌</option>\n                                    <option value=\"celtic_cross\" data-card-count=\"10\">凱爾特十字</option>\n"""
    s = replace_once(s, old, new, 'index spread options')
    p.write_text(s, encoding='utf-8')


def patch_main() -> None:
    p = Path('website/main.js')
    s = p.read_text(encoding='utf-8')
    s = replace_once(
        s,
        "window.effectiveSpread = null; // concrete spread selected for the current reading\n",
        "window.effectiveSpread = null; // concrete spread selected by the canonical server planner\nwindow.currentSpreadPlan = null; // product-safe planner metadata; never re-plan downstream\n",
        'main spread state',
    )

    pattern = re.compile(
        r"function automaticSpreadForQuestion\(question\) \{.*?\n\}\n\nfunction resolvedSpreadForQuestion\(question\) \{.*?\n\}\n\nfunction requiredDrawCount\(\) \{.*?\n\}\n",
        re.S,
    )
    replacement = """async function fetchCanonicalSpreadPlan(question) {\n    const response = await fetch('/api/v1/spread-plan', {\n        method: 'POST',\n        headers: {'Content-Type': 'application/json'},\n        body: JSON.stringify({question: String(question || '').trim()})\n    });\n    const payload = await response.json().catch(() => ({}));\n    const plan = payload?.plan;\n    if (!response.ok || !plan?.spread || !Number.isInteger(Number(plan.card_count))) {\n        throw new Error(payload?.error || 'SPREAD_PLAN_UNAVAILABLE');\n    }\n    return {...plan, card_count: Number(plan.card_count)};\n}\n\nfunction resolvedSpreadForQuestion() {\n    const resolved = window.activeSpread || 'auto';\n    window.effectiveSpread = resolved === 'auto' ? null : resolved;\n    if (resolved !== 'auto') window.currentSpreadPlan = null;\n    return resolved;\n}\n\nfunction requiredDrawCount() {\n    if (window.currentSpreadPlan?.spread === window.effectiveSpread) {\n        return Number(window.currentSpreadPlan.card_count) || 1;\n    }\n    const selected = document.getElementById('spread-select')?.selectedOptions?.[0];\n    const explicitCount = Number(selected?.dataset?.cardCount || 0);\n    return explicitCount > 0 ? explicitCount : 1;\n}\n"""
    s, count = pattern.subn(replacement, s, count=1)
    if count != 1:
        raise RuntimeError(f'main planner block: expected 1 match, got {count}')

    s = replace_once(
        s,
        'window.shuffleManualDeck = function() {\n',
        'window.shuffleManualDeck = async function() {\n',
        'manual shuffle async',
    )
    old_manual = """    if (!q) return alert(uiText('err_empty_question', 'Please enter your question first.'));\n    resolvedSpreadForQuestion(q);\n    const seed = freshShuffleSeed();\n"""
    new_manual = """    if (!q) return alert(uiText('err_empty_question', 'Please enter your question first.'));\n    try {\n        if ((window.activeSpread || 'auto') === 'auto') {\n            const plan = await fetchCanonicalSpreadPlan(q);\n            window.currentSpreadPlan = plan;\n            window.effectiveSpread = plan.spread;\n        } else {\n            resolvedSpreadForQuestion();\n        }\n    } catch (error) {\n        console.warn('[Spread planner] unavailable', error);\n        return alert(uiText('err_spread_plan_unavailable', '大師暫時無法決定牌陣，請稍後再試或手動選擇牌陣。'));\n    }\n    const seed = freshShuffleSeed();\n"""
    s = replace_once(s, old_manual, new_manual, 'manual planner call')

    s = replace_once(
        s,
        'spread: resolvedSpreadForQuestion(q),\n',
        "spread: window.drawMode === 'manual' ? (window.effectiveSpread || window.activeSpread || 'auto') : (window.activeSpread || 'auto'),\n",
        'reading payload spread authority',
    )

    old_picker = "window.activeSpread = ['auto', 'single', 'three_card'].includes(spread) ? spread : 'auto';\n            window.effectiveSpread = null;"
    new_picker = "const allowed = new Set([...selectEl.options].map(option => option.value));\n            window.activeSpread = allowed.has(spread) ? spread : 'auto';\n            window.effectiveSpread = null;\n            window.currentSpreadPlan = null;"
    s = replace_once(s, old_picker, new_picker, 'spread picker whitelist')

    s = s.replace(
        'window.currentReadingState = null;\n    window.currentQuestionSource = null;',
        'window.currentReadingState = null;\n    window.currentSpreadPlan = null;\n    window.effectiveSpread = null;\n    window.currentQuestionSource = null;',
        1,
    )
    p.write_text(s, encoding='utf-8')


if __name__ == '__main__':
    patch_server()
    patch_index()
    patch_main()
    print('master_spread_planner_patch=PASS')
