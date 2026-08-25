from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"{label}: expected one match, got {text.count(old)}")
    return text.replace(old, new, 1)


def replace_between(text: str, start: str, end: str, replacement: str, label: str) -> str:
    a = text.find(start)
    b = text.find(end, a + len(start))
    if a < 0 or b < 0:
        raise SystemExit(f"{label}: markers not found")
    return text[:a] + replacement + text[b:]


root = Path(__file__).resolve().parents[1]
server_path = root / "website" / "fortune_server.py"
main_path = root / "website" / "main.js"

server = server_path.read_text(encoding="utf-8")
server = replace_once(server, "import urllib.error\n", "import urllib.error\nimport urllib.parse\nimport html\n", "server imports")
server = replace_once(server, "from divination.ai_gateway import ZeroCostGeminiGateway, AIUnavailable\n", "from divination.ai_gateway import ZeroCostGeminiGateway, AIUnavailable\nfrom divination.brands import BrandRegistry\n", "brand import")
server = replace_once(server, "DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))\n", "DIVINATION_ENGINE = build_default_engine(os.path.dirname(os.path.abspath(__file__)))\nBRANDS = BrandRegistry(DIVINATION_ENGINE.decks)\n", "brand registry")

brand_route = '''        if path.startswith('/api/v1/brands/'):\n            deck_id = path.rsplit('/', 1)[-1]\n            try:\n                data = BRANDS.public_info(deck_id)\n                self.send_response(200)\n                self.send_header('Content-type', 'application/json; charset=utf-8')\n                self.send_header('Cache-Control', 'public, max-age=60')\n                self.end_headers()\n                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))\n            except DivinationError:\n                self.send_error(404)\n            return\n'''
server = replace_once(server, "        if path == '/api/v1/themes':\n", brand_route + "        if path == '/api/v1/themes':\n", "brand route")

old_card_parse = '''        if path == '/' or path == '/index.html':\n            card_id = None\n            if 'card=' in query:\n                match = re.search(r'card=([^&]+)', query)\n                if match:\n                    card_id = match.group(1)\n'''
new_card_parse = '''        if path == '/' or path == '/index.html':\n            params = urllib.parse.parse_qs(query)\n            deck_id = (params.get('deck') or ['leopardcat'])[0]\n            card_id = (params.get('card') or [None])[0]\n'''
server = replace_once(server, old_card_parse, new_card_parse, "root query parsing")

metadata = '''                # 🌿 Construction of metadata from the active Brand Pack + Deck Module.\n                host = 'leopardcat-tarot.milkcat.org'\n                base_url = f"https://{host}"\n                try:\n                    brand = BRANDS.get(deck_id)\n                    active_deck = DIVINATION_ENGINE.decks.get(deck_id)\n                except DivinationError:\n                    brand = BRANDS.get('leopardcat')\n                    active_deck = DIVINATION_ENGINE.decks.get('leopardcat')\n                    deck_id = 'leopardcat'\n\n                meta_title = brand.app_name\n                meta_desc = brand.description\n                fallback_card = active_deck.cards[0] if active_deck.cards else {}\n                selected_card = next((c for c in active_deck.cards if c.get('id') == card_id), None) if card_id else None\n                card_for_image = selected_card or fallback_card\n                image_path = str(card_for_image.get('image') or 'art/renders/card-00-the-fool.webp')\n                meta_img = image_path if image_path.startswith(('http://', 'https://')) else f"{base_url}/{image_path.lstrip('/')}"\n\n                if selected_card:\n                    titles = selected_card.get('title') or {}\n                    if isinstance(titles, dict):\n                        title_zh = titles.get('zh') or titles.get('zh-TW') or titles.get('en') or selected_card.get('id', '')\n                    else:\n                        title_zh = str(titles or selected_card.get('id', ''))\n                    meta_title = brand.share_copy_template.get('zh', '{card}').replace('{card}', title_zh)\n                    meanings = selected_card.get('meanings') or selected_card.get('meaning') or {}\n                    if isinstance(meanings, dict):\n                        raw_desc = meanings.get('upright') or meanings.get('zh') or meanings.get('zh-TW') or meanings.get('en') or ''\n                    else:\n                        raw_desc = str(meanings)\n                    if raw_desc:\n                        meta_desc = str(raw_desc)[:160]\n\n                meta_title = html.escape(str(meta_title), quote=True)\n                meta_desc = html.escape(str(meta_desc), quote=True)\n                meta_img = html.escape(str(meta_img), quote=True)\n\n'''
server = replace_between(server, "                # 🌿 Construction of Metadata\n", "                # 🌿 Use Placeholder Replacement", metadata, "metadata block")
server = server.replace('    <meta property="og:image" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">', '    <meta property="og:image" content="{meta_img}">')
server = server.replace('    <meta property="og:image:secure_url" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">', '    <meta property="og:image:secure_url" content="{meta_img}">')
server = server.replace('    <meta name="twitter:image" content="https://leopardcat-tarot.milkcat.org/spirit-vision/{os.path.splitext(os.path.basename(meta_img))[0]}.webp?v=v999">', '    <meta name="twitter:image" content="{meta_img}">')
server_path.write_text(server, encoding="utf-8")

