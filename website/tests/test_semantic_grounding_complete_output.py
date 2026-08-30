import json
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
