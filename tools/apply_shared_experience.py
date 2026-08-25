from pathlib import Path
p=Path('website/main.js')
s=p.read_text()

# The feature branch may already contain the generated patch. Treat that as success so
# validation workflows can be re-run safely without depending on the pre-patch source.
if "window.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck" in s:
    required = [
        "const shareOrientation = shareState.orientation || 'upright';",
        "shareImgEl.style.transform = shareOrientation === 'reversed' ? 'rotate(180deg)' : '';",
        "shareU.searchParams.set('orientation', 'reversed')",
        "window.currentReadingState = {",
        "deck_id: window.activeDeckId",
        "theme_id: window.activeThemeId",
    ]
    missing = [x for x in required if x not in s]
    if missing:
        raise SystemExit('shared experience patch is partial; missing: ' + ', '.join(missing))
    print('shared experience patch already applied and validated')
    raise SystemExit(0)

def once(old,new):
    global s
    if old not in s: raise SystemExit('missing anchor: '+old[:80])
    s=s.replace(old,new,1)

once("window.currentReadingEnvelope = null;", "window.currentReadingEnvelope = null;\nwindow.currentReadingState = null; // shared deck/theme/card/orientation state for every Tarot deck")

once("    document.getElementById('share-card-img').src = `art/renders/${currentDrawnCard.id}.webp`;\n    document.getElementById('share-card-title').innerText = `【${currentDrawnCard.title['zh']} / ${currentDrawnCard.title['en']}】`;", "    const shareState = window.currentReadingState || {};\n    const shareOrientation = shareState.orientation || 'upright';\n    const shareImage = currentDrawnCard.image || `art/renders/${currentDrawnCard.id}.webp`;\n    const shareImgEl = document.getElementById('share-card-img');\n    shareImgEl.src = shareImage;\n    shareImgEl.style.transform = shareOrientation === 'reversed' ? 'rotate(180deg)' : '';\n    const titleZh = currentDrawnCard.title?.zh || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.en || currentDrawnCard.id;\n    const titleEn = currentDrawnCard.title?.en || titleZh;\n    const orientationLabel = shareOrientation === 'reversed' ? (window.currentLang === 'zh' ? '逆位' : 'Reversed') : (window.currentLang === 'zh' ? '正位' : 'Upright');\n    document.getElementById('share-card-title').innerText = `【${titleZh} / ${titleEn}】 · ${orientationLabel}`;")

once("        const shareMsg = common.share_copy_template.replace('{card}', currentDrawnCard.title[shareLang]);\n        // 🛠️ Dynamic URL Detection (Fix for milkcat.org and other domains)\n        const shareUrl = window.location.origin + window.location.pathname;", "        const shareTitle = currentDrawnCard.title?.[shareLang] || currentDrawnCard.title?.['zh-TW'] || currentDrawnCard.title?.zh || currentDrawnCard.title?.en || currentDrawnCard.id;\n        const orientationText = (window.currentReadingState?.orientation === 'reversed') ? (shareLang === 'zh' ? '（逆位）' : ' (Reversed)') : '';\n        const shareMsg = common.share_copy_template.replace('{card}', `${shareTitle}${orientationText}`);\n        // Shared deep link preserves deck + theme + card + orientation.\n        const shareU = new URL(window.location.origin + window.location.pathname);\n        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n        if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n        shareU.searchParams.set('card', currentDrawnCard.id);\n        if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');\n        const shareUrl = shareU.toString();")

once("    const shareUrl = `${window.location.origin}${window.location.pathname}?card=${card.id}`;", "    const shareU = new URL(`${window.location.origin}${window.location.pathname}`);\n    if (window.activeDeckId && window.activeDeckId !== 'leopardcat') shareU.searchParams.set('deck', window.activeDeckId);\n    if (window.activeThemeId) shareU.searchParams.set('theme', window.activeThemeId);\n    shareU.searchParams.set('card', card.id);\n    if (window.currentReadingState?.orientation === 'reversed') shareU.searchParams.set('orientation', 'reversed');\n    const shareUrl = shareU.toString();")

once("    currentDrawnCard = resolved[0].card;\n    window.currentDrawnCard = currentDrawnCard;\n    window.currentReadingEnvelope = data;", "    currentDrawnCard = resolved[0].card;\n    window.currentDrawnCard = currentDrawnCard;\n    window.currentReadingEnvelope = data;\n    window.currentReadingState = {\n        deck_id: window.activeDeckId,\n        theme_id: window.activeThemeId,\n        card_id: resolved[0].spec.card_id || currentDrawnCard.id,\n        orientation: resolved[0].spec.orientation || 'upright',\n        spread: data.method_result?.spread || 'single',\n        cards: resolved.map(({spec, card}) => ({ card_id: spec.card_id || card.id, orientation: spec.orientation || 'upright', position: spec.position, position_label: spec.position_label }))\n    };")

once("    window.currentReadingEnvelope = null;\n    lastShareFile = null;", "    window.currentReadingEnvelope = null;\n    window.currentReadingState = null;\n    lastShareFile = null;")

p.write_text(s)
print('shared experience patch applied and validated')
