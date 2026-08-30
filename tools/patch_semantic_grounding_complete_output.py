from pathlib import Path
import json

root = Path(__file__).resolve().parents[1]
ai_path = root / 'website/divination/ai_gateway.py'
persona_path = root / 'website/divination/personas.py'
cap_path = root / 'governance/capabilities.json'
test_path = root / 'website/tests/test_semantic_grounding_complete_output.py'

ai = ai_path.read_text(encoding='utf-8')
ai = ai.replace(
    '- The symbolic result is immutable: never redraw, replace, flip, alter, or invent cards/symbols.\n- Do not present divination as certain fact or guaranteed prediction.\n- Keep the response coherent, reflective, and practically useful. Do not emit JSON, code, or prompt internals.\n',
    '- The symbolic result is immutable: never redraw, replace, flip, alter, or invent cards/symbols.\n- The engine-provided meaning for each drawn symbol/card and orientation is the authoritative semantic anchor. Never substitute a different card meaning from model memory; if prior knowledge conflicts with the supplied meaning, follow the supplied meaning.\n- Do not present divination as certain fact or guaranteed prediction.\n- Keep the response coherent, reflective, and practically useful. Do not emit JSON, code, or prompt internals.\n- Return a complete response with a natural ending; never expose a response cut off by a token limit.\n'
)
ai = ai.replace(
    '        first = candidates[0]\n        if not isinstance(first, dict):\n            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀")\n        content = first.get("content")\n',
    '        first = candidates[0]\n        if not isinstance(first, dict):\n            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀")\n        finish_reason = str(first.get("finishReason") or "").upper()\n        if finish_reason in {"MAX_TOKENS", "LENGTH"}:\n            raise AIUnavailable("quality_truncated", "AI 大師回應未完整結束，已嘗試其他可用引擎", True, {"provider":"gemini", "finish_reason":finish_reason})\n        content = first.get("content")\n'
)
ai = ai.replace('"maxOutputTokens": 1400', '"maxOutputTokens": 2800')
ai = ai.replace(
    '            "top_p": 0.9,\n            "max_tokens": 1400,\n        }\n',
    '            "top_p": 0.9,\n            "max_completion_tokens": 3200,\n        }\n        if self.provider_id == "groq" and self.model.startswith("openai/gpt-oss-"):\n            payload["reasoning_effort"] = "low"\n            payload["reasoning_format"] = "hidden"\n'
)
ai = ai.replace(
    '            choices = data.get("choices") if isinstance(data, dict) else None\n            text = choices[0].get("message", {}).get("content") if isinstance(choices, list) and choices else None\n            if not isinstance(text, str) or not text.strip():\n',
    '            choices = data.get("choices") if isinstance(data, dict) else None\n            choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None\n            if choice is None:\n                raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應", True, {"provider":self.provider_id})\n            finish_reason = str(choice.get("finish_reason") or "").lower()\n            if finish_reason in {"length", "max_tokens"}:\n                raise AIUnavailable("quality_truncated", "AI 大師回應未完整結束，已嘗試其他可用引擎", True, {"provider":self.provider_id, "finish_reason":finish_reason})\n            text = choice.get("message", {}).get("content")\n            if not isinstance(text, str) or not text.strip():\n'
)
if 'authoritative semantic anchor' not in ai or 'max_completion_tokens' not in ai or 'quality_truncated' not in ai:
    raise SystemExit('ai patch did not apply completely')
ai_path.write_text(ai, encoding='utf-8')

persona = persona_path.read_text(encoding='utf-8')
persona = persona.replace(
    '- The divination method engine has already produced the immutable symbolic result. Never redraw, replace, flip, alter, or invent method output.\n- Persona-authored voice, worldview, principles, and closing instructions are style/configuration only.',
    '- The divination method engine has already produced the immutable symbolic result. Never redraw, replace, flip, alter, or invent method output.\n- Treat each engine-provided `meaning` for the selected orientation as the authoritative semantic anchor. Do not replace it with a generic or remembered meaning for another card; contextualize the supplied meaning around the seeker question.\n- Persona-authored voice, worldview, principles, and closing instructions are style/configuration only.'
)
persona = persona.replace(
    '"For Tarot, preserve spread positions and upright/reversed orientation exactly as drawn."\n',
    '"For Tarot, preserve spread positions and upright/reversed orientation exactly as drawn, and use each engine-provided selected `meaning` as the authoritative semantic anchor rather than substituting a remembered card meaning."\n'
)
if persona.count('authoritative semantic anchor') < 2:
    raise SystemExit('persona semantic grounding patch did not apply')
