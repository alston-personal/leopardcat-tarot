from pathlib import Path

p = Path('website/main.js')
s = p.read_text(encoding='utf-8')
old = "cardMeaning: getLocalizedField(currentDrawnCard.meaning),\n                lang: getQuestionLanguageTag(q), history: currentChatHistory"
new = "cardMeaning: getLocalizedField(currentDrawnCard.meaning),\n                lang: getQuestionLanguageTag(text), history: currentChatHistory"
if old not in s:
    raise SystemExit('legacy follow-up language anchor not found')
if s.count(old) != 1:
    raise SystemExit(f'unexpected anchor count: {s.count(old)}')
s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
