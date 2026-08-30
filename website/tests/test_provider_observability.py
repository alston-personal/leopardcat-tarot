import json

import pytest

from divination.ai_gateway import AIUnavailable, ZeroCostProviderPool


class FakeProvider:
    def __init__(self, provider_id, model, *, text=None, error=None, configured=True):
        self.provider_id = provider_id
        self.model = model
        self._text = text
        self._error = error
        self._configured = configured

    def configured(self):
        return self._configured

    def policy(self):
        return {
            "provider": self.provider_id,
            "model": self.model,
            "configured": self._configured,
        }

    def generate(self, prompt):
        if self._error:
            raise self._error
        return self._text


def good_text(label="大師"):
    return (
        f"{label}看見這個牌局的核心不是急著得到答案，而是先釐清真正需要選擇的方向。"
        "眼前的訊號彼此呼應，提醒你把注意力放回可控制的條件，而不是被一時的不確定感牽著走。"
        "先整理你真正重視的排序，再觀察哪些現實條件正在改變，會比現在立刻做出結論更有幫助。"
        "當方向與界線都更清楚之後，下一步自然會比較容易辨認，也比較不會因焦慮而做出反覆的決定。"
    )


def test_trace_records_successful_provider_without_content():
    prompt_secret = "這是使用者不應出現在 trace 的私人問題"
    answer_secret = good_text("這是回答內容也不應出現在 trace。")
    pool = ZeroCostProviderPool([
        FakeProvider("gemini", "gemini-test", text=answer_secret),
        FakeProvider("groq", "groq-test", text=good_text()),
    ])

    assert pool.generate(prompt_secret) == answer_secret
    trace = pool.last_trace()

    assert trace["status"] == "success"
    assert trace["selected_provider"] == "gemini"
    assert trace["selected_model"] == "gemini-test"
    assert trace["attempts"] == [
        {"provider": "gemini", "model": "gemini-test", "status": "success"}
    ]
    encoded = json.dumps(trace, ensure_ascii=False)
    assert prompt_secret not in encoded
    assert answer_secret not in encoded


def test_trace_records_fallback_reason_and_selected_provider():
    gemini_error = AIUnavailable(
        "provider_429_quota_rejected",
        "quota",
        True,
        {"provider": "gemini", "http_status": 429, "category": "quota_rejected", "retry_after": "17"},
    )
    pool = ZeroCostProviderPool([
        FakeProvider("gemini", "gemini-test", error=gemini_error),
        FakeProvider("groq", "groq-test", text=good_text()),
    ])

    pool.generate("private question")
    trace = pool.last_trace()

    assert trace["status"] == "success"
    assert trace["selected_provider"] == "groq"
    assert trace["attempts"][0] == {
        "provider": "gemini",
        "model": "gemini-test",
        "status": "failed",
        "code": "provider_429_quota_rejected",
        "http_status": 429,
        "category": "quota_rejected",
        "retry_after": "17",
    }
    assert trace["attempts"][1] == {
        "provider": "groq", "model": "groq-test", "status": "success"
    }


def test_trace_records_both_provider_failures():
    pool = ZeroCostProviderPool([
        FakeProvider(
            "gemini",
            "gemini-test",
            error=AIUnavailable("provider_timeout", "timeout", True, {"provider": "gemini"}),
        ),
        FakeProvider(
            "groq",
            "groq-test",
            error=AIUnavailable("quality_too_short", "short", True, {"provider": "groq"}),
        ),
    ])

    with pytest.raises(AIUnavailable) as exc:
        pool.generate("private question")

    assert exc.value.code == "provider_pool_exhausted"
    trace = pool.last_trace()
    assert trace["status"] == "failed"
    assert trace["code"] == "provider_pool_exhausted"
    assert trace["attempts"] == [
        {"provider": "gemini", "model": "gemini-test", "status": "failed", "code": "provider_timeout"},
        {"provider": "groq", "model": "groq-test", "status": "failed", "code": "quality_too_short"},
    ]


def test_unconfigured_providers_are_not_attempted():
    pool = ZeroCostProviderPool([
        FakeProvider("gemini", "gemini-test", configured=False),
        FakeProvider("groq", "groq-test", text=good_text()),
    ])

    pool.generate("private question")
    trace = pool.last_trace()
    assert trace["configured_providers"] == ["groq"]
    assert trace["selected_provider"] == "groq"
