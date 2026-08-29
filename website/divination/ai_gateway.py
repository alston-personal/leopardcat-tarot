from __future__ import annotations

import json
import os
import socket
import ssl
import urllib.error
import urllib.request


class AIUnavailable(RuntimeError):
    def __init__(
        self,
        code: str,
        message: str,
        retryable: bool = True,
        provider: dict | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.retryable = retryable
        self.provider = provider or {}

    def public_diagnostics(self) -> dict:
        """Return provider metadata that is safe to expose to the browser.

        Never include API keys, project identifiers, full upstream messages or request
        payloads. The goal is to distinguish provider quota/billing/rate-limit states
        without leaking credentials or user content.
        """
        return dict(self.provider)


class ZeroCostGeminiGateway:
    """Fail-closed gateway: one explicitly allowed model, no paid fallback.

    IMPORTANT: code cannot discover whether the Google Cloud project behind an API key
    has billing enabled. Operational zero-cost still requires a key from a billing-disabled
    Free Tier project. This class prevents silent provider/model fallback and treats quota/
    upstream failures as temporary unavailability.
    """

    ALLOWED_MODELS = {"gemini-2.5-flash"}

    def __init__(self, api_key: str | None, model: str | None = None) -> None:
        self.api_key = api_key
        self.model = model or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        if self.model not in self.ALLOWED_MODELS:
            raise RuntimeError(f"model not allowed by zero-cost policy: {self.model}")
        self.context = ssl.create_default_context()

    def policy(self) -> dict:
        return {
            "cost_policy": "zero-cost-required",
            "provider": "gemini",
            "model": self.model,
            "paid_fallback": False,
            "billing_state_detectable_by_runtime": False,
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
        """Classify a Google 429 conservatively.

        HTTP 429 is not proof that Free Tier allowance is exhausted. Google also uses
        RESOURCE_EXHAUSTED for rate limits, billing/spend state and quota provisioning.
        """
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
        quota_violations: list[dict] = []
        details = error.get("details")
        if isinstance(details, list):
            for detail in details:
                if not isinstance(detail, dict):
                    continue
                violations = detail.get("violations")
                if not isinstance(violations, list):
                    continue
                for violation in violations[:8]:
                    if not isinstance(violation, dict):
                        continue
                    safe = {}
                    quota_metric = violation.get("quotaMetric")
                    quota_id = violation.get("quotaId")
                    if isinstance(quota_metric, str) and quota_metric:
                        safe["quota_metric"] = quota_metric[:160]
                    if isinstance(quota_id, str) and quota_id:
                        safe["quota_id"] = quota_id[:160]
                    if safe:
                        quota_violations.append(safe)
        if quota_violations:
            diagnostics["quota_violations"] = quota_violations
        return diagnostics

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIUnavailable("not_configured", "AI service is not configured", False)
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                raw = response.read().decode("utf-8")
            data = json.loads(raw)
            return self._extract_text(data)
        except AIUnavailable:
            raise
        except urllib.error.HTTPError as e:
            provider = self._safe_http_diagnostics(e)
            if e.code == 429:
                category = str(provider.get("category") or "resource_exhausted")
                raise AIUnavailable(
                    f"provider_429_{category}",
                    "Google Gemini 暫時拒絕這次 AI 請求；可能是 quota、rate limit、billing 狀態或供應商端額度異常，請稍後再試",
                    True,
                    provider,
                ) from e
            if e.code in (500, 502, 503, 504):
                raise AIUnavailable("provider_busy", "AI 大師目前忙碌，請稍後重新解讀", True, provider) from e
            raise AIUnavailable("provider_error", f"AI provider error {e.code}", True, provider) from e
        except urllib.error.URLError as e:
            raise AIUnavailable("provider_network", "AI 大師目前無法連線，請稍後重新解讀") from e
        except (TimeoutError, socket.timeout) as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時，請稍後重新解讀") from e
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀") from e
