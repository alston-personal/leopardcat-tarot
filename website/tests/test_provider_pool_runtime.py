from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER=(ROOT/'fortune_server.py').read_text(encoding='utf-8')

def test_runtime_builds_zero_cost_provider_pool():
    assert 'ZeroCostProviderPool' in SERVER
    assert 'ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY"))' in SERVER
    assert 'groq_key = load_env_value("GROQ_API_KEY")' in SERVER
    p120 = SERVER.index('ZeroCostGroqGateway(groq_key, load_env_value("GROQ_MODEL") or "openai/gpt-oss-120b")')
    p20 = SERVER.index('ZeroCostGroqGateway(groq_key, "openai/gpt-oss-20b")')
    pqwen = SERVER.index('ZeroCostGroqGateway(groq_key, "qwen/qwen3.6-27b")')
    assert p120 < p20 < pqwen
    assert 'OPENROUTER_MODEL' in SERVER
