from pathlib import Path
from divination.ai_gateway import ZeroCostGroqGateway


def test_groq_zero_cost_allowlist_contains_fixed_fallback_models():
    assert "openai/gpt-oss-120b" in ZeroCostGroqGateway.ALLOWED_MODELS
    assert "openai/gpt-oss-20b" in ZeroCostGroqGateway.ALLOWED_MODELS
    assert "qwen/qwen3.6-27b" in ZeroCostGroqGateway.ALLOWED_MODELS


def test_server_builds_ordered_groq_model_fallbacks_from_same_key():
    source = Path("fortune_server.py").read_text(encoding="utf-8")
    p120 = source.index('ZeroCostGroqGateway(groq_key, load_env_value("GROQ_MODEL") or "openai/gpt-oss-120b")')
    p20 = source.index('ZeroCostGroqGateway(groq_key, "openai/gpt-oss-20b")')
    pq = source.index('ZeroCostGroqGateway(groq_key, "qwen/qwen3.6-27b")')
    assert p120 < p20 < pq
    assert source.count('groq_key = load_env_value("GROQ_API_KEY")') == 1
