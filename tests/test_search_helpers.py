"""Tests for youdotcom.search_helpers — keyless-capable ``/v1/agents/search``."""

import json

import httpx
import pytest

from youdotcom import You
from youdotcom.errors import (
    InternalServerErrorResponse,
    PaymentRequiredResponseError,
    UnauthorizedResponseError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)
from youdotcom.models import SearchResponse
from youdotcom.search_helpers import search, search_async


_SEARCH_BODY = json.dumps(
    {"results": {"web": [{"title": "Test Result", "url": "https://example.com"}]}}
)


def _make_handler(status: int = 200, body: str = _SEARCH_BODY):
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


class TestSearchSuccess:
    def test_keyed_search_returns_search_response(self):
        res = search(_sync_you(_make_handler(200)), query="python", count=5)
        assert isinstance(res, SearchResponse)
        assert res.results is not None
        assert res.results.web is not None
        assert len(res.results.web) == 1
        assert res.results.web[0].title == "Test Result"

    def test_keyless_search_returns_search_response(self):
        """No api_key_auth → keyless free-tier path still returns SearchResponse."""
        res = search(_sync_you(_make_handler(200), api_key=None), query="python", count=5)
        assert isinstance(res, SearchResponse)

    def test_string_enum_params_accepted(self):
        """country/safesearch/livecrawl/freshness accept plain strings."""
        res = search(
            _sync_you(_make_handler(200)),
            query="python",
            country="US",
            safesearch="strict",
            livecrawl="all",
            freshness="week",
        )
        assert isinstance(res, SearchResponse)

    def test_lowercase_language_is_normalized(self):
        """language='en' should be normalized to 'EN' before model validation."""
        res = search(_sync_you(_make_handler(200)), query="python", language="en")
        assert isinstance(res, SearchResponse)

    def test_lowercase_country_is_normalized(self):
        """country='us' should be normalized to 'US' before model validation."""
        res = search(_sync_you(_make_handler(200)), query="python", country="us")
        assert isinstance(res, SearchResponse)

    def test_exclude_and_boost_domains_accepted(self):
        """exclude_domains and boost_domains should be accepted as lists."""
        res = search(
            _sync_you(_make_handler(200)),
            query="python",
            exclude_domains=["spam.com"],
            boost_domains=["realpython.com"],
        )
        assert isinstance(res, SearchResponse)

    def test_posts_to_agents_search_endpoint(self):
        """Request must hit /v1/agents/search, not /v1/search."""
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["method"] = request.method
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        search(_sync_you(handler), query="python")
        assert captured["method"] == "POST"
        assert "/v1/agents/search" in captured["url"]

    @pytest.mark.asyncio
    async def test_async_keyed_search_returns_search_response(self):
        res = await search_async(_async_you(_make_handler(200)), query="python", count=5)
        assert isinstance(res, SearchResponse)

    @pytest.mark.asyncio
    async def test_async_keyless_search_returns_search_response(self):
        res = await search_async(
            _async_you(_make_handler(200), api_key=None), query="python", count=5
        )
        assert isinstance(res, SearchResponse)


class TestSearchErrors:
    def test_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Insufficient credits",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            search(_sync_you(_make_handler(402, body)), query="python", count=100)
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.message == "Insufficient credits"
        assert exc_info.value.data.upgrade_url == "https://you.com/platform"

    def test_401_raises_unauthorized_error(self):
        body = json.dumps({"detail": "invalid api key"})
        with pytest.raises(UnauthorizedResponseError):
            search(_sync_you(_make_handler(401, body), api_key="bad-key"), query="python")

    def test_422_raises_unprocessable_entity_error(self):
        body = json.dumps({"error": "include_domains and exclude_domains are mutually exclusive"})
        with pytest.raises(UnprocessableEntityResponseError):
            search(_sync_you(_make_handler(422, body)), query="python")

    def test_500_raises_internal_server_error(self):
        body = json.dumps({"detail": "internal server error"})
        with pytest.raises(InternalServerErrorResponse):
            search(_sync_you(_make_handler(500, body)), query="python")

    def test_4xx_fallback_raises_default_error(self):
        body = json.dumps({"detail": "rate limited"})
        with pytest.raises(YouDefaultError):
            search(_sync_you(_make_handler(429, body)), query="python")

    @pytest.mark.asyncio
    async def test_async_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Free tier limit exceeded",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            await search_async(_async_you(_make_handler(402, body)), query="python", count=100)
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.error == "payment_required"

    @pytest.mark.asyncio
    async def test_async_401_raises_unauthorized_error(self):
        body = json.dumps({"detail": "unauthorized"})
        with pytest.raises(UnauthorizedResponseError):
            await search_async(
                _async_you(_make_handler(401, body), api_key="bad-key"), query="python"
            )

    @pytest.mark.asyncio
    async def test_async_500_raises_internal_server_error(self):
        body = json.dumps({"detail": "internal server error"})
        with pytest.raises(InternalServerErrorResponse):
            await search_async(_async_you(_make_handler(500, body)), query="python")
