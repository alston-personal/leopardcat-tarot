from pathlib import Path
p=Path('website/main.js')
s=p.read_text()
old="""        // ⚡ Stage 2: Background load manifest (Large)\n        const mR = await fetch(`manifest.json?v=${ts}`, { cache: 'no-cache' });\n        if (mR.ok) {\n            window.cardData = await mR.json();\n            console.log(\"Manifest loaded, preparing gallery...\");\n            setTimeout(() => {\n                const groups = window.siteData[window.currentLang].groups;\n                renderGallery(groups, window.cardData);\n                initScrollReveal();\n            }, 200);\n        }\n"""
new="""        // ⚡ Stage 2: Bootstrap exactly one Deck Module.\n        // Custom decks must never be overwritten by LeopardCat's built-in manifest.\n        if (window.activeDeckId && window.activeDeckId !== 'leopardcat') {\n            await window.loadActiveDeckBranding();\n            initScrollReveal();\n        } else {\n            const mR = await fetch(`manifest.json?v=${ts}`, { cache: 'no-cache' });\n            if (mR.ok) {\n                window.cardData = await mR.json();\n                console.log(\"LeopardCat deck loaded, preparing gallery...\");\n                setTimeout(() => {\n                    const groups = window.siteData[window.currentLang].groups;\n                    renderGallery(groups, window.cardData);\n                    initScrollReveal();\n                }, 200);\n            }\n        }\n"""
if old not in s:
    if 'Bootstrap exactly one Deck Module' in s:
        print('deck bootstrap already fixed')
        raise SystemExit(0)
    raise SystemExit('stage2 anchor not found')
s=s.replace(old,new,1)
old_listener="document.addEventListener('DOMContentLoaded', () => window.loadActiveDeckBranding());"
if old_listener not in s:
    raise SystemExit('custom deck listener anchor not found')
s=s.replace(old_listener,"// Custom deck bootstrap is owned by initAllSystems() to prevent manifest races.",1)
p.write_text(s)
print('deck_bootstrap_exclusive=patched')
