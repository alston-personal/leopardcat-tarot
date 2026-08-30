from pathlib import Path

p = Path('website/divination/ai_gateway.py')
s = p.read_text()
old = 'headers={"Content-Type":"application/json", "Authorization":f"Bearer {self.api_key}"},'
new = 'headers={"Content-Type":"application/json", "Accept":"application/json", "User-Agent":"leopardcat-tarot/1.0", "Authorization":f"Bearer {self.api_key}"},'
if old not in s:
    raise SystemExit('target header block not found')
s = s.replace(old, new, 1)
p.write_text(s)

# Regression test: OpenAI-compatible requests must present a normal client fingerprint.
t = Path('website/tests/test_groq_transport_headers.py')
t.write_text('''from pathlib import Path\n\n\ndef test_openai_compatible_gateway_has_stable_transport_headers():\n    src = Path("website/divination/ai_gateway.py").read_text()\n    assert "\\\"User-Agent\\\":\\\"leopardcat-tarot/1.0\\\"" in src\n    assert "\\\"Accept\\\":\\\"application/json\\\"" in src\n    assert "Authorization" in src\n''')
print('patched')
