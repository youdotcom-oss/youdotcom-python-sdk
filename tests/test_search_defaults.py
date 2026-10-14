"""Tests for the flipped defaults on ``you.search`` (knowledge + highlights).

Locks the contract:

- A default ``you.search(query=...)`` call sends ``knowledge: "core"`` and
  ``extraction: {"extraction_mode": "highlights"}`` on the wire. Both are
  injected in ``_build_search_request`` (the single shared body-builder for
  the sync, async, and deprecated shim paths), so the flip covers every
  call spelling at once.
- Explicit ``None`` is the opt-out for either: ``knowledge=None`` sends no
  knowledge key and ``extraction=None`` sends no extraction key, restoring
  the pre-3.6.0 plain-search shape. Omitted vs ``None`` is distinguished
  with the same ``UNSET`` sentinel the ``language`` parameter uses.
- The deprecated ``livecrawl`` / ``livecrawl_formats`` parameters suppress
  the injection: an injected default ``extraction`` would trip the existing
  conflict ``ValueError`` against ``livecrawl``.
- An explicitly passed ``extraction`` (any mode) or ``knowledge`` passes
  through unchanged.
- ``crawl_timeout`` is stripped as before under the injected highlights
  mode (the existing plus-value rule); a default ``crawl_timeout`` value
  does not warn (default callers stay silent).
- The shims (``you.search.unified`` and ``__call__``) inherit the same
  defaults because they forward into the shared body-builder.
"""

import json
import warnings
from contextlib import contextmanager

import httpx
import pytest

from youdotcom import You


_SEARCH_BODY = json.dumps({"results": {"web": []}})


@contextmanager
def _capture():
    """Yield (You, captured) over a mock transport, closing the client after."""
    captured: dict = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(api_key_auth="k", server_url="http://mock.local", client=client) as you:
            yield you, captured
    finally:
        client.close()


def _search_body(**kwargs) -> dict:
    """Run one synchronous search; return the JSON body that went over the wire."""
    with _capture() as (you, captured):
        you.search(query="q", **kwargs)
    return captured["body"]


# ---------------------------------------------------------------------------
# Default injection
# ---------------------------------------------------------------------------


class TestDefaultInjection:
    def test_default_sends_knowledge_core(self):
        assert _search_body()["knowledge"] == "core"

    def test_default_sends_highlights_extraction(self):
        assert _search_body()["extraction"] == {"extraction_mode": "highlights"}

    def test_default_crawl_timeout_strips_silently(self):
        """The injected highlights mode strips the default ``crawl_timeout``
        (plus-value rule) without warning; default callers stay silent."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            body = _search_body()
        assert "crawl_timeout" not in body
        assert not caught


# ---------------------------------------------------------------------------
# Opt-outs
# ---------------------------------------------------------------------------


class TestDefaultOptOuts:
    def test_knowledge_none_sends_no_knowledge(self):
        assert "knowledge" not in _search_body(knowledge=None)

    def test_extraction_none_sends_no_extraction(self):
        assert "extraction" not in _search_body(extraction=None)

    def test_both_none_restores_plain_shape(self):
        """``knowledge=None, extraction=None`` restores the pre-3.6.0 body."""
        body = _search_body(knowledge=None, extraction=None)
        assert "knowledge" not in body
        assert "extraction" not in body
        assert "crawl_timeout" in body  # untouched default is 10, on the wire

    def test_knowledge_core_explicit_passes_through(self):
        assert _search_body(knowledge="core")["knowledge"] == "core"

    def test_explicit_extraction_passes_through(self):
        body = _search_body(extraction={"extraction_mode": "full_page"})
        assert body["extraction"] == {"extraction_mode": "full_page"}

    def test_highlights_total_max_tokens_passes_through(self):
        body = _search_body(
            extraction={
                "extraction_mode": "highlights",
                "highlights": {"total_max_tokens": 2048},
            }
        )
        assert body["extraction"] == {
            "extraction_mode": "highlights",
            "highlights": {"total_max_tokens": 2048},
        }
        # The caller's knowledge default is still injected.
        assert body["knowledge"] == "core"


# ---------------------------------------------------------------------------
# livecrawl guard
# ---------------------------------------------------------------------------


class TestLivecrawlGuard:
    def test_livecrawl_suppresses_extraction_injection(self):
        """The deprecated livecrawl path keeps its old plain shape: no
        injected ``extraction`` (which would trip the conflict ValueError)."""
        with pytest.warns(DeprecationWarning):
            body = _search_body(livecrawl="web")
        assert "extraction" not in body
        assert body["livecrawl"] == "web"

    def test_livecrawl_still_injects_knowledge(self):
        """Only the extraction injection is suppressed; knowledge still flips."""
        with pytest.warns(DeprecationWarning):
            body = _search_body(livecrawl="web")
        assert body["knowledge"] == "core"

    def test_livecrawl_formats_suppresses_too(self):
        with pytest.warns(DeprecationWarning):
            body = _search_body(livecrawl="all", livecrawl_formats=["markdown"])
        assert "extraction" not in body


# ---------------------------------------------------------------------------
# Shims inherit the defaults
# ---------------------------------------------------------------------------


class TestShimDefaults:
    def test_shim_call_injects_defaults(self):
        with _capture() as (you, captured):
            you.search(query="q")
        assert captured["body"]["knowledge"] == "core"
        assert captured["body"]["extraction"] == {"extraction_mode": "highlights"}

    def test_unified_injects_defaults(self):
        import warnings

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with _capture() as (you, captured):
                you.search.unified(query="q")

        assert captured["body"]["knowledge"] == "core"
        assert captured["body"]["extraction"] == {"extraction_mode": "highlights"}
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)

# ---------------------------------------------------------------------------
# Async parity
# ---------------------------------------------------------------------------


class TestDefaultInjectionAsync:
    """``search_async`` shares the injection through the same body-builder."""

    @pytest.mark.asyncio
    async def test_async_default_injects_both(self):
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
                await you.search_async(query="q")

        assert captured["body"]["knowledge"] == "core"
        assert captured["body"]["extraction"] == {"extraction_mode": "highlights"}
