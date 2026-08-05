"""Tests for direct methods on You that replace sub-SDK access patterns.

Verifies that you.create_run(), you.search_unified(), you.generate_contents()
work identically to the sub-SDK paths, and that sub-SDK access emits
DeprecationWarning.
"""

import json
import warnings

import httpx
import pytest

from youdotcom import You
from youdotcom.models import (
    AgentRunsBatchResponse,
    ContentsResponse,
    SearchResponse,
)


_SEARCH_BODY = json.dumps(
    {"results": {"web": [{"title": "Test", "url": "https://example.com"}]}}
)
_CONTENTS_BODY = json.dumps(
    [{"url": "https://example.com", "html": "<p>Hello</p>"}]
)
_RUNS_BODY = json.dumps(
    {
        "agent": "express",
        "input": [{"role": "user", "content": "Hello"}],
        "output": [{"type": "message.answer", "text": "Hello world"}],
    }
)


def _make_client(handler, *, api_key="test-key"):
    kwargs: dict = {
        "server_url": "http://mock.local",
        "client": httpx.Client(transport=httpx.MockTransport(handler)),
    }
    if api_key is not None:
        kwargs["api_key_auth"] = api_key
    return You(**kwargs)


class TestDirectMethodDelegation:
    def test_search_unified_delegates_to_search_unified(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        res = _make_client(handler).search_unified(query="python")
        assert isinstance(res, SearchResponse)
        assert "/v1/search" in captured["url"]

    def test_search_unified_passes_all_params(self):
        captured: dict = {}

        def handler(request):
            captured["params"] = dict(request.url.params)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        _make_client(handler).search_unified(
            query="ai news",
            count=5,
            freshness="week",
            country="US",
            include_domains="nytimes.com",
        )
        assert captured["params"]["query"] == "ai news"
        assert captured["params"]["count"] == "5"
        assert captured["params"]["freshness"] == "week"

    def test_generate_contents_delegates_to_contents_generate(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
            )

        res = _make_client(handler).generate_contents(urls=["https://example.com"])
        assert isinstance(res, list)
        assert isinstance(res[0], ContentsResponse)
        assert "/v1/contents" in captured["url"]

    def test_create_run_delegates_to_agents_runs_create(self):
        captured: dict = {}

        def handler(request):
            captured["url"] = str(request.url)
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_RUNS_BODY
            )

        res = _make_client(handler).create_run(
            request={"agent": "express", "input": "Hello"}
        )
        assert isinstance(res, AgentRunsBatchResponse)
        assert "/v1/agents/runs" in captured["url"]
        assert captured["body"]["agent"] == "express"

    @pytest.mark.asyncio
    async def test_search_unified_async_delegates(self):
        def handler(request):
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        you = You(
            api_key_auth="test-key",
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        res = await you.search_unified_async(query="python")
        assert isinstance(res, SearchResponse)

    @pytest.mark.asyncio
    async def test_generate_contents_async_delegates(self):
        def handler(request):
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY
            )

        you = You(
            api_key_auth="test-key",
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        res = await you.generate_contents_async(urls=["https://example.com"])
        assert isinstance(res, list)
        assert isinstance(res[0], ContentsResponse)

    @pytest.mark.asyncio
    async def test_create_run_async_delegates(self):
        def handler(request):
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_RUNS_BODY
            )

        you = You(
            api_key_auth="test-key",
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        )
        res = await you.create_run_async(
            request={"agent": "express", "input": "Hello"}
        )
        assert isinstance(res, AgentRunsBatchResponse)


class TestDeprecationWarnings:
    def test_search_access_emits_deprecation_warning(self):
        you = _make_client(lambda req: httpx.Response(200))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = you.search
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.search_unified()" in str(w[0].message)

    def test_agents_access_emits_deprecation_warning(self):
        you = _make_client(lambda req: httpx.Response(200))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = you.agents
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.create_run()" in str(w[0].message)

    def test_contents_access_emits_deprecation_warning(self):
        you = _make_client(lambda req: httpx.Response(200))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _ = you.contents
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.generate_contents()" in str(w[0].message)

    def test_sub_sdk_still_works_after_warning(self):
        """Sub-SDK access still returns a working instance despite the warning."""
        you = _make_client(lambda req: httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        ))
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            search_sdk = you.search
            res = search_sdk.unified(query="test")
            assert isinstance(res, SearchResponse)
