"""Tests for the new ``extraction`` parameter on ``you.search``.

Locks the contract from DX-719:

- ``extraction`` is a new typed object replacing ``livecrawl`` /
  ``livecrawl_formats`` on ``POST /v1/search``.
- ``Extraction`` models ``extra="forbid"`` so unknown keys raise
  ``ValidationError`` locally (mirrors the server's 422 on unknown keys
  inside ``extraction``).
- ``extraction_mode == "highlights"`` strips top-level ``crawl_timeout``
  on the wire (plus-value rule, server-side verified); an explicit
  non-default ``crawl_timeout`` additionally emits ``UserWarning``.
- ``extraction`` + (``livecrawl`` | ``livecrawl_formats``) is invalid;
  raises ``ValueError`` locally.
- ``livecrawl`` / ``livecrawl_formats`` continue to work but emit
  ``DeprecationWarning``.
- ``highlights.max_tokens`` is bounded to [512, 8192] (verified from
  ``youdotcom_index_api/services/highlights/schemas.py``).
"""

import json
import warnings
from contextlib import contextmanager

import httpx
import pytest
from pydantic import ValidationError

from youdotcom import You
from youdotcom.models import (
    Extraction,
    ExtractionFormat,
    ExtractionFullPage,
    ExtractionHighlights,
    ExtractionMode,
)


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
# Extraction model contract — fed directly without going through you.search()
# ---------------------------------------------------------------------------


class TestExtractionModelContract:
    """Pydantic-level checks on Extraction / ExtractionMode / ExtractionFormat."""

    def test_extraction_mode_enum_members(self):
        assert ExtractionMode.HIGHLIGHTS.value == "highlights"
        assert ExtractionMode.FULL_PAGE.value == "full_page"

    def test_extraction_format_enum_members(self):
        assert ExtractionFormat.HTML.value == "html"
        assert ExtractionFormat.MARKDOWN.value == "markdown"

    def test_extraction_omits_absent_sub_objects(self):
        """Empty-extraction round-trips as just the mode (field-level Nones
        stripped by ``model_serializer``)."""
        e = Extraction(extraction_mode="highlights")
        assert e.model_dump(exclude_none=True) == {
            "extraction_mode": ExtractionMode.HIGHLIGHTS
        }

    def test_extraction_highlights_default_no_subkeys(self):
        e = Extraction(extraction_mode="full_page")
        assert e.model_dump(exclude_none=True) == {
            "extraction_mode": ExtractionMode.FULL_PAGE
        }

    def test_extraction_highlights_with_max_tokens(self):
        e = Extraction(
            extraction_mode="highlights",
            highlights=ExtractionHighlights(max_tokens=1000),
        )
        assert e.model_dump(exclude_none=True) == {
            "extraction_mode": ExtractionMode.HIGHLIGHTS,
            "highlights": {"max_tokens": 1000},
        }

    def test_extraction_full_page_explicit_formats(self):
        e = Extraction(
            extraction_mode="full_page",
            full_page=ExtractionFullPage(
                extraction_formats=[ExtractionFormat.HTML, ExtractionFormat.MARKDOWN]
            ),
        )
        assert e.model_dump(exclude_none=True) == {
            "extraction_mode": ExtractionMode.FULL_PAGE,
            "full_page": {"extraction_formats": ["html", "markdown"]},
        }

    @pytest.mark.parametrize("value", [512, 1000, 4096, 8192])
    def test_max_tokens_in_range_ok(self, value):
        e = ExtractionHighlights(max_tokens=value)
        assert e.max_tokens == value

    def test_extraction_accepts_dict_input(self):
        """`Extraction.model_validate(dict)` lets callers construct from dicts."""
        e = Extraction.model_validate(
            {"extraction_mode": "highlights", "highlights": {"max_tokens": 512}}
        )
        assert e.extraction_mode is ExtractionMode.HIGHLIGHTS
        assert e.highlights.max_tokens == 512

    @pytest.mark.parametrize("value", [100, 511, 8193, 10000])
    def test_max_tokens_out_of_range_raises(self, value):
        with pytest.raises(ValidationError):
            ExtractionHighlights(max_tokens=value)


