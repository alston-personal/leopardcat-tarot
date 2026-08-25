from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.request


class AIUnavailable(RuntimeError):
    def __init__(self, code: str, message: str, retryable: bool = True):
        super().__init__(message)
        self.code = code
        self.retryable = retryable


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

    def generate(self, prompt: str) -> str:
        if not self.api_key:
            raise AIUnavailable("not_configured", "AI service is not configured", False)
        payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, context=self.context, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                raise AIUnavailable("free_quota_exhausted", "免費 AI 額度暫時用完，請稍後再試") from e
            if e.code in (500, 502, 503, 504):
                raise AIUnavailable("provider_busy", "AI 大師目前忙碌，請稍後重新解讀") from e
            raise AIUnavailable("provider_error", f"AI provider error {e.code}") from e
        except TimeoutError as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時，請稍後重新解讀") from e
