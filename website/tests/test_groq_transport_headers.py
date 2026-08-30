from pathlib import Path


def test_openai_compatible_gateway_has_stable_transport_headers():
    src = Path("website/divination/ai_gateway.py").read_text()
    assert "\"User-Agent\":\"leopardcat-tarot/1.0\"" in src
    assert "\"Accept\":\"application/json\"" in src
    assert "Authorization" in src
