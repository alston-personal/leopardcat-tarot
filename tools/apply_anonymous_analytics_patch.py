from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / 'website' / 'fortune_server.py'
MAIN = ROOT / 'website' / 'main.js'


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly one anchor, found {count}')
    return text.replace(old, new, 1)


server = SERVER.read_text(encoding='utf-8')
server = replace_once(
    server,
    "from divination.tarot import plan_spread, spread_catalog\n",
    "from divination.tarot import plan_spread, spread_catalog\nfrom divination.analytics import ReadingAnalyticsStore, classify_question, normalize_source\n",
    'analytics import',
)
server = replace_once(
    server,
    "SESSION_STORE = ReadingSessionStore(os.path.join(DATA_DIR, 'reading_sessions.sqlite3'), ttl_seconds=86400)\n",
    "SESSION_STORE = ReadingSessionStore(os.path.join(DATA_DIR, 'reading_sessions.sqlite3'), ttl_seconds=86400)\nANALYTICS_STORE = ReadingAnalyticsStore(os.path.join(DATA_DIR, 'analytics.sqlite3'))\n",
    'analytics store init',
)

old_stats = '''def update_stats(divination=False):\n    try:\n        if not os.path.exists('stats.json'):\n            with open('stats.json', 'w') as f: \n                json.dump({"total_visitors": 2026, "total_divinations": 888}, f)\n        \n        with open('stats.json', 'r+') as sf:\n            sdata = json.load(sf)\n            if divination:\n                sdata['total_divinations'] = sdata.get('total_divinations', 0) + 1\n            else:\n                sdata['total_visitors'] = sdata.get('total_visitors', 0) + 1\n            sf.seek(0)\n            json.dump(sdata, sf)\n            sf.truncate()\n            return sdata\n    except Exception as e:\n        log(f"Error updating stats: {e}")\n        return {"total_visitors": 2026, "total_divinations": 888, "error": str(e)}\n'''
new_stats = '''def _ensure_stats_file():\n    if not os.path.exists('stats.json'):\n        with open('stats.json', 'w') as f:\n            json.dump({"total_visitors": 2026, "total_divinations": 888}, f)\n\ndef read_stats():\n    try:\n        _ensure_stats_file()\n        with open('stats.json', 'r') as sf:\n            return json.load(sf)\n    except Exception as e:\n        log(f"Error reading stats: {e}")\n        return {"total_visitors": 2026, "total_divinations": 888, "error": str(e)}\n\ndef update_stats(divination=False):\n    try:\n        _ensure_stats_file()\n        with open('stats.json', 'r+') as sf:\n            sdata = json.load(sf)\n            if divination:\n                sdata['total_divinations'] = sdata.get('total_divinations', 0) + 1\n            else:\n                sdata['total_visitors'] = sdata.get('total_visitors', 0) + 1\n            sf.seek(0)\n            json.dump(sdata, sf)\n            sf.truncate()\n            return sdata\n    except Exception as e:\n        log(f"Error updating stats: {e}")\n        return {"total_visitors": 2026, "total_divinations": 888, "error": str(e)}\n'''
server = replace_once(server, old_stats, new_stats, 'stats refactor')
server = replace_once(
    server,
    "        if path == '/api/stats':\n            sdata = update_stats(divination=False)\n",
    "        if path == '/api/v1/analytics/summary':\n            analytics_token = load_env_value('LEOPARDCAT_ANALYTICS_TOKEN')\n            supplied_token = self.headers.get('X-Analytics-Token', '')\n            if not analytics_token:\n                self._send_api_json(404, {'error': 'analytics_not_configured'})\n                return\n            if not supplied_token or not secrets.compare_digest(supplied_token, analytics_token):\n                self._send_api_json(403, {'error': 'analytics_denied'})\n                return\n            params = urllib.parse.parse_qs(query)\n            try:\n                days = int((params.get('days') or ['30'])[0])\n            except ValueError:\n                days = 30\n            self._send_api_json(200, ANALYTICS_STORE.summary(days=days))\n            return\n        if path == '/api/stats':\n            sdata = read_stats()\n",
    'stats get and analytics summary',
)

new_reading_anchor = "                    expires_at = issued['expires_at']\n\n                if history:\n"
new_reading_replacement = "                    expires_at = issued['expires_at']\n                    analytics_meta = req_data.get('analytics') if isinstance(req_data.get('analytics'), dict) else {}\n                    analytics_source = normalize_source(analytics_meta.get('source'))\n                    analytics_category = classify_question(question, method_result)\n                    try:\n                        ANALYTICS_STORE.record_reading(\n                            source=analytics_source,\n                            question_category=analytics_category,\n                            method=method_id,\n                            method_result=method_result,\n                            language=lang,\n                            persona_id=persona_id,\n                        )\n                    except Exception as analytics_error:\n                        log(f'Anonymous analytics write failed: {analytics_error}')\n                    update_stats(divination=True)\n\n                if history:\n"
server = replace_once(server, new_reading_anchor, new_reading_replacement, 'initial reading analytics')
server = replace_once(
    server,
    "                update_stats(divination=True)\n                capsule = build_capsule(\n",
    "                capsule = build_capsule(\n",
    'remove follow-up overcount',
)
SERVER.write_text(server, encoding='utf-8')

main = MAIN.read_text(encoding='utf-8')
main = replace_once(
    main,
    "            ...(drawOptions.seed ? {seed: drawOptions.seed} : {}),\n            lang: getQuestionLanguageTag(q)\n",
    "            ...(drawOptions.seed ? {seed: drawOptions.seed} : {}),\n            analytics: { source: window.currentQuestionSource ? 'threads' : 'direct' },\n            lang: getQuestionLanguageTag(q)\n",
    'frontend source enum',
)
MAIN.write_text(main, encoding='utf-8')

print('anonymous analytics patch applied')
