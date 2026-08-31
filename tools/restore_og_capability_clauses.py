from pathlib import Path
import json

p = Path('governance/capabilities.json')
data = json.loads(p.read_text(encoding='utf-8'))
contract = data['protected_capabilities']['sharing.reading-og-share-preview']['contract']
required = [
    'OG metadata and persisted share images MUST NOT upload or expose the private question or AI answer.',
    'When the browser has rendered the deck-owned 600x600 share card, it MAY persist that PNG using the private reading session token; the public share token grants read-only access to that image while the reading receipt remains valid.'
]
for clause in required:
    if clause not in contract:
        contract.append(clause)
p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
