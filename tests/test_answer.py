"""Tests for youdotcom.answer — POST /v1/answer."""

import json

import httpx
import pytest

from youdotcom import You
from youdotcom.errors import (
    ForbiddenResponseError,
    InternalServerErrorResponse,
    PaymentRequiredResponseError,
    UnauthorizedResponseError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)
from youdotcom.models import AnswerResponse

_ANSWER_BODY = json.dumps(
    {
        "answer": "Quantum computing advanced in 2025[[1, 2]].",
        "citations": [
            {"source": "https://example.com/quantum", "excerpts": ["IBM announced a new processor."]},
            {"source": "https://example.com/ibm", "excerpts": ["Google achieved error correction.", "IBM unveiled 1000 qubits."]},
        ],
        "results": {
            "web": [
                {"url": "https://example.com/quantum", "title": "Quantum News", "snippets": ["IBM announced a new processor."], "page_age": "2025-06-25T11:41:00"},
                {"url": "https://example.com/ibm", "title": "IBM Quantum", "snippets": ["Google achieved error correction."]},
            ]
        },
    }
)


def _make_handler(status: int = 200, body: str = _ANSWER_BODY):
    def handler(request):
        return httpx.Response(
            status, headers={"content-type": "application/json"}, content=body
        )

    return handler


def _sync_you(handler, *, api_key: str | None = "test-key"):
    kwargs: dict = {
        "server_url": "http://mock.local",
        "client": httpx.Client(transport=httpx.MockTransport(handler)),
    }
    if api_key is not None:
        kwargs["api_key_auth"] = api_key
    return You(**kwargs)


def _async_you(handler, *, api_key: str | None = "test-key"):
    kwargs: dict = {
        "server_url": "http://mock.local",
        "async_client": httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    }
    if api_key is not None:
        kwargs["api_key_auth"] = api_key
    return You(**kwargs)


