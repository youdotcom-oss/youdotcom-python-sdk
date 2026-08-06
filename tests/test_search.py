import json
import pytest
import httpx

from youdotcom import You
from youdotcom.errors import (
    ForbiddenResponseError,
    InternalServerErrorResponse,
    UnauthorizedResponseError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)
from youdotcom.models import SearchResponse


# ---------------------------------------------------------------------------
# Error tests: search() (POST /v1/search) must raise the
# consolidated *ResponseError classes.  Uses MockTransport.
# ---------------------------------------------------------------------------


class TestSearchErrors:
    """Verify search() raises the consolidated *ResponseError classes.

    These tests lock the error-class contract so a regen that mis-wires
    errors would fail CI. Each test asserts the specific error class.
    """

    def test_unauthorized(self):
        def handler(request):
            return httpx.Response(
                401,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "Invalid or expired API key"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="invalid")
        with pytest.raises(UnauthorizedResponseError):
            you.search(query="test")
        sdk_client.close()

    def test_forbidden(self):
        def handler(request):
            return httpx.Response(
                403,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "Forbidden"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises(ForbiddenResponseError):
            you.search(query="test")
        sdk_client.close()

    def test_unprocessable(self):
        def handler(request):
            return httpx.Response(
                422,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "include_domains and exclude_domains cannot be combined"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises(UnprocessableEntityResponseError):
            you.search(
                query="test",
                include_domains=["example.com"],
                exclude_domains=["spam.com"],
            )
        sdk_client.close()

    def test_internal_server_error(self):
        def handler(request):
            return httpx.Response(
                500,
                headers={"content-type": "application/json"},
                content=json.dumps({"detail": "internal server error"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises(InternalServerErrorResponse):
            you.search(query="test")
        sdk_client.close()

    def test_4xx_fallback_raises_default_error(self):
        def handler(request):
            return httpx.Response(
                429,
                headers={"content-type": "application/json"},
                content=json.dumps({"detail": "rate limited"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises(YouDefaultError):
            you.search(query="test")
        sdk_client.close()

    @pytest.mark.asyncio
    async def test_async_unauthorized(self):
        def handler(request):
            return httpx.Response(
                401,
                headers={"content-type": "application/json"},
                content=json.dumps({"detail": "unauthorized"}),
            )

        transport = httpx.MockTransport(handler)
        async_client = httpx.AsyncClient(transport=transport)
        you = You(server_url="http://mock.local", async_client=async_client, api_key_auth="bad-key")
        with pytest.raises(UnauthorizedResponseError):
            await you.search_async(query="test")
        await async_client.aclose()

    @pytest.mark.asyncio
    async def test_async_internal_server_error(self):
        def handler(request):
            return httpx.Response(
                500,
                headers={"content-type": "application/json"},
                content=json.dumps({"detail": "internal server error"}),
            )

        transport = httpx.MockTransport(handler)
        async_client = httpx.AsyncClient(transport=transport)
        you = You(server_url="http://mock.local", async_client=async_client, api_key_auth="test")
        with pytest.raises(InternalServerErrorResponse):
            await you.search_async(query="test")
        await async_client.aclose()


class TestSearchBoostDomains:
    """Verify search() forwards boost_domains in the request body."""

    def test_boost_domains_forwarded(self):
        def handler(request):
            body = json.loads(request.content)
            assert "boost_domains" in body
            assert "python.org" in body["boost_domains"]
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "results": {
                        "web": [
                            {"url": "https://python.org", "title": "Python", "description": "Python.org"}
                        ],
                    },
                    "metadata": {"q": "test", "latency": 0.1},
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        res = you.search(
            query="Python type hints",
            boost_domains=["python.org", "realpython.com"],
        )
        assert res.results is not None
        sdk_client.close()


class TestSearchSuccess:
    """Verify search() returns SearchResponse and hits POST /v1/search."""

    _SEARCH_BODY = json.dumps(
        {"results": {"web": [{"title": "Test Result", "url": "https://example.com"}]}}
    )

    def test_search_returns_search_response(self):
        def handler(request):
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=self._SEARCH_BODY
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test-key")
        res = you.search(query="python", count=5)
        assert isinstance(res, SearchResponse)
        assert res.results is not None
        assert res.results.web is not None
        assert len(res.results.web) == 1
        assert res.results.web[0].title == "Test Result"
        sdk_client.close()

    def test_posts_to_search_endpoint(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["method"] = request.method
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=self._SEARCH_BODY
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test-key")
        you.search(query="python")
        assert captured["method"] == "POST"
        assert "/v1/search" in captured["url"]
        sdk_client.close()
