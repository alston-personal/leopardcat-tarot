from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 exact match, got {count}')
    return text.replace(old, new, 1)


def patch_main() -> None:
    p = Path('website/main.js')
    s = p.read_text(encoding='utf-8')

    # Restore and fresh readings both hydrate planner metadata from the receipt.
    restore_anchor = """    window.currentReadingState = snapshot?.reading_state || buildReadingStateFromEnvelope(data);\n    window.activeSpread = window.currentReadingState?.spread || window.activeSpread;\n"""
    restore_new = """    window.currentReadingState = snapshot?.reading_state || buildReadingStateFromEnvelope(data);\n    window.currentSpreadPlan = data.method_result?.spread_plan || null;\n    window.effectiveSpread = data.method_result?.spread || window.currentReadingState?.spread || null;\n    window.activeSpread = window.currentReadingState?.spread || window.activeSpread;\n"""
    s = replace_once(s, restore_anchor, restore_new, 'restore planner receipt')

    fresh_anchor = """    window.currentReadingState = {\n        deck_id: window.activeDeckId,\n"""
    # Fresh metadata is set immediately before the canonical reading state is materialized.
    fresh_new = """    window.currentSpreadPlan = data.method_result?.spread_plan || null;\n    window.effectiveSpread = data.method_result?.spread || null;\n    window.currentReadingState = {\n        deck_id: window.activeDeckId,\n"""
    s = replace_once(s, fresh_anchor, fresh_new, 'fresh planner receipt')

    old_names = """    const spreadNames = {\n        single: uiText('spread_single', 'Single Guidance'),\n        three_card: uiText('spread_three', 'Three-card Timeline'),\n        decision: uiText('spread_decision', 'Decision Spread')\n    };\n"""
    new_names = """    const spreadNames = {\n        single: uiText('spread_single', 'Single Guidance'),\n        clarifier: uiText('spread_clarifier', 'Clarifier'),\n        three_card: uiText('spread_three', 'Three-card Timeline'),\n        situation_advice: uiText('spread_situation_advice', 'Situation · Obstacle · Advice'),\n        decision: uiText('spread_decision', 'Decision Spread'),\n        relationship: uiText('spread_relationship', 'Relationship Five'),\n        career: uiText('spread_career', 'Career Five'),\n        path: uiText('spread_path', 'Path Five'),\n        celtic_cross: uiText('spread_celtic_cross', 'Celtic Cross')\n    };\n"""
    s = replace_once(s, old_names, new_names, 'spread display names')

    old_render = """function renderShareCards(frame, shareContext) {\n    const entries = shareContext.cards;\n    frame.classList.toggle('share-three-card', entries.length > 1);\n    frame.innerHTML = '';\n"""
    new_render = """function renderShareCards(frame, shareContext) {\n    const entries = shareContext.cards;\n    frame.classList.toggle('share-three-card', entries.length > 1 && entries.length <= 3);\n    frame.classList.toggle('share-many-card', entries.length > 3);\n    frame.classList.toggle('share-ten-card', entries.length > 6);\n    frame.dataset.shareCardCount = String(entries.length);\n    frame.innerHTML = '';\n"""
    s = replace_once(s, old_render, new_render, 'N-card share frame classes')

    old_title = """    } else {\n        document.getElementById('share-card-title').innerText = `【${uiText('spread_three_short', 'Three Cards')}】 ${titleParts.join(' · ')}`;\n    }\n"""
    new_title = """    } else {\n        const spreadId = shareState.spread || window.currentReadingEnvelope?.method_result?.spread || '';\n        const spreadLabel = window.currentSpreadPlan?.label || ({\n            three_card: uiText('spread_three', 'Three-card Timeline'),\n            situation_advice: uiText('spread_situation_advice', 'Situation · Obstacle · Advice'),\n            decision: uiText('spread_decision', 'Decision Spread'),\n            relationship: uiText('spread_relationship', 'Relationship Five'),\n            career: uiText('spread_career', 'Career Five'),\n            path: uiText('spread_path', 'Path Five'),\n            celtic_cross: uiText('spread_celtic_cross', 'Celtic Cross')\n        })[spreadId] || `${shareEntries.length} Cards`;\n        document.getElementById('share-card-title').innerText = `【${spreadLabel}】 ${titleParts.join(' · ')}`;\n    }\n"""
    s = replace_once(s, old_title, new_title, 'share spread title')

    pattern = re.compile(
        r"    const count = shareEntries\.length;\n    const gap = count === 1 \? 0 : 14;\n    const cardW = count === 1 \? 180 : 138;\n    const cardH = count === 1 \? 292 : 224;\n    const totalW = cardW \* count \+ gap \* Math\.max\(0, count - 1\);\n    const startX = \(size - totalW\) / 2;\n    const cardY = 102;\n",
        re.S,
    )
    grid = """    const count = shareEntries.length;\n    const layout = count === 1\n        ? {cols:1, cardW:180, cardH:292, gapX:0, gapY:0, captionH:42, cardY:102}\n        : count <= 3\n            ? {cols:count, cardW:138, cardH:224, gapX:14, gapY:0, captionH:46, cardY:102}\n            : count <= 6\n                ? {cols:3, cardW:84, cardH:136, gapX:14, gapY:12, captionH:38, cardY:88}\n                : {cols:5, cardW:62, cardH:100, gapX:10, gapY:10, captionH:34, cardY:88};\n    const rows = Math.ceil(count / layout.cols);\n    const totalW = layout.cardW * layout.cols + layout.gapX * Math.max(0, layout.cols - 1);\n    const startX = (size - totalW) / 2;\n    const cardW = layout.cardW;\n    const cardH = layout.cardH;\n    const cardY = layout.cardY;\n"""
    s, count_sub = pattern.subn(grid, s, count=1)
    if count_sub != 1:
        raise RuntimeError(f'mobile grid declaration: expected 1 match, got {count_sub}')

    old_xy = """    shareEntries.forEach((entry, index) => {\n        const x = startX + index * (cardW + gap);\n        roundedRectPath(ctx, x - 4, cardY - 4, cardW + 8, cardH + 8, 12);\n"""
    new_xy = """    shareEntries.forEach((entry, index) => {\n        const col = index % layout.cols;\n        const row = Math.floor(index / layout.cols);\n        const x = startX + col * (cardW + layout.gapX);\n        const y = cardY + row * (cardH + layout.captionH + layout.gapY);\n        roundedRectPath(ctx, x - 4, y - 4, cardW + 8, cardH + 8, 12);\n"""
    s = replace_once(s, old_xy, new_xy, 'mobile grid x/y')

    # All drawing/caption operations inside the loop must use the row-specific y.
    loop_start = s.index('    shareEntries.forEach((entry, index) => {', s.index('async function renderMobileSafeSquareCanvas'))
    loop_end = s.index('    });\n\n    const quoteTop', loop_start)
    loop = s[loop_start:loop_end]
    loop = loop.replace('cardY + cardH / 2', 'y + cardH / 2')
    loop = loop.replace('ctx.fillRect(x, cardY, cardW, cardH);', 'ctx.fillRect(x, y, cardW, cardH);')
    loop = loop.replace('cardY + cardH + 24 + lineIndex * 17', 'y + cardH + 20 + lineIndex * 15')
    loop = loop.replace("ctx.font = `${count === 1 ? 16 : 13}px", "ctx.font = `${count === 1 ? 16 : (count <= 3 ? 13 : 10)}px")
    s = s[:loop_start] + loop + s[loop_end:]

    old_quote = """    const quoteTop = count === 1 ? 444 : 392;\n"""
    new_quote = """    const gridBottom = cardY + rows * (cardH + layout.captionH) + Math.max(0, rows - 1) * layout.gapY;\n    const quoteTop = count === 1 ? 444 : (count <= 3 ? 392 : Math.min(472, gridBottom + 14));\n"""
    s = replace_once(s, old_quote, new_quote, 'mobile quote position')

    # For dense spreads keep the quote concise enough to preserve the full card grid.
    s = replace_once(
        s,
        "const quoteLines = canvasWrapLines(ctx, `「${quote || ''}」`, 520, count === 1 ? 4 : 5);",
        "const quoteLines = canvasWrapLines(ctx, `「${quote || ''}」`, 520, count === 1 ? 4 : (count <= 3 ? 5 : 3));",
        'dense spread quote lines',
    )

    p.write_text(s, encoding='utf-8')