class TestAnswerSuccess:
    def test_returns_answer_response(self):
        res = _sync_you(_make_handler(200)).answer(query="quantum computing 2025")
        assert isinstance(res, AnswerResponse)
        assert "Quantum computing" in res.answer
        assert len(res.citations) == 2
        assert res.citations[0].source == "https://example.com/quantum"
        assert len(res.citations[0].excerpts) == 1
        assert res.citations[1].source == "https://example.com/ibm"
        assert len(res.citations[1].excerpts) == 2
        assert len(res.results.web) == 2
        assert res.results.web[0].title == "Quantum News"
        assert res.results.web[0].page_age == "2025-06-25T11:41:00"
        assert res.results.web[1].page_age is None

    def test_posts_to_answer_endpoint(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["method"] = request.method
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        _sync_you(handler).answer(query="test")
        assert captured["method"] == "POST"
        assert "/v1/answer" in captured["url"]

    def test_domain_params_serialized(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        _sync_you(handler).answer(
            query="test",
            include_domains=["nature.com", "science.org"],
            country="US",
            language="EN",
            freshness="week",
        )
        assert captured["body"]["include_domains"] == ["nature.com", "science.org"]
        assert captured["body"]["country"] == "US"
        assert captured["body"]["freshness"] == "week"

    def test_exclude_and_boost_domains_serialized(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        _sync_you(handler).answer(
            query="test",
            exclude_domains=["spam.com"],
            boost_domains=["reuters.com"],
        )
        assert captured["body"]["exclude_domains"] == ["spam.com"]
        assert captured["body"]["boost_domains"] == ["reuters.com"]
        assert "include_domains" not in captured["body"]

    def test_server_url_override_honored(self):
        """You(server_url=...) should be respected by answer.create()."""
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        you = You(
            server_url="http://custom.local",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
            api_key_auth="test-key",
        )
        you.answer(query="test")
        assert "http://custom.local" in captured["url"]
        assert "/v1/answer" in captured["url"]

    def test_lowercase_language_and_country_normalized(self):
        """language='en' and country='us' should be normalized to uppercase."""
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        _sync_you(handler).answer(query="test", language="en", country="us")
        assert captured["body"]["language"] == "EN"
        assert captured["body"]["country"] == "US"

    def test_omits_optional_params_when_not_set(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_ANSWER_BODY
            )

        _sync_you(handler).answer(query="test")
        body = captured["body"]
        assert "freshness" not in body
        assert "country" not in body
        assert "include_domains" not in body
        assert body["query"] == "test"

    @pytest.mark.asyncio
    async def test_async_returns_answer_response(self):
        res = await _async_you(_make_handler(200)).answer_async(query="quantum")
        assert isinstance(res, AnswerResponse)
        assert len(res.citations) == 2
        assert len(res.results.web) == 2


class TestAnswerErrors:
    def test_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Insufficient credits",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            _sync_you(_make_handler(402, body)).answer(query="test")
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.message == "Insufficient credits"
        assert exc_info.value.data.upgrade_url == "https://you.com/platform"

    def test_402_with_usage_fields(self):
        """402 response with optional limit/used/period/reset_at fields."""
        body = json.dumps({
            "error": "payment_required",
            "message": "Daily limit exceeded",
            "upgrade_url": "https://you.com/platform",
            "limit": 100,
            "used": 100,
            "period": "day",
            "reset_at": "2026-08-05T00:00:00Z",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            _sync_you(_make_handler(402, body)).answer(query="test")
        assert exc_info.value.data.limit == 100
        assert exc_info.value.data.used == 100
        assert exc_info.value.data.period == "day"
        assert exc_info.value.data.reset_at == "2026-08-05T00:00:00Z"

    def test_401_raises_unauthorized_error(self):
        body = json.dumps({"detail": "Invalid or expired API key"})
        with pytest.raises(UnauthorizedResponseError):
            _sync_you(_make_handler(401, body), api_key="bad-key").answer(query="test")

    def test_403_raises_forbidden_error(self):
        body = json.dumps({"detail": "Missing required scopes"})
        with pytest.raises(ForbiddenResponseError):
            _sync_you(_make_handler(403, body)).answer(query="test")

    def test_422_raises_unprocessable_entity_error(self):
        body = json.dumps({"detail": [{"type": "missing", "loc": ["body", "query"], "msg": "Field required"}]})
        with pytest.raises(UnprocessableEntityResponseError) as exc_info:
            _sync_you(_make_handler(422, body)).answer(query="")
        # FastAPI validation format: detail array
        assert exc_info.value.data.detail is not None
        assert exc_info.value.data.detail[0]["type"] == "missing"

    def test_422_json_api_format(self):
        """422 in JSON:API format {errors: [{status, code, title, detail}]}."""
        body = json.dumps({"errors": [{"status": "422", "code": "unprocessable_entity", "title": "Unprocessable Entity", "detail": "invalid request parameter(s)"}]})
        with pytest.raises(UnprocessableEntityResponseError) as exc_info:
            _sync_you(_make_handler(422, body)).answer(query="")
        assert exc_info.value.data.errors is not None
        assert exc_info.value.data.errors[0]["code"] == "unprocessable_entity"

    def test_422_search_spec_format(self):
        """422 in search spec format {error: string}."""
        body = json.dumps({"error": "invalid request parameter(s)"})
        with pytest.raises(UnprocessableEntityResponseError) as exc_info:
            _sync_you(_make_handler(422, body)).answer(query="")
        assert exc_info.value.data.error == "invalid request parameter(s)"

    def test_500_with_json_api_errors(self):
        """500 in JSON:API format {errors: [...]}."""
        body = json.dumps({"errors": [{"status": "500", "code": "internal_server_error", "title": "Internal Server Error"}]})
        with pytest.raises(InternalServerErrorResponse) as exc_info:
            _sync_you(_make_handler(500, body)).answer(query="test")
        assert exc_info.value.data.errors is not None
        assert exc_info.value.data.errors[0]["code"] == "internal_server_error"

    def test_4xx_fallback_raises_default_error(self):
        body = json.dumps({"detail": "rate limited"})
        with pytest.raises(YouDefaultError):
            _sync_you(_make_handler(429, body)).answer(query="test")

    @pytest.mark.asyncio
    async def test_async_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Insufficient credits",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            await _async_you(_make_handler(402, body)).answer_async(query="test")
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.error == "payment_required"

    @pytest.mark.asyncio
    async def test_async_500_raises_internal_server_error(self):
        body = json.dumps({"detail": "internal server error"})
        with pytest.raises(InternalServerErrorResponse):
            await _async_you(_make_handler(500, body)).answer_async(query="test")
