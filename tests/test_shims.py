"""Tests for backward-compat sub-SDK shims with DeprecationWarning."""

import json
import warnings

import httpx
import pytest

from youdotcom import You
from youdotcom.models import SearchResponse


_SEARCH_BODY = json.dumps(
    {"results": {"web": [{"title": "Test", "url": "https://example.com"}]}}
)
_CONTENTS_BODY = json.dumps([{"url": "https://example.com", "html": "<p>Hi</p>"}])


def _you(handler, api_key="test"):
    return You(
        server_url="http://mock.local",
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        api_key_auth=api_key,
    )


class TestSearchShim:
    def test_direct_call_no_warning(self):
        you = _you(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_SEARCH_BODY))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = you.search(query="test")
            assert len(w) == 0
        assert isinstance(res, SearchResponse)

    def test_unified_emits_deprecation_warning(self):
        you = _you(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_SEARCH_BODY))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = you.search.unified(query="test")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.search()" in str(w[0].message)
        assert isinstance(res, SearchResponse)

    @pytest.mark.asyncio
    async def test_unified_async_emits_deprecation_warning(self):
        async_you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_SEARCH_BODY))),
            api_key_auth="test",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = await async_you.search.unified_async(query="test")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.search_async()" in str(w[0].message)
        assert isinstance(res, SearchResponse)


class TestContentsShim:
    def test_direct_call_no_warning(self):
        you = _you(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = you.contents(urls=["https://example.com"])
            assert len(w) == 0
        assert len(res) == 1

    def test_generate_emits_deprecation_warning(self):
        you = _you(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY))
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = you.contents.generate(urls=["https://example.com"])
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.contents()" in str(w[0].message)
        assert len(res) == 1

    @pytest.mark.asyncio
    async def test_generate_async_emits_deprecation_warning(self):
        async_you = You(
            server_url="http://mock.local",
            async_client=httpx.AsyncClient(transport=httpx.MockTransport(lambda req: httpx.Response(200, headers={"content-type": "application/json"}, content=_CONTENTS_BODY))),
            api_key_auth="test",
        )
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            res = await async_you.contents.generate_async(urls=["https://example.com"])
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "you.contents_async()" in str(w[0].message)
        assert len(res) == 1