def patch_style() -> None:
    p = Path('website/style.css')
    s = p.read_text(encoding='utf-8')
    marker = '/* === N-card canonical share layouts (#69) === */'
    if marker in s:
        raise RuntimeError('N-card share style marker already exists')
    s += """\n\n/* === N-card canonical share layouts (#69) === */\n.share-card-frame.share-many-card {\n  display: grid;\n  grid-template-columns: repeat(3, 84px);\n  width: 310px;\n  gap: 8px 10px;\n  justify-content: center;\n  align-items: start;\n}\n.share-card-frame.share-many-card .share-card-slot { width: 84px; }\n.share-card-frame.share-many-card img { width: 78px; max-height: 132px; object-fit: contain; }\n.share-card-frame.share-many-card .share-card-caption { max-width: 84px; font-size: 7.5px; line-height: 1.2; }\n.share-card-frame.share-many-card.share-ten-card {\n  grid-template-columns: repeat(5, 58px);\n  width: 340px;\n  gap: 6px 8px;\n}\n.share-card-frame.share-many-card.share-ten-card .share-card-slot { width: 58px; }\n.share-card-frame.share-many-card.share-ten-card img { width: 54px; max-height: 92px; }\n.share-card-frame.share-many-card.share-ten-card .share-card-caption { max-width: 58px; font-size: 6.5px; line-height: 1.15; }\n.share-card-body.share-og-mode .share-card-frame.share-many-card {\n  display: grid;\n  grid-template-columns: repeat(5, 92px);\n  width: 100%;\n  max-width: 510px;\n  gap: 8px;\n  justify-content: center;\n}\n.share-card-body.share-og-mode .share-card-frame.share-many-card .share-card-slot { width: 92px; }\n.share-card-body.share-og-mode .share-card-frame.share-many-card img { width: 82px; max-height: 138px; object-fit: contain; }\n.share-card-body.share-og-mode .share-card-frame.share-many-card .share-card-caption { max-width: 92px; font-size: 8px; line-height: 1.2; }\n"""
    p.write_text(s, encoding='utf-8')


if __name__ == '__main__':
    patch_main()
    patch_style()
    print('master_spread_share_v2_patch=PASS')