main = main_path.read_text(encoding="utf-8")
main = replace_once(main, "window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck\n", "window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck\nwindow.activeBrand = null; // Brand Pack: presentation/social identity, independent from Tarot logic\n", "brand state")
main = replace_once(main, '    console.log("Initializing LeopardCat Tarot Systems...");', '    console.log("Initializing Divination Platform...");', "generic init log")
main = replace_once(main, '靈山氣息凝聚中...', '牌卡體驗載入中...', "generic loader")
main = replace_once(main, "            window.siteData = await cR.json();\n            applyLanguage();", "            window.siteData = await cR.json();\n            await window.loadActiveBrand();\n            applyLanguage();", "load brand before language")

brand_js = r'''
window.brandText = function(field, fallback = '') {
    const value = window.activeBrand?.[field];
    if (value && typeof value === 'object') return value[window.currentLang] || value.zh || value.en || fallback;
    return value || fallback;
};

window.applyActiveBrand = function() {
    const b = window.activeBrand;
    if (!b || window.activeDeckId === 'leopardcat') return;
    document.title = b.app_name || b.short_name || 'Tarot';
    const setText = (selector, text) => {
        const el = document.querySelector(selector);
        if (!el || !text) return;
        el.removeAttribute('data-i18n');
        el.textContent = text;
    };
    setText('.nav-logo', b.short_name || b.app_name);
    setText('#hero h1', b.app_name);
    setText('#hero .subtitle', b.description || b.creator_line);
    setText('#fortune .section-title h2', `${b.short_name || b.app_name}・塔羅占卜`);
    setText('#fortune .section-title .label', b.creator_line || 'Creator Tarot');
    setText('#share-memo-title', window.brandText('share_title', b.app_name));
    setText('#share-site-tag', window.brandText('share_site_tag', b.creator_line || ''));
};

window.loadActiveBrand = async function() {
    try {
        const r = await fetch(`/api/v1/brands/${encodeURIComponent(window.activeDeckId || 'leopardcat')}`, {cache:'no-cache'});
        if (!r.ok) throw new Error(`BRAND_${r.status}`);
        window.activeBrand = await r.json();
        window.applyActiveBrand();
    } catch (e) {
        console.warn('[Brand Pack] load failed', e);
        window.activeBrand = {
            brand_id: `fallback:${window.activeDeckId || 'leopardcat'}`,
            app_name: window.activeDeckId || 'Tarot', short_name: window.activeDeckId || 'Tarot',
            share_title: {zh:'塔羅指引', en:'Tarot Reading'},
            share_site_tag: {zh:'線上塔羅', en:'Online Tarot'},
            share_copy_template: {zh:'我抽到了：{card}', en:'I drew {card}'},
            default_quote: {zh:'聽見牌面，也聽見自己。', en:'Listen to the cards, and to yourself.'},
            file_prefix: window.activeDeckId || 'tarot'
        };
    }
};

'''
main = replace_once(main, "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\n", "window.activeDeckId = new URLSearchParams(window.location.search).get('deck') || 'leopardcat';\n\n" + brand_js, "brand functions")
main = replace_once(main, "            await navigator.share({ title: '靈山靈貓 石虎塔羅', text: lastShareText, files: [lastShareFile] });", "            await navigator.share({ title: window.brandText('share_title', 'Tarot Reading'), text: lastShareText, files: [lastShareFile] });", "native reshare title")
main = replace_once(main, "    const quote = bestQuote || (window.currentLang === 'zh' ? '與山靈連結，尋找內心的平靜。' : 'Connect with the spirits, find your inner peace.');", "    const quote = bestQuote || window.brandText('default_quote', window.currentLang === 'zh' ? '聽見牌面，也聽見自己。' : 'Listen to the cards, and to yourself.');", "brand default quote")
main = replace_once(main, "        document.getElementById('share-memo-title').innerText = uiCommon.share_memo_title;\n        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;\n        document.getElementById('share-site-tag').innerText = uiCommon.share_site_tag;", "        document.getElementById('share-memo-title').innerText = window.brandText('share_title', uiCommon.share_memo_title);\n        document.getElementById('share-seeker-label').innerText = uiCommon.share_seeker_label;\n        document.getElementById('share-site-tag').innerText = window.brandText('share_site_tag', uiCommon.share_site_tag);", "share card labels")
main = replace_once(main, "        const shareMsg = common.share_copy_template.replace('{card}', `${shareTitle}${orientationText}`);", "        const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);\n        const shareMsg = brandTemplate.replace('{card}', `${shareTitle}${orientationText}`);", "share copy")
main = replace_once(main, "        const file = new File([blob], `leopardcat-tarot-${Date.now()}.png`, { type: 'image/png' });", "        const filePrefix = window.activeBrand?.file_prefix || 'tarot';\n        const file = new File([blob], `${filePrefix}-${Date.now()}.png`, { type: 'image/png' });", "brand filename")
main = replace_once(main, "                    title: window.siteData[window.currentLang].common.share_memo_title,", "                    title: window.brandText('share_title', window.siteData[window.currentLang].common.share_memo_title),", "native share title")
main = replace_once(main, "                link.download = `leopardcat-tarot-${Date.now()}.png`;", "                link.download = `${window.activeBrand?.file_prefix || 'tarot'}-${Date.now()}.png`;", "fallback filename")
main = replace_once(main, "    const shareMsg = customQuote ? `「${customQuote}」` : common.share_copy_template.replace('{card}', card.title[shareLang]);", "    const brandTemplate = window.brandText('share_copy_template', common.share_copy_template);\n    const cardTitle = card.title?.[shareLang] || card.title?.['zh-TW'] || card.title?.zh || card.title?.en || card.id;\n    const shareMsg = customQuote ? `「${customQuote}」` : brandTemplate.replace('{card}', cardTitle);", "social brand copy")
# Ensure the Brand Pack wins after legacy deck gallery/section adaptation until that compatibility code is removed.
main = replace_once(main, "        if (shareTag) shareTag.textContent = deck.creator ? `牌卡創作：${deck.creator}` : '專屬線上占卜';\n", "        if (shareTag) shareTag.textContent = deck.creator ? `牌卡創作：${deck.creator}` : '專屬線上占卜';\n        window.applyActiveBrand();\n", "reapply brand")
main_path.write_text(main, encoding="utf-8")

print('brand_pack_patch=applied')
