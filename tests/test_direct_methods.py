"""Tests for the direct methods on You.

Verifies that you.contents() and you.search() hit the
correct endpoints, pass params correctly, and work in both sync and
async modes.  Uses httpx.MockTransport (no live server required).
"""

import json

import httpx
import pytest

from youdotcom import You
from youdotcom.models import (
    ContentsResponse,
    SearchResponse,
)


_SEARCH_BODY = json.dumps(
    {"results": {"web": [{"title": "Test", "url": "https://example.com"}]}}
)
_CONTENTS_BODY = json.dumps(
    [{"url": "https://example.com", "html": "<p>Hello</p>"}]
)


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


# ---------------------------------------------------------------------------
# you.search() — POST /v1/search
# ---------------------------------------------------------------------------


class TestSearchDirect:
    def test_returns_search_response(self):
        res = _sync_you(lambda req: httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        )).search(query="python")
        assert isinstance(res, SearchResponse)
        assert res.results is not None
        assert res.results.web is not None
        assert len(res.results.web) == 1

    def test_posts_to_search_endpoint(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["method"] = request.method
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        _sync_you(handler).search(query="test")
        assert captured["method"] == "POST"
        assert "/v1/search" in captured["url"]

    def test_passes_params_in_body(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        _sync_you(handler).search(
            query="ai news",
            count=5,
            freshness="week",
            country="US",
            include_domains=["nature.com"],
        )
        assert captured["body"]["query"] == "ai news"
        assert captured["body"]["count"] == 5
        assert captured["body"]["freshness"] == "week"
        assert captured["body"]["include_domains"] == ["nature.com"]

    @pytest.mark.asyncio
    async def test_async_returns_search_response(self):
        res = await _async_you(lambda req: httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        )).search_async(query="python")
        assert isinstance(res, SearchResponse)


# ---------------------------------------------------------------------------
# you.contents() — POST /v1/contents
# ---------------------------------------------------------------------------


class TestContentsDirect:
    def test_returns_contents_response_list(self):
        res = _sync_you(lambda req: httpx.Response(
            200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
        )).contents(urls=["https://example.com"])
        assert isinstance(res, list)
        assert isinstance(res[0], ContentsResponse)
        assert res[0].url == "https://example.com"

    def test_posts_to_contents_endpoint(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["method"] = request.method
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
            )

        _sync_you(handler).contents(urls=["https://example.com"])
        assert captured["method"] == "POST"
        assert "/v1/contents" in captured["url"]

    def test_passes_urls_in_body(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
            )

        _sync_you(handler).contents(urls=["https://example.com", "https://python.org"])
        assert captured["body"]["urls"] == ["https://example.com", "https://python.org"]

    @pytest.mark.asyncio
    async def test_async_returns_contents_response_list(self):
        res = await _async_you(lambda req: httpx.Response(
            200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
        )).contents_async(urls=["https://example.com"])
        assert isinstance(res, list)
        assert isinstance(res[0], ContentsResponse)
