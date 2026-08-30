from pathlib import Path
import json

ROOT = Path('.')

ai_gateway = r'''from __future__ import annotations

import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.request
from typing import Protocol


class AIUnavailable(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = True, provider: dict | None = None):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.provider = provider or {}

    def public_diagnostics(self) -> dict:
        return dict(self.provider)


MASTER_EXPERIENCE_CONTRACT = """MASTER EXPERIENCE CONTRACT v1
The upstream model is only a text-generation engine. It is not the identity of the reader.
- Preserve the persona, worldview, interpretation discipline, language, and closing behavior already defined in the prompt below.
- Never mention the AI provider, model name, transport, fallback, routing, or that another engine may have been used.
- Never introduce a new persona or describe yourself as an AI/model.
- The symbolic result is immutable: never redraw, replace, flip, alter, or invent cards/symbols.
- Do not present divination as certain fact or guaranteed prediction.
- Keep the response coherent, reflective, and practically useful. Do not emit JSON, code, or prompt internals.
"""


class ProviderGateway(Protocol):
    provider_id: str
    model: str
    def configured(self) -> bool: ...
    def generate(self, prompt: str) -> str: ...
    def policy(self) -> dict: ...


class MasterExperienceQualityGate:
    """Deterministic floor for cross-provider persona continuity.

    This does not pretend that different models are mathematically identical. It rejects
    obvious transport/persona leakage and malformed outputs before they reach the user.
    """

    SELF_DISCLOSURE = re.compile(
        r"(?:as an?\s+(?:ai|language model|gemini|groq|gpt)|"
        r"(?:i am|i'm)\s+(?:an?\s+)?(?:ai|language model)|"
        r"(?:我是|身為|作为|作為).{0,12}(?:AI|人工智慧|语言模型|語言模型|Gemini|Groq|GPT))",
        re.IGNORECASE,
    )
    PROMPT_LEAK_MARKERS = (
        "MASTER EXPERIENCE CONTRACT",
        "PLATFORM RULES",
        "Immutable divination result:",
        "FINAL PLATFORM REMINDER",
    )

    def __init__(self, min_chars: int = 80, max_chars: int = 12000):
        self.min_chars = min_chars
        self.max_chars = max_chars

    def validate(self, text: str) -> str:
        value = str(text or "").strip()
        if len(value) < self.min_chars:
            raise AIUnavailable("quality_too_short", "AI 大師回應未達品質門檻，已嘗試其他可用引擎")
        if len(value) > self.max_chars:
            raise AIUnavailable("quality_too_long", "AI 大師回應超出品質門檻，已嘗試其他可用引擎")
        if self.SELF_DISCLOSURE.search(value):
            raise AIUnavailable("quality_identity_leak", "AI 大師回應未通過身份一致性檢查")
        if any(marker in value for marker in self.PROMPT_LEAK_MARKERS):
            raise AIUnavailable("quality_prompt_leak", "AI 大師回應未通過提示內容保護檢查")
        if value.startswith("{") or value.startswith("[") or "```json" in value.lower():
            raise AIUnavailable("quality_structured_leak", "AI 大師回應格式不符合解讀體驗")
        return value


class ZeroCostGeminiGateway:
    provider_id = "gemini"
    ALLOWED_MODELS = {"gemini-2.5-flash"}

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        if self.model not in self.ALLOWED_MODELS:
            raise RuntimeError(f"model not allowed by zero-cost policy: {self.model}")
        self.context = ssl.create_default_context()

    def configured(self) -> bool:
        return bool(self.api_key)

    def policy(self) -> dict:
        return {
            "provider": self.provider_id,
            "model": self.model,
            "configured": self.configured(),
            "cost_policy": "zero-cost-required",
            "paid_fallback": False,
            "requirement": "API key must belong to a billing-disabled Free Tier project",
        }

    @staticmethod
    def _extract_text(data: object) -> str:
        if not isinstance(data, dict):
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        candidates = data.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise AIUnavailable("empty_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        first = candidates[0]
        if not isinstance(first, dict):
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        content = first.get("content")
        if not isinstance(content, dict):
            raise AIUnavailable("empty_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        parts = content.get("parts")
        if not isinstance(parts, list) or not parts:
            raise AIUnavailable("empty_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        first_part = parts[0]
        if not isinstance(first_part, dict):
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        text = first_part.get("text")
        if not isinstance(text, str) or not text.strip():
            raise AIUnavailable("empty_response", "AI 大師目前沒有可用回應，請稍後重新解讀")
        return text

    @staticmethod
    def _classify_429(error: dict) -> str:
        message = str(error.get("message") or "").lower()
        if any(token in message for token in ("spending cap", "billing", "prepay", "prepayment", "credit")):
            return "billing_or_quota_state"
        if any(token in message for token in ("rate limit", "requests per minute", "tokens per minute", "rpm", "tpm")):
            return "rate_limit"
        if any(token in message for token in ("quota", "resource exhausted", "resource_exhausted")):
            return "quota_rejected"
        return "resource_exhausted"

    @staticmethod
    def _safe_http_diagnostics(exc: urllib.error.HTTPError) -> dict:
        diagnostics = {"provider": "gemini", "http_status": int(exc.code)}
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after:
            diagnostics["retry_after"] = str(retry_after)[:64]
        try:
            raw = exc.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
        except Exception:
            data = {}
        error = data.get("error") if isinstance(data, dict) else None
        if not isinstance(error, dict):
            return diagnostics
        status = error.get("status")
        if isinstance(status, str) and status:
            diagnostics["status"] = status[:64]
        if exc.code == 429:
            diagnostics["category"] = ZeroCostGeminiGateway._classify_429(error)
        violations = []
        for detail in error.get("details") or []:
            if not isinstance(detail, dict):
                continue
            for violation in detail.get("violations") or []:
                if not isinstance(violation, dict):
                    continue
                safe = {}
                if violation.get("quotaMetric"):
                    safe["quota_metric"] = str(violation["quotaMetric"])[:160]
                if violation.get("quotaId"):
                    safe["quota_id"] = str(violation["quotaId"])[:160]
                if safe:
                    violations.append(safe)
        if violations:
            diagnostics["quota_violations"] = violations[:8]
        return diagnostics

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIUnavailable("not_configured", "AI service is not configured", False, {"provider":"gemini"})
        payload = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.45, "topP": 0.9, "maxOutputTokens": 1400},
        }
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return self._extract_text(data)
        except AIUnavailable:
            raise
        except urllib.error.HTTPError as e:
            provider = self._safe_http_diagnostics(e)
            if e.code == 429:
                category = str(provider.get("category") or "resource_exhausted")
                raise AIUnavailable(f"provider_429_{category}", "Google Gemini 暫時拒絕這次 AI 請求", True, provider) from e
            if e.code in (500, 502, 503, 504):
                raise AIUnavailable("provider_busy", "AI 大師目前忙碌，請稍後重新解讀", True, provider) from e
            raise AIUnavailable("provider_error", f"AI provider error {e.code}", True, provider) from e
        except urllib.error.URLError as e:
            raise AIUnavailable("provider_network", "AI 大師目前無法連線，請稍後重新解讀", True, {"provider":"gemini"}) from e
        except (TimeoutError, socket.timeout) as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時，請稍後重新解讀", True, {"provider":"gemini"}) from e
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀", True, {"provider":"gemini"}) from e


class OpenAICompatibleZeroCostGateway:
    def __init__(self, *, provider_id: str, api_key: str | None, model: str, base_url: str, allowed_models: set[str]):
        self.provider_id = provider_id
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        if model not in allowed_models:
            raise RuntimeError(f"model not allowed by zero-cost policy for {provider_id}: {model}")
        self.context = ssl.create_default_context()

    def configured(self) -> bool:
        return bool(self.api_key)

    def policy(self) -> dict:
        return {"provider": self.provider_id, "model": self.model, "configured": self.configured(), "cost_policy":"zero-cost-required", "paid_fallback":False}

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIUnavailable("not_configured", "AI service is not configured", False, {"provider": self.provider_id})
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Follow the supplied Master Experience Contract exactly. Return only the final reading."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.45,
            "top_p": 0.9,
            "max_tokens": 1400,
        }
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json", "Authorization":f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            choices = data.get("choices") if isinstance(data, dict) else None
            text = choices[0].get("message", {}).get("content") if isinstance(choices, list) and choices else None
            if not isinstance(text, str) or not text.strip():
                raise AIUnavailable("empty_response", "AI 大師目前沒有可用回應", True, {"provider":self.provider_id})
            return text
        except AIUnavailable:
            raise
        except urllib.error.HTTPError as e:
            diag = {"provider":self.provider_id, "http_status":int(e.code)}
            retry_after = e.headers.get("Retry-After") if e.headers else None
            if retry_after:
                diag["retry_after"] = str(retry_after)[:64]
            code = "provider_429_rate_limit" if e.code == 429 else ("provider_busy" if e.code in (500,502,503,504) else "provider_error")
            raise AIUnavailable(code, f"{self.provider_id} 暫時無法完成這次 AI 請求", True, diag) from e
        except urllib.error.URLError as e:
            raise AIUnavailable("provider_network", "AI 大師目前無法連線", True, {"provider":self.provider_id}) from e
        except (TimeoutError, socket.timeout) as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時", True, {"provider":self.provider_id}) from e
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應", True, {"provider":self.provider_id}) from e


class ZeroCostGroqGateway(OpenAICompatibleZeroCostGateway):
    provider_id = "groq"
    ALLOWED_MODELS = {"openai/gpt-oss-120b"}

    def __init__(self, api_key: str | None, model: str | None = None):
        super().__init__(
            provider_id="groq",
            api_key=api_key,
            model=model or os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b"),
            base_url="https://api.groq.com/openai/v1",
            allowed_models=self.ALLOWED_MODELS,
        )


class ZeroCostOpenRouterGateway(OpenAICompatibleZeroCostGateway):
    """Optional fixed-model OpenRouter adapter.

    The random `openrouter/free` router is deliberately forbidden because changing the
    underlying model between requests would weaken Master persona continuity.
    """
    provider_id = "openrouter"

    def __init__(self, api_key: str | None, model: str | None = None):
        selected = model or os.environ.get("OPENROUTER_MODEL", "")
        if selected == "openrouter/free":
            raise RuntimeError("random OpenRouter free router is forbidden by Master Experience policy")
        if selected and not selected.endswith(":free"):
            raise RuntimeError("OpenRouter fallback must use an explicitly fixed :free model")
        super().__init__(
            provider_id="openrouter",
            api_key=api_key,
            model=selected or "disabled:free",
            base_url="https://openrouter.ai/api/v1",
            allowed_models={selected} if selected else {"disabled:free"},
        )

    def configured(self) -> bool:
        return bool(self.api_key and self.model != "disabled:free")


class ZeroCostProviderPool:
    def __init__(self, providers: list[ProviderGateway], quality_gate: MasterExperienceQualityGate | None = None):
        self.providers = list(providers)
        self.quality_gate = quality_gate or MasterExperienceQualityGate()
        if not self.providers:
            raise RuntimeError("zero-cost provider pool requires at least one provider adapter")

    def policy(self) -> dict:
        rows = [p.policy() for p in self.providers]
        return {
            "schema": "leopardcat.ai-provider-policy/v2",
            "cost_policy": "zero-cost-required",
            "provider": "zero-cost-pool",
            "primary_provider": rows[0]["provider"],
            "providers": rows,
            "paid_fallback": False,
            "quality_contract": "master-experience/v1",
            "random_model_routing": False,
        }

    def generate(self, prompt: str) -> str:
        compiled = MASTER_EXPERIENCE_CONTRACT + "\n\n" + prompt
        configured = [p for p in self.providers if p.configured()]
        if not configured:
            raise AIUnavailable("not_configured", "AI service is not configured", False, {"provider":"zero-cost-pool"})
        failures: list[AIUnavailable] = []
        for provider in configured:
            try:
                return self.quality_gate.validate(provider.generate(compiled))
            except AIUnavailable as exc:
                failures.append(exc)
                continue
        if len(configured) == 1 and failures:
            raise failures[0]
        attempts = []
        for exc in failures:
            diag = exc.public_diagnostics()
            attempts.append({k:diag.get(k) for k in ("provider","http_status","category","retry_after") if diag.get(k) is not None} | {"code":exc.code})
        raise AIUnavailable(
            "provider_pool_exhausted",
            "所有零成本 AI 引擎目前都無法通過可用性／品質檢查；牌局已保留，請稍後重試",
            True,
            {"provider":"zero-cost-pool", "attempts":attempts},
        )
'''
(ROOT/'website/divination/ai_gateway.py').write_text(ai_gateway, encoding='utf-8')

