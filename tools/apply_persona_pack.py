from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, got {count}")
    return text.replace(old, new, 1)


root = Path(__file__).resolve().parents[1]
server_path = root / "website" / "fortune_server.py"
main_path = root / "website" / "main.js"
publisher_path = root / "website" / "divination" / "publishing.py"

# Publisher: persist a declarative default Persona Pack on new custom decks.
pub = publisher_path.read_text(encoding="utf-8")
pub = replace_once(
    pub,
    "        reversals = bool(payload.get(\"reversals\", False))\n",
    "        reversals = bool(payload.get(\"reversals\", False))\n        default_persona = _clean_text(payload.get(\"persona\"), 64).lower() or \"master\"\n        if not re.fullmatch(r\"[a-z0-9][a-z0-9-]{1,63}\", default_persona):\n            raise DivinationError(\"無效的解牌 Persona\")\n",
    "publisher persona input",
)
pub = replace_once(
    pub,
    '                "reversals": reversals,\n                "card_count": len(saved_cards),\n',
    '                "reversals": reversals,\n                "default_persona": default_persona,\n                "card_count": len(saved_cards),\n',
    "publisher manifest persona",
)
pub = replace_once(
    pub,
    '            "reversals": reversals,\n            "share_path": f"/?deck={deck_id}",\n',
    '            "reversals": reversals,\n            "default_persona": default_persona,\n            "share_path": f"/?deck={deck_id}",\n',
    "publisher return persona",
)
publisher_path.write_text(pub, encoding="utf-8")

# Server: Persona catalog endpoint + data-driven default selection.
server = server_path.read_text(encoding="utf-8")
server = replace_once(
    server,
    "from divination.brands import BrandRegistry\n",
    "from divination.brands import BrandRegistry\nfrom divination.personas import persona_public_info\n",
    "server persona import",
)
persona_route = '''        if path == '/api/v1/personas':\n            params = urllib.parse.parse_qs(query)\n            deck_id = (params.get('deck') or ['leopardcat'])[0]\n            try:\n                deck = DIVINATION_ENGINE.decks.get(deck_id)\n                default_persona = deck.default_persona\n                items = [persona_public_info(DIVINATION_ENGINE.personas.get(pid)) for pid in DIVINATION_ENGINE.personas.capabilities()]\n                self.send_response(200)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Cache-Control', 'public, max-age=60')\n                self.end_headers()\n                self.wfile.write(json.dumps({'default_persona': default_persona, 'personas': items}, ensure_ascii=False).encode('utf-8'))\n            except DivinationError:\n                self.send_error(404)\n            return\n'''
server = replace_once(
    server,
    "        if path.startswith('/api/v1/brands/'):\n",
    persona_route + "        if path.startswith('/api/v1/brands/'):\n",
    "persona route",
)
old_initial = '''                else:\n                    persona_id = str(req_data.get('persona') or 'leopardcat')\n                    request = ReadingRequest(\n                        method=str(req_data.get('method') or 'tarot'),\n                        persona=persona_id,\n                        question=question,\n                        input=req_data.get('input') or {},\n                        lang=lang,\n                        seed=req_data.get('seed'),\n                    )\n'''
new_initial = '''                else:\n                    input_data = req_data.get('input') or {}\n                    deck_id = str(input_data.get('deck_id') or 'leopardcat')\n                    requested_persona = str(req_data.get('persona') or '').strip()\n                    persona_id = requested_persona or DIVINATION_ENGINE.decks.get(deck_id).default_persona\n                    request = ReadingRequest(\n                        method=str(req_data.get('method') or 'tarot'),\n                        persona=persona_id,\n                        question=question,\n                        input=input_data,\n                        lang=lang,\n                        seed=req_data.get('seed'),\n                    )\n'''
server = replace_once(server, old_initial, new_initial, "server persona resolution")
server_path.write_text(server, encoding="utf-8")

