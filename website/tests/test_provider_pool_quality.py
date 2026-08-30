import json
import urllib.error

import pytest

from divination.ai_gateway import (
    AIUnavailable,
    MASTER_EXPERIENCE_CONTRACT,
    MasterExperienceQualityGate,
    ZeroCostGroqGateway,
    ZeroCostOpenRouterGateway,
    ZeroCostProviderPool,
)


class FakeProvider:
    def __init__(self, provider_id, answer=None, error=None, configured=True):
        self.provider_id=provider_id
        self.model='fixed-test-model'
        self.answer=answer
        self.error=error
        self._configured=configured
        self.prompts=[]
    def configured(self): return self._configured
    def policy(self):
        return {'provider':self.provider_id,'model':self.model,'configured':self._configured,'cost_policy':'zero-cost-required','paid_fallback':False}
    def generate(self,prompt):
        self.prompts.append(prompt)
        if self.error: raise self.error
        return self.answer


def good(text='同一位大師會先忠實閱讀既有牌局，再把象徵與提問連結起來。這段解讀保持一致的語氣、界線與實際建議，不改牌、不重抽，也不把供應商當成新的角色。'):
    return text


def test_fallback_gets_exact_same_compiled_prompt():
    a=FakeProvider('gemini',error=AIUnavailable('provider_busy','busy',True,{'provider':'gemini'}))
    b=FakeProvider('groq',answer=good())
    pool=ZeroCostProviderPool([a,b],MasterExperienceQualityGate(min_chars=20))
    assert pool.generate('PERSONA PROMPT') == good()
    assert a.prompts == b.prompts
    assert a.prompts[0].startswith(MASTER_EXPERIENCE_CONTRACT)
    assert a.prompts[0].endswith('PERSONA PROMPT')


def test_unconfigured_provider_is_skipped_without_changing_prompt():
    a=FakeProvider('gemini',configured=False)
    b=FakeProvider('groq',answer=good())
    pool=ZeroCostProviderPool([a,b],MasterExperienceQualityGate(min_chars=20))
    pool.generate('X')
    assert a.prompts == []
    assert len(b.prompts)==1


def test_quality_gate_rejects_provider_identity_leak_and_uses_next_engine():
    a=FakeProvider('gemini',answer='As an AI language model, I will now read your cards. ' + good())
    b=FakeProvider('groq',answer=good('大師仍以同樣方式解讀：先看牌陣結構，再回到你的問題，最後給出可執行但不武斷的提醒。這不是另一個角色，只是同一套解讀契約的延續。'))
    pool=ZeroCostProviderPool([a,b],MasterExperienceQualityGate(min_chars=20))
    out=pool.generate('X')
    assert '同樣方式' in out


def test_policy_is_zero_cost_fixed_model_pool():
    a=FakeProvider('gemini',answer=good())
    b=FakeProvider('groq',answer=good())
    p=ZeroCostProviderPool([a,b]).policy()
    assert p['provider']=='zero-cost-pool'
    assert p['primary_provider']=='gemini'
    assert p['paid_fallback'] is False
    assert p['random_model_routing'] is False
    assert p['quality_contract']=='master-experience/v1'


def test_groq_uses_fixed_approved_model():
    g=ZeroCostGroqGateway('key')
    assert g.model=='openai/gpt-oss-120b'
    with pytest.raises(RuntimeError):
        ZeroCostGroqGateway('key','some-random-model')


def test_openrouter_random_free_router_is_forbidden():
    with pytest.raises(RuntimeError):
        ZeroCostOpenRouterGateway('key','openrouter/free')
    with pytest.raises(RuntimeError):
        ZeroCostOpenRouterGateway('key','paid/model')