class TestExtractionStrictValidation:
    """``extra="forbid"`` rejects unknown keys anywhere inside ``extraction``."""

    def test_unknown_key_on_extraction_raises(self):
        with pytest.raises(ValidationError):
            Extraction.model_validate(
                {"extraction_mode": "highlights", "unknown_key": "x"}
            )

    def test_unknown_key_on_highlights_raises(self):
        with pytest.raises(ValidationError):
            Extraction.model_validate(
                {
                    "extraction_mode": "highlights",
                    "highlights": {"max_tokens": 1000, "unknown": "x"},
                }
            )

    def test_unknown_key_on_full_page_raises(self):
        with pytest.raises(ValidationError):
            Extraction.model_validate(
                {
                    "extraction_mode": "full_page",
                    "full_page": {"extraction_formats": ["html"], "unknown": "x"},
                }
            )

    def test_wrong_mode_highlights_with_full_page_raises(self):
        with pytest.raises(ValidationError):
            Extraction(
                extraction_mode="highlights",
                full_page=ExtractionFullPage(),
            )

    def test_wrong_mode_full_page_with_highlights_raises(self):
        with pytest.raises(ValidationError):
            Extraction(
                extraction_mode="full_page",
                highlights=ExtractionHighlights(),
            )

    def test_extraction_mode_required(self):
        with pytest.raises(ValidationError):
            Extraction()


# ---------------------------------------------------------------------------
# Wire contract — what goes out on POST /v1/search
# ---------------------------------------------------------------------------


class TestExtractionWireContract:
    """End-to-end MockTransport checks via you.search() / search_async()."""

    def test_extraction_omitted_sends_no_key(self):
        body = _search_body()
        assert "extraction" not in body

    def test_extraction_highlights_full_body(self):
        body = _search_body(
            extraction={
                "extraction_mode": "highlights",
                "highlights": {"max_tokens": 1000},
            }
        )
        assert body["extraction"] == {
            "extraction_mode": "highlights",
            "highlights": {"max_tokens": 1000},
        }

    def test_extraction_highlights_omits_subkeys(self):
        body = _search_body(extraction={"extraction_mode": "highlights"})
        assert body["extraction"] == {"extraction_mode": "highlights"}

    def test_extraction_full_page_default_formats(self):
        body = _search_body(extraction={"extraction_mode": "full_page"})
        assert body["extraction"] == {"extraction_mode": "full_page"}

    def test_extraction_full_page_explicit_html(self):
        body = _search_body(
            extraction={
                "extraction_mode": "full_page",
                "full_page": {"extraction_formats": ["html", "markdown"]},
            }
        )
        formats = body["extraction"]["full_page"]["extraction_formats"]
        # Enums serialize to their string values, not the enum members.
        assert sorted(formats) == ["html", "markdown"]

    def test_extraction_unknown_keys_raise_locally(self):
        with pytest.raises(ValidationError):
            with _capture() as (you, _):
                you.search(
                    query="q",
                    extraction={
                        "extraction_mode": "highlights",
                        "unknown_key": "x",
                    },
                )

    def test_extraction_max_tokens_out_of_range_raises_locally(self):
        with pytest.raises(ValidationError):
            with _capture() as (you, _):
                you.search(
                    query="q",
                    extraction={
                        "extraction_mode": "highlights",
                        "highlights": {"max_tokens": 100},  # below 512
                    },
                )

    def test_wrong_mode_config_raises_locally(self):
        with pytest.raises(ValidationError):
            with _capture() as (you, _):
                you.search(
                    query="q",
                    extraction={
                        "extraction_mode": "highlights",
                        "full_page": {},
                    },
                )


# ---------------------------------------------------------------------------
# Conflict: extraction + livecrawl/livecrawl_formats
# ---------------------------------------------------------------------------


