"""Tests for plain-string parameter normalization.

The SDK advertises that enum-typed parameters accept plain strings in any
case so callers never have to import an enum class. `country`/`language`
normalize upward (their enum members are uppercase); `safesearch`,
`livecrawl`, `livecrawl_formats`, and `freshness` normalize downward.

Also pins the three-way `language` contract, which is easy to break:

    omitted       -> API default ("EN")
    explicit None -> field omitted entirely (no language filter)
    "en" / "EN"   -> "EN"
"""

import json
from contextlib import contextmanager

import httpx
import pytest

from youdotcom import You
from youdotcom.models import Country, Language, LiveCrawl, SafeSearch


_SEARCH_BODY = json.dumps({"results": {"web": []}})
_ANSWER_BODY = json.dumps({"answer": "hi", "citations": [], "results": {"web": []}})


@contextmanager
def _capture(response_body: str):
    """Yield (You, captured) over a mock transport, closing the client after.

    Caller-supplied transports are never closed by the SDK, so ownership of
    the client stays here.
    """
    captured: dict = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=response_body
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(
            api_key_auth="k", server_url="http://mock.local", client=client
        ) as you:
            yield you, captured
    finally:
        client.close()


def _search_body(**kwargs) -> dict:
    """Run one search and return the JSON body that went over the wire."""
    with _capture(_SEARCH_BODY) as (you, captured):
        you.search(query="x", **kwargs)
    return captured["body"]


def _answer_body(**kwargs) -> dict:
    """Run one answer call and return the JSON body that went over the wire."""
    with _capture(_ANSWER_BODY) as (you, captured):
        you.answer(query="x", **kwargs)
    return captured["body"]


class TestUppercaseParams:
    @pytest.mark.parametrize("value", ["us", "US", "uS", Country.US])
    def test_country_normalizes_to_upper(self, value):
        assert _search_body(country=value)["country"] == "US"

    @pytest.mark.parametrize("value", ["en", "EN", Language.EN])
    def test_language_normalizes_to_upper(self, value):
        assert _search_body(language=value)["language"] == "EN"

    def test_hyphenated_language_normalizes(self):
        assert _search_body(language="zh-hans")["language"] == "ZH-HANS"


class TestLowercaseParams:
    @pytest.mark.parametrize("value", ["strict", "STRICT", SafeSearch.STRICT])
    def test_safesearch_normalizes_to_lower(self, value):
        assert _search_body(safesearch=value)["safesearch"] == "strict"

    @pytest.mark.parametrize("value", ["web", "WEB", LiveCrawl.WEB])
    def test_livecrawl_normalizes_to_lower(self, value):
        assert _search_body(livecrawl=value)["livecrawl"] == "web"

    def test_livecrawl_formats_normalize_each_item(self):
        body = _search_body(livecrawl="web", livecrawl_formats=["HTML", "Markdown"])
        assert body["livecrawl_formats"] == ["html", "markdown"]

    @pytest.mark.parametrize("value", ["week", "WEEK", "Week"])
    def test_freshness_keyword_normalizes_to_lower(self, value):
        assert _search_body(freshness=value)["freshness"] == "week"

    def test_freshness_date_range_separator_normalizes(self):
        """`YYYY-MM-DDtoYYYY-MM-DD` needs a lowercase `to`; uppercase input is fixed up."""
        body = _search_body(freshness="2026-01-01TO2026-02-01")
        assert body["freshness"] == "2026-01-01to2026-02-01"

    def test_freshness_date_range_unchanged_when_already_lowercase(self):
        body = _search_body(freshness="2026-01-01to2026-02-01")
        assert body["freshness"] == "2026-01-01to2026-02-01"


class TestLanguageThreeWayContract:
    def test_omitted_uses_api_default(self):
        assert _search_body()["language"] == "EN"

    def test_explicit_none_sends_no_language(self):
        """Passing None must opt out of the filter, not fall back to the default."""
        assert "language" not in _search_body(language=None)

    def test_explicit_value_wins(self):
        assert _search_body(language="fr")["language"] == "FR"

    @pytest.mark.asyncio
    async def test_async_matches_sync(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as ac:
            async with You(
                api_key_auth="k", server_url="http://mock.local", async_client=ac
            ) as you:
                await you.search_async(query="x", language=None)
        assert "language" not in captured["body"]


class TestAnswerNormalization:
    def test_country_and_language_upper(self):
        body = _answer_body(country="us", language="en")
        assert body["country"] == "US"
        assert body["language"] == "EN"

    def test_freshness_lower(self):
        assert _answer_body(freshness="MONTH")["freshness"] == "month"

    def test_optional_params_omitted_when_unset(self):
        body = _answer_body()
        for field in ("country", "language", "freshness"):
            assert field not in body


class TestDeprecatedShimNormalization:
    """The deprecated `unified()` spelling must normalize identically."""

    def test_unified_normalizes_and_defaults_language(self):
        with _capture(_SEARCH_BODY) as (you, captured):
            with pytest.warns(DeprecationWarning):
                you.search.unified(query="x", country="us", safesearch="STRICT")

        assert captured["body"]["country"] == "US"
        assert captured["body"]["safesearch"] == "strict"
        assert captured["body"]["language"] == "EN"

    def test_unified_language_none_opts_out(self):
        with _capture(_SEARCH_BODY) as (you, captured):
            with pytest.warns(DeprecationWarning):
                you.search.unified(query="x", language=None)

        assert "language" not in captured["body"]