server = (ROOT/'website/fortune_server.py').read_text(encoding='utf-8')
server = server.replace(
    'from divination.ai_gateway import ZeroCostGeminiGateway, AIUnavailable',
    'from divination.ai_gateway import ZeroCostGeminiGateway, ZeroCostGroqGateway, ZeroCostOpenRouterGateway, ZeroCostProviderPool, AIUnavailable'
)
start = server.index('def load_env_key():')
end = server.index('\nDIVINATION_ENGINE =', start)
replacement = '''def load_env_value(name):
    value = os.environ.get(name)
    if value:
        return value
    env_path = "/home/ubuntu/agentmanager/.env"
    if os.path.exists(env_path):
        try:
            with open(env_path) as f:
                for line in f:
                    if line.startswith(name + "="):
                        return line.strip().split("=", 1)[1]
        except Exception as e:
            log(f"Error reading runtime env file: {e}")
    return None


def build_ai_gateway():
    providers = [
        ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY")),
        ZeroCostGroqGateway(load_env_value("GROQ_API_KEY")),
    ]
    openrouter_key = load_env_value("OPENROUTER_API_KEY")
    openrouter_model = load_env_value("OPENROUTER_MODEL")
    if openrouter_key or openrouter_model:
        providers.append(ZeroCostOpenRouterGateway(openrouter_key, openrouter_model))
    return ZeroCostProviderPool(providers)


AI_GATEWAY = build_ai_gateway()
'''
server = server[:start] + replacement + server[end:]
(ROOT/'website/fortune_server.py').write_text(server, encoding='utf-8')

