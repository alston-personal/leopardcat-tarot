from pathlib import Path
import re

# decks.py: add backward-compatible deck-owned default theme.
p = Path('website/divination/decks.py')
s = p.read_text(encoding='utf-8')
s = s.replace('_SAFE_PERSONA_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")', '_SAFE_PERSONA_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")\n_SAFE_THEME_ID = re.compile(r"^[a-z0-9][a-z0-9-]{1,63}$")')
s = s.replace('    default_persona: str = "master"\n', '    default_persona: str = "master"\n    default_theme: str = "minimal-light"\n')
s = s.replace('                "leopardcat",\n            )', '                "leopardcat",\n                "leopardcat",\n            )', 1)
needle = '''        default_persona = str(data.get("default_persona") or "master").strip().lower()\n        if not _SAFE_PERSONA_ID.fullmatch(default_persona):\n            default_persona = "master"\n'''
repl = needle + '''        default_theme = str(data.get("default_theme") or "minimal-light").strip().lower()\n        if not _SAFE_THEME_ID.fullmatch(default_theme):\n            default_theme = "minimal-light"\n'''
assert needle in s
s = s.replace(needle, repl, 1)
s = s.replace('            default_persona=default_persona,\n        )', '            default_persona=default_persona,\n            default_theme=default_theme,\n        )', 1)
s = s.replace('            "default_persona": d.default_persona,\n', '            "default_persona": d.default_persona,\n            "default_theme": d.default_theme,\n', 1)
p.write_text(s, encoding='utf-8')

# publishing.py: persist/return/manage optional default_theme; old clients remain minimal-light.
p = Path('website/divination/publishing.py')
s = p.read_text(encoding='utf-8')
needle = '        default_persona = _clean_text(payload.get("persona"), 64).lower() or "master"\n'
assert needle in s
s = s.replace(needle, needle + '        default_theme = _clean_text(payload.get("theme"), 64).lower() or "minimal-light"\n', 1)
s = s.replace('        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", default_persona):\n            raise DivinationError("無效的解牌 Persona")\n', '        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", default_persona):\n            raise DivinationError("無效的解牌 Persona")\n        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", default_theme):\n            raise DivinationError("無效的牌組主題")\n', 1)
s = s.replace('                "default_persona": default_persona,\n                "card_count": len(saved_cards),', '                "default_persona": default_persona,\n                "default_theme": default_theme,\n                "card_count": len(saved_cards),', 1)
s = s.replace('            "default_persona": default_persona,\n            "share_path":', '            "default_persona": default_persona,\n            "default_theme": default_theme,\n            "share_path":', 1)
s = s.replace('            "default_persona": data.get("default_persona", "master"),\n            "reversals":', '            "default_persona": data.get("default_persona", "master"),\n            "default_theme": data.get("default_theme", "minimal-light"),\n            "reversals":', 1)
needle = '''        if "persona" in payload:\n            persona = _clean_text(payload.get("persona"), 64).lower()\n            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", persona):\n                raise DivinationError("無效的解牌 Persona")\n            data["default_persona"] = persona\n'''
assert needle in s
s = s.replace(needle, needle + '''        if "theme" in payload:\n            theme = _clean_text(payload.get("theme"), 64).lower()\n            if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,63}", theme):\n                raise DivinationError("無效的牌組主題")\n            data["default_theme"] = theme\n''', 1)
p.write_text(s, encoding='utf-8')

# fortune_server.py: validate a referenced theme exists before persisting it.
p = Path('website/fortune_server.py')
s = p.read_text(encoding='utf-8')
needle = '''            if path.startswith('/api/v1/manage/decks/'):\n                deck_id = path.rsplit('/', 1)[-1]\n                if 'persona' in payload:\n'''
assert needle in s
s = s.replace(needle, '''            if path.startswith('/api/v1/manage/decks/'):\n                deck_id = path.rsplit('/', 1)[-1]\n                if 'theme' in payload:\n                    THEMES.get(str(payload.get('theme') or '').strip())\n                if 'persona' in payload:\n''', 1)
needle = '''                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                persona_id = str(payload.get('persona') or 'master').strip()\n                DIVINATION_ENGINE.personas.get(persona_id)\n                result = DECK_PUBLISHER.publish(payload)\n'''
assert needle in s
s = s.replace(needle, '''                payload = json.loads(self.rfile.read(content_length).decode('utf-8'))\n                persona_id = str(payload.get('persona') or 'master').strip()\n                DIVINATION_ENGINE.personas.get(persona_id)\n                theme_id = str(payload.get('theme') or 'minimal-light').strip()\n                THEMES.get(theme_id)\n                payload['theme'] = theme_id\n                result = DECK_PUBLISHER.publish(payload)\n''', 1)
p.write_text(s, encoding='utf-8')

