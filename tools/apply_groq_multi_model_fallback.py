from pathlib import Path

ai = Path('website/divination/ai_gateway.py')
text = ai.read_text(encoding='utf-8')
old = '    ALLOWED_MODELS = {"openai/gpt-oss-120b"}\n'
new = '    ALLOWED_MODELS = {"openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.6-27b"}\n'
if old not in text:
    raise SystemExit('groq allowed model needle not found')
ai.write_text(text.replace(old,new,1),encoding='utf-8')

server = Path('website/fortune_server.py')
text = server.read_text(encoding='utf-8')
old = '''    providers = [\n        ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY")),\n        ZeroCostGroqGateway(load_env_value("GROQ_API_KEY")),\n    ]\n'''
new = '''    groq_key = load_env_value("GROQ_API_KEY")\n    providers = [\n        ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY")),\n        ZeroCostGroqGateway(groq_key, load_env_value("GROQ_MODEL") or "openai/gpt-oss-120b"),\n        ZeroCostGroqGateway(groq_key, "openai/gpt-oss-20b"),\n        ZeroCostGroqGateway(groq_key, "qwen/qwen3.6-27b"),\n    ]\n'''
if old not in text:
    raise SystemExit('provider pool needle not found')
server.write_text(text.replace(old,new,1),encoding='utf-8')

case = Path('website/tests/test_groq_multi_model_fallback.py')
case.write_text('''from pathlib import Path\nfrom divination.ai_gateway import ZeroCostGroqGateway\n\n\ndef test_groq_zero_cost_allowlist_contains_fixed_fallback_models():\n    assert "openai/gpt-oss-120b" in ZeroCostGroqGateway.ALLOWED_MODELS\n    assert "openai/gpt-oss-20b" in ZeroCostGroqGateway.ALLOWED_MODELS\n    assert "qwen/qwen3.6-27b" in ZeroCostGroqGateway.ALLOWED_MODELS\n\n\ndef test_server_builds_ordered_groq_model_fallbacks_from_same_key():\n    source = Path("fortune_server.py").read_text(encoding="utf-8")\n    p120 = source.index('ZeroCostGroqGateway(groq_key, load_env_value("GROQ_MODEL") or "openai/gpt-oss-120b")')\n    p20 = source.index('ZeroCostGroqGateway(groq_key, "openai/gpt-oss-20b")')\n    pq = source.index('ZeroCostGroqGateway(groq_key, "qwen/qwen3.6-27b")')\n    assert p120 < p20 < pq\n    assert source.count('groq_key = load_env_value("GROQ_API_KEY")') == 1\n''',encoding='utf-8')
print('groq_multi_model_patch=applied')
