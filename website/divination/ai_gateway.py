from __future__ import annotations

import json
import os
import socket
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

    @staticmethod
    def _extract_text(data: object) -> str:
        """Return usable Gemini text or fail closed on any empty/malformed candidate.

        Gemini may occasionally return a syntactically valid success payload without a
        `content.parts[0].text` field (for example, an empty/safety-stopped candidate).
        That is provider unavailability from this application's point of view; it must
        never escape as KeyError/IndexError and become a platform HTTP 500.
        """
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
            if e.code == 429:
                raise AIUnavailable("free_quota_exhausted", "免費 AI 額度暫時用完，請稍後再試") from e
            if e.code in (500, 502, 503, 504):
                raise AIUnavailable("provider_busy", "AI 大師目前忙碌，請稍後重新解讀") from e
            raise AIUnavailable("provider_error", f"AI provider error {e.code}") from e
        except urllib.error.URLError as e:
            raise AIUnavailable("provider_network", "AI 大師目前無法連線，請稍後重新解讀") from e
        except (TimeoutError, socket.timeout) as e:
            raise AIUnavailable("provider_timeout", "AI 大師回應逾時，請稍後重新解讀") from e
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise AIUnavailable("invalid_response", "AI 大師目前沒有可用回應，請稍後重新解讀") from e