# creator.js: make chosen theme part of deck ownership; explicit share URL still carries it.
p = Path('website/public/creator.js')
s = p.read_text(encoding='utf-8')
needle = '          persona: selectedPersonaId,\n          cards\n'
assert needle in s
s = s.replace(needle, '          persona: selectedPersonaId,\n          theme: selectedThemeId,\n          cards\n', 1)
p.write_text(s, encoding='utf-8')

# main.js: URL theme stays highest priority; otherwise custom deck metadata wins once loaded.
p = Path('website/main.js')
s = p.read_text(encoding='utf-8')
needle = "window.activeThemeId = new URLSearchParams(window.location.search).get('theme') || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');"
assert needle in s
s = s.replace(needle, "window.explicitThemeId = new URLSearchParams(window.location.search).get('theme');\nwindow.activeThemeId = window.explicitThemeId || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');", 1)
needle = '''        const deck = await resp.json();\n        window.activeDeckInfo = deck;\n        document.title = `${deck.name}・線上塔羅占卜`;\n'''
assert needle in s
s = s.replace(needle, '''        const deck = await resp.json();\n        window.activeDeckInfo = deck;\n        if (!window.explicitThemeId && deck.default_theme && deck.default_theme !== window.activeThemeId) {\n            window.activeThemeId = deck.default_theme;\n            await window.applyTheme(deck.default_theme);\n        }\n        document.title = `${deck.name}・線上塔羅占卜`;\n''', 1)
p.write_text(s, encoding='utf-8')

# read.js: discover deck-owned theme only when URL does not explicitly override it.
p = Path('website/public/read.js')
s = p.read_text(encoding='utf-8')
needle = '''  async function loadExperienceIdentity(){\n    const defaultTheme=state.deck==='leopardcat'?'leopardcat':'minimal-light';\n    state.theme=state.theme||defaultTheme;\n    try{\n'''
assert needle in s
s = s.replace(needle, '''  async function loadExperienceIdentity(){\n    const defaultTheme=state.deck==='leopardcat'?'leopardcat':'minimal-light';\n    if(!state.theme && state.deck!=='leopardcat'){\n      try{\n        const deckResp=await fetch(`/api/v1/decks/${encodeURIComponent(state.deck)}`,{cache:'no-store'});\n        if(deckResp.ok){const deck=await deckResp.json();state.theme=deck.default_theme||defaultTheme;}\n      }catch(_){}\n    }\n    state.theme=state.theme||defaultTheme;\n    try{\n''', 1)
p.write_text(s, encoding='utf-8')

# Focused regression tests.
t = Path('website/tests/test_custom_deck_theme_ownership.py')
t.write_text('''import json\nfrom pathlib import Path\n\nfrom divination.decks import DeckRegistry\nfrom divination.publishing import DeckPublisher\n\n\ndef _card():\n    return {\"id\": \"x\", \"title\": {\"zh\": \"X\"}, \"meanings\": {\"upright\": \"u\", \"reversed\": \"r\"}, \"image\": \"/x.webp\"}\n\n\ndef test_old_custom_manifest_defaults_theme_without_migration(tmp_path):\n    builtin = tmp_path / \"manifest.json\"\n    builtin.write_text(json.dumps([_card()]), encoding=\"utf-8\")\n    root = tmp_path / \"custom\"\n    d = root / \"legacy-deck\"\n    d.mkdir(parents=True)\n    (d / \"deck.json\").write_text(json.dumps({\"name\": \"Legacy\", \"cards\": [_card()]}), encoding=\"utf-8\")\n    deck = DeckRegistry(builtin, root).get(\"legacy-deck\")\n    assert deck.default_theme == \"minimal-light\"\n\n\ndef test_public_info_exposes_owned_theme(tmp_path):\n    builtin = tmp_path / \"manifest.json\"\n    builtin.write_text(json.dumps([_card()]), encoding=\"utf-8\")\n    root = tmp_path / \"custom\"\n    d = root / \"owned-theme\"\n    d.mkdir(parents=True)\n    (d / \"deck.json\").write_text(json.dumps({\"name\": \"Owned\", \"default_theme\": \"midnight\", \"cards\": [_card()]}), encoding=\"utf-8\")\n    assert DeckRegistry(builtin, root).public_info(\"owned-theme\")[\"default_theme\"] == \"midnight\"\n\n\ndef test_sources_keep_url_override_and_creator_persists_theme():\n    website = Path(__file__).resolve().parents[1]\n    creator = (website / \"public\" / \"creator.js\").read_text(encoding=\"utf-8\")\n    main = (website / \"main.js\").read_text(encoding=\"utf-8\")\n    read = (website / \"public\" / \"read.js\").read_text(encoding=\"utf-8\")\n    assert \"theme: selectedThemeId\" in creator\n    assert \"window.explicitThemeId\" in main\n    assert \"!window.explicitThemeId && deck.default_theme\" in main\n    assert \"deck.default_theme||defaultTheme\" in read\n    assert \"theme: qs.get('theme') || ''\" in read\n''', encoding='utf-8')