class TestExtractionConflict:
    def test_extraction_plus_livecrawl_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be combined"):
            with _capture() as (you, _):
                you.search(
                    query="q",
                    extraction={"extraction_mode": "full_page"},
                    livecrawl="web",
                )

    def test_extraction_plus_livecrawl_formats_raises_value_error(self):
        with pytest.raises(ValueError, match="cannot be combined"):
            with _capture() as (you, _):
                you.search(
                    query="q",
                    extraction={"extraction_mode": "full_page"},
                    livecrawl_formats=["markdown"],
                )

    def test_livecrawl_alone_is_accepted_with_deprecation_warning(self):
        """``livecrawl`` without ``extraction`` is still accepted (deprecated
        but the server still supports it per DX-719 server-side verification)."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            body = _search_body(livecrawl="web", livecrawl_formats=["markdown"])

        assert body["livecrawl"] == "web"
        assert body["livecrawl_formats"] == ["markdown"]
        deprecation = [
            w for w in caught if issubclass(w.category, DeprecationWarning)
        ]
        assert len(deprecation) >= 1
        assert "livecrawl is deprecated" in str(deprecation[0].message)


# ---------------------------------------------------------------------------
# Plus-value rule: extraction_mode='highlights' strips top-level crawl_timeout
# ---------------------------------------------------------------------------


class TestExtractionPlusValueRule:
    def test_highlights_strips_default_crawl_timeout(self):
        body = _search_body(extraction={"extraction_mode": "highlights"})
        assert "crawl_timeout" not in body

    def test_highlights_strips_explicit_crawl_timeout(self):
        """An explicit non-default crawl_timeout is stripped in highlights mode
        (the server rejects the combination) and that strip is surfaced as a
        UserWarning rather than being silent."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            body = _search_body(
                extraction={"extraction_mode": "highlights"},
                crawl_timeout=30,
            )

        assert "crawl_timeout" not in body
        user = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user) == 1
        assert "crawl_timeout is ignored" in str(user[0].message)

    def test_full_page_keeps_crawl_timeout(self):
        body = _search_body(
            extraction={"extraction_mode": "full_page"},
            crawl_timeout=30,
        )
        assert body["crawl_timeout"] == 30

    def test_no_extraction_keeps_default_crawl_timeout(self):
        body = _search_body()
        assert body["crawl_timeout"] == 10


# ---------------------------------------------------------------------------
# Async parity
# ---------------------------------------------------------------------------


class TestExtractionAsync:
    """Sanity checks: ``search_async`` shares the contract with ``search``."""

    @pytest.mark.asyncio
    async def test_async_highlights_strips_crawl_timeout(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=_SEARCH_BODY,
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as ac:
            async with You(
                api_key_auth="k", server_url="http://mock.local", async_client=ac
            ) as you:
                await you.search_async(
                    query="q", extraction={"extraction_mode": "highlights"}
                )

        assert "crawl_timeout" not in captured["body"]
        assert captured["body"]["extraction"] == {"extraction_mode": "highlights"}

    @pytest.mark.asyncio
    async def test_async_highlights_warns_on_explicit_crawl_timeout(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=_SEARCH_BODY,
            )

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as ac:
                async with You(
                    api_key_auth="k", server_url="http://mock.local", async_client=ac
                ) as you:
                    await you.search_async(
                        query="q",
                        extraction={"extraction_mode": "highlights"},
                        crawl_timeout=30,
                    )

        assert "crawl_timeout" not in captured["body"]
        user = [w for w in caught if issubclass(w.category, UserWarning)]
        assert len(user) == 1
        assert "crawl_timeout is ignored" in str(user[0].message)

    @pytest.mark.asyncio
    async def test_async_conflict_raises(self):
        with pytest.raises(ValueError, match="cannot be combined"):
            with _capture() as (you, _):
                await you.search_async(
                    query="q",
                    extraction={"extraction_mode": "full_page"},
                    livecrawl="web",
                )


# ---------------------------------------------------------------------------
# Shim parity — search.unified() and search.__call__() both forward extraction
# ---------------------------------------------------------------------------


class TestExtractionShimForward:
    def test_shim_call_forwards_extraction(self):
        with _capture() as (you, captured):
            you.search(query="q", extraction={"extraction_mode": "full_page"})
        assert captured["body"]["extraction"] == {"extraction_mode": "full_page"}

    def test_unified_forwards_extraction(self):
        """``you.search.unified()`` (deprecated alias) also forwards extraction
        and emits its own deprecation warning for the alias."""
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            with _capture() as (you, captured):
                you.search.unified(
                    query="q", extraction={"extraction_mode": "highlights"}
                )

        assert captured["body"]["extraction"] == {"extraction_mode": "highlights"}
        assert "crawl_timeout" not in captured["body"]
        msgs = [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]
        # Both the unified() deprecation and the livecrawl deprecation fire.
        assert any("unified" in m for m in msgs)
