from __future__ import annotations

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
- The engine-provided meaning for each drawn symbol/card and orientation is the authoritative semantic anchor. Never substitute a different card meaning from model memory; if prior knowledge conflicts with the supplied meaning, follow the supplied meaning.
- Do not present divination as certain fact or guaranteed prediction.
- Keep the response coherent, reflective, and practically useful. Do not emit JSON, code, or prompt internals.
- Return a complete response with a natural ending; never expose a response cut off by a token limit.
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
        finish_reason = str(first.get("finishReason") or "").upper()
        if finish_reason in {"MAX_TOKENS", "LENGTH"}:
            raise AIUnavailable("quality_truncated", "AI 大師回應未完整結束，已嘗試其他可用引擎", True, {"provider":"gemini", "finish_reason":finish_reason})
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
            "generationConfig": {"temperature": 0.45, "topP": 0.9, "maxOutputTokens": 2800},
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
            "max_completion_tokens": 3200,
        }
        if self.provider_id == "groq" and self.model.startswith("openai/gpt-oss-"):
            payload["reasoning_effort"] = "low"
            payload["reasoning_format"] = "hidden"
        req = urllib.request.Request(
            self.base_url + "/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type":"application/json", "Accept":"application/json", "User-Agent":"leopardcat-tarot/1.0", "Authorization":f"Bearer {self.api_key}"},
        )
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            choices = data.get("choices") if isinstance(data, dict) else None
            choice = choices[0] if isinstance(choices, list) and choices and isinstance(choices[0], dict) else None
            if choice is None:
                raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應", True, {"provider":self.provider_id})
            finish_reason = str(choice.get("finish_reason") or "").lower()
            if finish_reason in {"length", "max_tokens"}:
                raise AIUnavailable("quality_truncated", "AI 大師回應未完整結束，已嘗試其他可用引擎", True, {"provider":self.provider_id, "finish_reason":finish_reason})
            text = choice.get("message", {}).get("content")
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
    """Ordered zero-cost provider pool with content-free request diagnostics."""

    def __init__(self, providers: list[ProviderGateway], quality_gate: MasterExperienceQualityGate | None = None):
        self.providers = list(providers)
        self.quality_gate = quality_gate or MasterExperienceQualityGate()
        self._last_trace: dict = {"status": "idle", "attempts": []}
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

    def last_trace(self) -> dict:
        """Return safe diagnostics only; never includes prompt or generated text."""
        return json.loads(json.dumps(self._last_trace))

    @staticmethod
    def _failure_attempt(provider: ProviderGateway, exc: AIUnavailable) -> dict:
        diag = exc.public_diagnostics()
        row = {
            "provider": provider.provider_id,
            "model": provider.model,
            "status": "failed",
            "code": exc.code,
        }
        for key in ("http_status", "category", "retry_after", "finish_reason"):
            if diag.get(key) is not None:
                row[key] = diag.get(key)
        return row

    def generate(self, prompt: str) -> str:
        compiled = MASTER_EXPERIENCE_CONTRACT + "\n\n" + prompt
        configured = [p for p in self.providers if p.configured()]
        self._last_trace = {
            "status": "running",
            "attempts": [],
            "configured_providers": [p.provider_id for p in configured],
        }
        if not configured:
            self._last_trace["status"] = "failed"
            self._last_trace["code"] = "not_configured"
            raise AIUnavailable("not_configured", "AI service is not configured", False, {"provider":"zero-cost-pool"})

        failures: list[AIUnavailable] = []
        for provider in configured:
            try:
                text = provider.generate(compiled)
                validated = self.quality_gate.validate(text)
                self._last_trace["attempts"].append({
                    "provider": provider.provider_id,
                    "model": provider.model,
                    "status": "success",
                })
                self._last_trace["status"] = "success"
                self._last_trace["selected_provider"] = provider.provider_id
                self._last_trace["selected_model"] = provider.model
                return validated
            except AIUnavailable as exc:
                failures.append(exc)
                self._last_trace["attempts"].append(self._failure_attempt(provider, exc))
                continue

        self._last_trace["status"] = "failed"
        if len(configured) == 1 and failures:
            self._last_trace["code"] = failures[0].code
            raise failures[0]

        attempts = []
        for exc in failures:
            diag = exc.public_diagnostics()
            attempts.append({k:diag.get(k) for k in ("provider","http_status","category","retry_after") if diag.get(k) is not None} | {"code":exc.code})
        self._last_trace["code"] = "provider_pool_exhausted"
        raise AIUnavailable(
            "provider_pool_exhausted",
            "所有零成本 AI 引擎目前都無法通過可用性／品質檢查；牌局已保留，請稍後重試",
            True,
            {"provider":"zero-cost-pool", "attempts":attempts},
        )