# Browser: Persona becomes URL/runtime state, not a deck-id conditional.
main = main_path.read_text(encoding="utf-8")
main = replace_once(
    main,
    "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\n",
    "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\nwindow.activePersonaId = new URLSearchParams(window.location.search).get('persona') || null;\nwindow.defaultPersonaId = null;\n",
    "persona runtime state",
)
persona_js = r'''
window.initPersonaSwitcher = async function() {
    try {
        const r = await fetch(`/api/v1/personas?deck=${encodeURIComponent(window.activeDeckId)}`, {cache:'no-cache'});
        if (!r.ok) throw new Error(`PERSONAS_${r.status}`);
        const data = await r.json();
        window.defaultPersonaId = data.default_persona || 'master';
        if (!window.activePersonaId) window.activePersonaId = window.defaultPersonaId;

        const box = document.createElement('div');
        box.id = 'persona-switcher';
        box.style.cssText = 'position:fixed;right:12px;bottom:58px;z-index:1200;background:#111c;border:1px solid #ffffff22;border-radius:999px;padding:6px 10px;backdrop-filter:blur(8px);font-size:12px';
        box.innerHTML = '<label style="display:flex;gap:6px;align-items:center">解牌者 <select id="persona-switcher-select" style="border-radius:999px;padding:4px 8px"></select></label>';
        document.body.appendChild(box);
        const sel = box.querySelector('select');
        for (const p of data.personas || []) {
            const o = document.createElement('option');
            o.value = p.persona_id;
            o.textContent = p.name || p.persona_id;
            sel.appendChild(o);
        }
        if (![...sel.options].some(o => o.value === window.activePersonaId)) window.activePersonaId = window.defaultPersonaId;
        sel.value = window.activePersonaId;
        sel.addEventListener('change', () => {
            window.activePersonaId = sel.value;
            const u = new URL(location.href);
            if (window.activePersonaId === window.defaultPersonaId) u.searchParams.delete('persona');
            else u.searchParams.set('persona', window.activePersonaId);
            history.replaceState(null, '', u);
        });
    } catch (e) {
        console.warn('[Persona Pack] load failed', e);
    }
};

document.addEventListener('DOMContentLoaded', () => window.initPersonaSwitcher());

'''
main = replace_once(
    main,
    "window.activeThemeId = new URLSearchParams(window.location.search).get('theme') || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');\n",
    persona_js + "window.activeThemeId = new URLSearchParams(window.location.search).get('theme') || (window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'minimal-light');\n",
    "persona switcher",
)
main = replace_once(
    main,
    "            method: 'tarot', persona: window.activeDeckId === 'leopardcat' ? 'leopardcat' : 'master', question: q,\n",
    "            method: 'tarot', persona: window.activePersonaId || undefined, question: q,\n",
    "remove deck persona conditional",
)
main = replace_once(
    main,
    "    const data = await resp.json();\n    window.pendingReadingSession = null;\n",
    "    const data = await resp.json();\n    window.pendingReadingSession = null;\n    window.activePersonaId = data.persona || window.activePersonaId || window.defaultPersonaId;\n",
    "capture resolved persona",
)
main = replace_once(
    main,
    "        theme_id: window.activeThemeId,\n        card_id: resolved[0].spec.card_id || currentDrawnCard.id,\n",
    "        theme_id: window.activeThemeId,\n        persona_id: window.activePersonaId,\n        card_id: resolved[0].spec.card_id || currentDrawnCard.id,\n",
    "reading state persona",
)
main = replace_once(
    main,
    "    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n    shareU.searchParams.set('card', card.id);\n",
    "    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n    if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n    shareU.searchParams.set('card', card.id);\n",
    "share persona deep link",
)
# The share generator has a second deep-link construction path.
main = replace_once(
    main,
    "        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n        shareU.searchParams.set('card', currentDrawnCard.id);\n",
    "        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n        if (window.activePersonaId && window.activePersonaId !== window.defaultPersonaId) shareU.searchParams.set('persona', window.activePersonaId);\n        shareU.searchParams.set('card', currentDrawnCard.id);\n",
    "share generator persona deep link",
)
main_path.write_text(main, encoding="utf-8")

print('persona_pack_patch=applied')