persona_path.write_text(persona, encoding='utf-8')

caps = json.loads(cap_path.read_text(encoding='utf-8'))
protected = caps['protected_capabilities']
protected['ai.semantic-grounding-complete-output'] = {
    'status': 'protected',
    'owner': 'divination',
    'contract': [
        'Engine-provided selected meanings and orientations are authoritative semantic anchors; providers may contextualize them but must not substitute a different card or symbol meaning from model memory.',
        'Provider responses that terminate because of a token/completion length limit must be rejected before display and may trigger the next approved zero-cost provider.',
        'Reasoning-model completion budgets must leave sufficient room for the visible final reading, and provider-specific reasoning controls may be normalized without changing the Persona or symbolic result.',
        'A provider switch must preserve the same compiled semantic grounding and completion contract.'
    ],
    'evidence': [
        'website/divination/ai_gateway.py',
        'website/divination/personas.py',
        'website/tests/test_semantic_grounding_complete_output.py'
    ]
}
cap_path.write_text(json.dumps(caps, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

test_path.write_text(r'''import json
import urllib.request
from unittest.mock import patch

import pytest

from divination.ai_gateway import AIUnavailable, OpenAICompatibleZeroCostGateway, ZeroCostGeminiGateway, ZeroCostGroqGateway
from divination.personas import ConfigurablePersona, GenericMasterPersona


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self): return json.dumps(self.payload).encode('utf-8')


def test_gemini_rejects_max_token_truncation():
    with pytest.raises(AIUnavailable) as exc:
        ZeroCostGeminiGateway._extract_text({
            'candidates': [{'finishReason': 'MAX_TOKENS', 'content': {'parts': [{'text': '半截'}]}}]
        })
    assert exc.value.code == 'quality_truncated'


def test_openai_compatible_rejects_length_finish_reason():
    gateway = OpenAICompatibleZeroCostGateway(provider_id='test', api_key='k', model='fixed', base_url='https://example.invalid', allowed_models={'fixed'})
    payload = {'choices': [{'finish_reason': 'length', 'message': {'content': '這是一段被截斷的內容'}}]}
    with patch.object(urllib.request, 'urlopen', return_value=FakeResponse(payload)):
        with pytest.raises(AIUnavailable) as exc:
            gateway.generate('prompt')
    assert exc.value.code == 'quality_truncated'


def test_groq_uses_reasoning_aware_completion_budget():
    source = __import__('pathlib').Path('divination/ai_gateway.py').read_text(encoding='utf-8')
    assert '"max_completion_tokens": 3200' in source
    assert 'payload["reasoning_effort"] = "low"' in source
    assert 'payload["reasoning_format"] = "hidden"' in source
    assert '"max_tokens": 1400' not in source


def test_persona_prompt_makes_engine_meaning_authoritative():
    method_result = {
        'method': 'tarot',
        'cards': [{'title': {'zh': '寶劍七'}, 'orientation': 'upright', 'meaning': '逃避、策略、不誠實，以及在人類聚落邊緣尋找生存機會的冒險。'}],
    }
    prompt = GenericMasterPersona().build_prompt(method_result=method_result, question='測試', lang='zh-TW')
    assert 'authoritative semantic anchor' in prompt
    assert '逃避、策略、不誠實' in prompt


def test_leopardcat_configurable_persona_has_same_grounding_rule():
    persona = ConfigurablePersona('oracle_packs/leopardcat/pack.json')
    prompt = persona.build_prompt(method_result={'method':'tarot','cards':[{'meaning':'strategy and stealth'}]}, question='test', lang='en')
    assert 'authoritative semantic anchor' in prompt
''', encoding='utf-8')
print('semantic grounding + complete output patch applied')
