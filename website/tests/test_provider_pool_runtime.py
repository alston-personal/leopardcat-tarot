from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER=(ROOT/'fortune_server.py').read_text(encoding='utf-8')

def test_runtime_builds_zero_cost_provider_pool():
    assert 'ZeroCostProviderPool' in SERVER
    assert 'ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY"))' in SERVER
    assert 'ZeroCostGroqGateway(load_env_value("GROQ_API_KEY"))' in SERVER
    assert 'OPENROUTER_MODEL' in SERVER