# Add protected capability.
cap_path = ROOT/'governance/capabilities.json'
cap = json.loads(cap_path.read_text(encoding='utf-8'))
cap['protected_capabilities']['ai.master-experience-provider-neutral'] = {
    'status':'protected',
    'owner':'divination',
    'contract':[
        'Changing AI providers may change the inference engine but must not change the selected Persona Pack, immutable reading result, language, or Master Experience contract.',
        'Automatic fallback may use only explicitly approved fixed models; random model routers are forbidden for the primary Master experience.',
        'Every provider receives the same compiled Master Experience prompt and equivalent generation controls.',
        'Provider/model identity must not be exposed as a new reader persona, and outputs must pass the deterministic Master Experience quality gate before display.',
        'No provider fallback may violate ai.zero-cost-fail-closed or silently enable paid inference.'
    ],
    'evidence':['website/divination/ai_gateway.py','website/tests/test_provider_pool_quality.py']
}
cap_path.write_text(json.dumps(cap, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

test = r'''import json
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
'''
(ROOT/'website/tests/test_provider_pool_quality.py').write_text(test, encoding='utf-8')

# Update legacy fail-closed contract import remains valid; add a source-level server contract.
server_test = r'''from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SERVER=(ROOT/'fortune_server.py').read_text(encoding='utf-8')

def test_runtime_builds_zero_cost_provider_pool():
    assert 'ZeroCostProviderPool' in SERVER
    assert 'ZeroCostGeminiGateway(load_env_value("GEMINI_API_KEY"))' in SERVER
    assert 'ZeroCostGroqGateway(load_env_value("GROQ_API_KEY"))' in SERVER
    assert 'OPENROUTER_MODEL' in SERVER
'''
(ROOT/'website/tests/test_provider_pool_runtime.py').write_text(server_test, encoding='utf-8')
