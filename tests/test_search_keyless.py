"""Tests for you.search() — keyless-capable ``POST /v1/agents/search``.

The search method now targets ``/v1/agents/search`` (the keyless-capable
proxy) instead of ``/v1/search``.  With no API key it runs in the free tier;
with a key the proxy forwards to the full search endpoint.

Three test layers:
- **Unit** (MockTransport): TestSearchSuccess, TestSearchErrors — fast, no server.
- **Mock server** (Go): TestSearchKeylessMockServer — verifies the keyless path
  against the mock server with no API key header.
- **Live**: tests/test_live.py::TestLiveSearchKeyless — hits the real API.
"""

import json
import os

import httpx
import pytest

from youdotcom import You
from youdotcom._version import __version__
from youdotcom.errors import (
    InternalServerErrorResponse,
    PaymentRequiredResponseError,
    UnauthorizedResponseError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)
from youdotcom.models import SearchResponse


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
        res = _sync_you(_make_handler(200)).search(query="python", count=5)
        assert isinstance(res, SearchResponse)
        assert res.results is not None
        assert res.results.web is not None
        assert len(res.results.web) == 1
        assert res.results.web[0].title == "Test Result"

    def test_keyless_search_returns_search_response(self):
        """No api_key_auth → keyless free-tier path still returns SearchResponse."""
        res = _sync_you(_make_handler(200), api_key=None).search(query="python", count=5)
        assert isinstance(res, SearchResponse)

    def test_string_enum_params_accepted(self):
        """country/safesearch/livecrawl/freshness accept plain strings."""
        res = _sync_you(_make_handler(200)).search(
            query="python",
            country="US",
            safesearch="strict",
            livecrawl="all",
            freshness="week",
        )
        assert isinstance(res, SearchResponse)

    def test_lowercase_language_is_normalized(self):
        """language='en' should be normalized to 'EN' before model validation."""
        res = _sync_you(_make_handler(200)).search(query="python", language="en")
        assert isinstance(res, SearchResponse)

    def test_lowercase_country_is_normalized(self):
        """country='us' should be normalized to 'US' before model validation."""
        res = _sync_you(_make_handler(200)).search(query="python", country="us")
        assert isinstance(res, SearchResponse)

    def test_exclude_and_boost_domains_accepted(self):
        """exclude_domains and boost_domains should be accepted as lists."""
        res = _sync_you(_make_handler(200)).search(
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

        _sync_you(handler).search(query="python")
        assert captured["method"] == "POST"
        assert "/v1/agents/search" in captured["url"]

    def test_default_user_agent_is_set(self):
        """Default UA on the request is youdotcom-python-sdk/{version}."""
        captured: dict = {}

        def handler(request):
            captured["ua"] = request.headers.get("user-agent", "")
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        _sync_you(handler).search(query="python")
        assert captured["ua"] == f"youdotcom-python-sdk/{__version__}"

    def test_custom_user_agent_passes_through(self):
        """A custom user_agent overrides the default on the wire."""
        captured: dict = {}

        def handler(request):
            captured["ua"] = request.headers.get("user-agent", "")
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        you = You(
            api_key_auth="test-key",
            server_url="http://mock.local",
            client=httpx.Client(transport=httpx.MockTransport(handler)),
        )
        you.sdk_configuration.user_agent = "my-integration/1.0"
        you.search(query="python")
        assert captured["ua"] == "my-integration/1.0"

    @pytest.mark.asyncio
    async def test_async_keyed_search_returns_search_response(self):
        res = await _async_you(_make_handler(200)).search_async(query="python", count=5)
        assert isinstance(res, SearchResponse)

    @pytest.mark.asyncio
    async def test_async_keyless_search_returns_search_response(self):
        res = await _async_you(_make_handler(200), api_key=None).search_async(query="python", count=5)
        assert isinstance(res, SearchResponse)


class TestSearchErrors:
    def test_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Insufficient credits",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            _sync_you(_make_handler(402, body)).search(query="python", count=100)
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.message == "Insufficient credits"
        assert exc_info.value.data.upgrade_url == "https://you.com/platform"

    def test_401_raises_unauthorized_error(self):
        body = json.dumps({"detail": "invalid api key"})
        with pytest.raises(UnauthorizedResponseError):
            _sync_you(_make_handler(401, body), api_key="bad-key").search(query="python")

    def test_422_raises_unprocessable_entity_error(self):
        body = json.dumps({"error": "include_domains and exclude_domains are mutually exclusive"})
        with pytest.raises(UnprocessableEntityResponseError):
            _sync_you(_make_handler(422, body)).search(query="python")

    def test_500_raises_internal_server_error(self):
        body = json.dumps({"detail": "internal server error"})
        with pytest.raises(InternalServerErrorResponse):
            _sync_you(_make_handler(500, body)).search(query="python")

    def test_4xx_fallback_raises_default_error(self):
        body = json.dumps({"detail": "rate limited"})
        with pytest.raises(YouDefaultError):
            _sync_you(_make_handler(429, body)).search(query="python")

    @pytest.mark.asyncio
    async def test_async_402_raises_payment_required_error(self):
        body = json.dumps({
            "error": "payment_required",
            "message": "Free tier limit exceeded",
            "upgrade_url": "https://you.com/platform",
        })
        with pytest.raises(PaymentRequiredResponseError) as exc_info:
            await _async_you(_make_handler(402, body)).search_async(query="python", count=100)
        assert exc_info.value.status_code == 402
        assert exc_info.value.data.error == "payment_required"

    @pytest.mark.asyncio
    async def test_async_401_raises_unauthorized_error(self):
        body = json.dumps({"detail": "unauthorized"})
        with pytest.raises(UnauthorizedResponseError):
            await _async_you(_make_handler(401, body), api_key="bad-key").search_async(query="python")

    @pytest.mark.asyncio
    async def test_async_500_raises_internal_server_error(self):
        body = json.dumps({"detail": "internal server error"})
        with pytest.raises(InternalServerErrorResponse):
            await _async_you(_make_handler(500, body)).search_async(query="python")


# ---------------------------------------------------------------------------
# Mock server tests — verify the keyless path against the Go mock server.
# The mock server's POST /v1/agents/search handler accepts requests without
# an X-API-Key header (keyless-capable). These tests require the mock server
# running on localhost:18080 (same as performance tests).
# ---------------------------------------------------------------------------


def _mock_server_url() -> str:
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def mock_server_running():
    """Skip if the mock server isn't running."""
    import socket
    from urllib.parse import urlparse

    parsed = urlparse(_mock_server_url())
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)

    try:
        with socket.create_connection((host, port), timeout=1):
            pass
    except (ConnectionRefusedError, OSError):
        pytest.skip(f"Mock server not running on {host}:{port}")


@pytest.mark.usefixtures("mock_server_running")
class TestSearchKeylessMockServer:
    """Keyless search against the Go mock server (no API key)."""

    def test_keyless_search_returns_results(self):
        """you.search() with no API key hits /v1/agents/search on the mock server."""
        you = You(server_url=_mock_server_url())
        with you:
            res = you.search(query="test query", count=5)
            assert res.results is not None
            assert res.results.web is not None
            assert len(res.results.web) > 0

    def test_keyless_search_with_string_params(self):
        """Keyless search accepts plain string params (country, freshness, safesearch)."""
        you = You(server_url=_mock_server_url())
        with you:
            res = you.search(
                query="AI news",
                count=3,
                country="US",
                freshness="week",
                safesearch="moderate",
            )
            assert res.results is not None

    @pytest.mark.asyncio
    async def test_async_keyless_search(self):
        """you.search_async() with no API key works against the mock server."""
        you = You(server_url=_mock_server_url())
        async with you:
            res = await you.search_async(query="test query", count=3)
            assert res.results is not None
            assert res.results.web is not None
