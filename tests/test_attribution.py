"""Tests for the ``X-Client-Info`` attribution header.

Locks two contracts:

1. ``youdotcom.utils.attribution.build_client_info_header`` produces the
   exact wire format — leading ``python-sdk`` token,
   the four optional segments in the canonical order, ``"; "`` separator
   throughout, no leading/trailing separators, no empty segments when
   the optional args are falsy. Values must be printable ASCII (excluding
   ``;``); non-ASCII, control characters, and ``;`` are rejected to
   prevent segment forgery, header injection, and encoding errors.

2. ``BaseSDK._build_request_with_client`` writes ``X-Client-Info`` at
   the same site as ``User-Agent``, every endpoint routes through it,
   so a per-endpoint drift is impossible. Exercised via ``MockTransport``
   round-trips since the established test pattern calls
   ``You.search(...)`` against a mock and inspects
   ``request.headers``.
"""

from __future__ import annotations

import contextlib
import importlib
import importlib.metadata
import json
import sys
from unittest import mock

import httpx
import pytest

from youdotcom import You
from youdotcom.utils.attribution import build_client_info_header


_SEARCH_BODY = json.dumps({"results": {"web": []}})


@contextlib.contextmanager
def _capture(**you_kwargs):
    """Yield ``(You, captured)`` over a mock transport, closing the client after.

    Mirrors the ``_capture()`` pattern in ``tests/test_extraction.py``, but
    records request *headers* (lowercased, since HTTP header names are
    case-insensitive) rather than the body. ``you_kwargs`` are forwarded to the
    ``You`` constructor so a test can vary only what it cares about.
    """
    captured: dict = {}

    def handler(request):
        captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(
            api_key_auth="k",
            server_url="http://mock.local",
            client=client,
            timeout_ms=10_000,
            **you_kwargs,
        ) as you:
            yield you, captured
    finally:
        client.close()


def _search_headers(**you_kwargs) -> dict:
    """Run one synchronous search; return the headers that went over the wire."""
    with _capture(**you_kwargs) as (you, captured):
        you.search(query="q")
    return captured["headers"]


def _expected_default_header(version: str) -> str:
    """The canonical header value when no attribution args are supplied."""
    return (
        f"python-sdk; client=youdotcom/{version}; "
        f"ua=python/{sys.version_info.major}.{sys.version_info.minor}."
        f"{sys.version_info.micro} httpx/{httpx.__version__}"
    )


# ---------------------------------------------------------------------------
# Pure helper tests — drive ``build_client_info_header`` directly.
# ---------------------------------------------------------------------------


class TestBuildClientInfoHeaderGrammar:
    """Locks the grammar portion of the wire format spec.

    These tests pin the exact wire format so a regression is caught
    at unit-test time.
    """

    def test_leading_token_is_python_sdk(self):
        out = build_client_info_header()
        assert out.startswith("python-sdk; "), out

    def test_default_call_has_only_required_segments(self):
        out = build_client_info_header()
        # Required: python-sdk; client=…; ua=…
        # Optional (None drops segment): title=, url=
        assert out == (
            f"python-sdk; client=youdotcom/{__import__('youdotcom').__version__}; "
            f"ua=python/{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro} httpx/{httpx.__version__}"
        )

    def test_app_title_appended_after_client(self):
        out = build_client_info_header(app_title="MyAgent")
        # title= comes after client= and before ua=
        parts = out.split("; ")
        assert parts[0] == "python-sdk"
        assert parts[1].startswith("client=youdotcom/")
        assert "title=MyAgent" in parts
        # ua= stays at the end
        assert parts[-1].startswith("ua=python/")

    def test_app_url_appended_after_title(self):
        out = build_client_info_header(app_title="MyAgent", app_url="https://example.com")
        # canonical order: python-sdk, client=, title=, url=, ua=
        parts = out.split("; ")
        assert parts[0] == "python-sdk"
        assert parts[1].startswith("client=youdotcom/")
        assert parts[2] == "title=MyAgent"
        assert parts[3] == "url=https://example.com"
        assert parts[-1].startswith("ua=python/")

    def test_no_extra_separators_when_optional_segments_dropped(self):
        # app_title=None and app_url=None: no ``; ;``, no leading ``;``,
        # no trailing ``;``, no empty ``=``.
        out = build_client_info_header()
        assert "; ;" not in out
        assert not out.startswith("; ")
        assert not out.endswith("; ")
        assert "=;" not in out
        assert "; ; " not in out

    def test_url_with_query_string_survives_segment_split(self):
        # URL values with query strings contain ``=``; pin that the
        # value stays intact so the SDK never feeds malformed segments.
        out = build_client_info_header(app_url="https://example.com?x=1&y=2")
        # Parse the segment by re-splitting at the first occurrence of
        # "url=" and reading until the next "; " boundary.
        url_seg_start = out.index("url=") + len("url=")
        # Trailing segment is ``ua=…``; its prefix ``; ua=`` is the
        # unambiguous separator.
        url_seg = out[url_seg_start: out.index("; ua=")]
        assert url_seg == "https://example.com?x=1&y=2"

    def test_ua_segment_contains_python_and_httpx_versions(self):
        out = build_client_info_header()
        ua_seg = out[out.index("ua=") + len("ua="):]
        assert ua_seg.startswith(f"python/{sys.version_info.major}")
        assert f" httpx/{httpx.__version__}" in ua_seg

    def test_client_segment_uses_youdotcom_version(self):
        import youdotcom

        out = build_client_info_header()
        assert f"client=youdotcom/{youdotcom.__version__}" in out


class TestBuildClientInfoHeaderEdgeCases:
    """Edge-case handling for the optional segments."""

    @pytest.mark.parametrize(
        "title,url",
        [
            ("MyAgent", "https://example.com"),
            ("Spaces In Title", "https://example.com/path?q=v"),
            ("Special&Chars!", "https://example.com/?foo=bar&baz=qux"),
        ],
    )
    def test_round_trip_through_grammar(self, title, url):
        # Sanity: any pair (title, url) reproduces the canonical order,
        # client/title/url/ua all present and segments are intact.
        out = build_client_info_header(app_title=title, app_url=url)
        parts = out.split("; ")
        assert parts[0] == "python-sdk"
        assert parts[1].startswith("client=")
        assert parts[2] == f"title={title}"
        assert parts[3] == f"url={url}"
        assert parts[4].startswith("ua=")

    def test_empty_string_title_drops_segment(self):
        """Empty string is falsy, so ``title=`` segment is dropped entirely."""
        out = build_client_info_header(app_title="")
        assert "title=" not in out

    def test_empty_string_url_drops_segment(self):
        """Empty string is falsy, so ``url=`` segment is dropped entirely."""
        out = build_client_info_header(app_url="")
        assert "url=" not in out

    @pytest.mark.parametrize(
        "bad_title",
        [
            "Evil; url=http://attacker.com",
            "line\rbreak",
            "line\nbreak",
            "Café Assistant",
            "検索アシスタント",
            "null\x00byte",
            "vert\x0btab",
        ],
    )
    def test_invalid_title_raises(self, bad_title):
        with pytest.raises(ValueError, match="app_title"):
            build_client_info_header(app_title=bad_title)

    @pytest.mark.parametrize(
        "bad_url",
        [
            "http://evil.com; title=forged",
            "http://evil.com\r",
            "http://evil.com\n",
            "http://café.com",
            "http://例え.jp",
            "http://evil.com\x00",
            "http://evil.com\x0b",
        ],
    )
    def test_invalid_url_raises(self, bad_url):
        with pytest.raises(ValueError, match="app_url"):
            build_client_info_header(app_url=bad_url)


# ---------------------------------------------------------------------------
# Construction-time validation — You.__init__ must fail fast.
# ---------------------------------------------------------------------------


class TestConstructionTimeValidation:
    """``You(app_title=..., app_url=...)`` validates at construction time."""

    @pytest.mark.parametrize(
        "bad_title",
        [
            "Evil; url=http://attacker.com",
            "Café Assistant",
            "検索アシスタント",
            "null\x00byte",
        ],
    )
    def test_invalid_app_title_raises_at_construction(self, bad_title):
        with pytest.raises(ValueError, match="app_title"):
            You(api_key_auth="k", app_title=bad_title)

    @pytest.mark.parametrize(
        "bad_url",
        [
            "http://evil.com; title=forged",
            "http://café.com",
            "http://evil.com\x00",
        ],
    )
    def test_invalid_app_url_raises_at_construction(self, bad_url):
        with pytest.raises(ValueError, match="app_url"):
            You(api_key_auth="k", app_url=bad_url)

    def test_valid_app_title_and_url_construct_fine(self):
        with You(
            api_key_auth="k",
            server_url="http://mock.local",
            app_title="MyAgent",
            app_url="https://example.com",
        ) as you:
            assert you.sdk_configuration.app_title == "MyAgent"


# ---------------------------------------------------------------------------
# Round-trip tests — header makes it onto the wire via _build_request_with_client.
# ---------------------------------------------------------------------------


class TestWireRoundTrip:
    """``X-Client-Info`` must land on the wire for every outbound request."""

    def test_search_sets_x_client_info(self):
        from youdotcom import __version__

        headers = _search_headers()
        assert "x-client-info" in headers, (
            f"X-Client-Info not on the wire. Headers: {sorted(headers)}"
        )
        assert headers["x-client-info"] == _expected_default_header(__version__)

    def test_app_title_and_url_propagate_to_wire(self):
        headers = _search_headers(
            app_title="MyAgent", app_url="https://example.com"
        )
        info = headers["x-client-info"]
        assert "title=MyAgent" in info
        assert "url=https://example.com" in info
        # Order: python-sdk; client=; title=; url=; ua=
        parts = info.split("; ")
        assert parts[0] == "python-sdk"
        assert parts[2] == "title=MyAgent"
        assert parts[3] == "url=https://example.com"

    def test_caller_supplied_http_headers_override(self):
        """A caller's own ``X-Client-Info`` wins.

        ``_build_request_with_client`` writes the attribution header *before*
        merging per-call ``http_headers``, so an explicit caller value is not
        clobbered. Pins that ordering.
        """
        with _capture(app_title="MyAgent") as (you, captured):
            you.search(query="q", http_headers={"X-Client-Info": "caller-wins"})
        assert captured["headers"]["x-client-info"] == "caller-wins"


class TestMcpAttributionNeverSent:
    """The SDK must never emit ``X-MCP-Attribution``.

    Per DX-777: that header is assembled on the MCP server, which is the only
    layer that can populate its ``keyless`` / ``payment`` / ``ip`` flags. The
    SDK sits outside Cloudflare and has no ``CF-Connecting-IP`` to read, so
    emitting it here would fabricate routing flags that the downstream
    analytics recipe treats as authoritative. This is a negative contract, so
    it needs a test that fails loudly if someone adds the header later.
    """

    @staticmethod
    def _assert_absent(headers: dict) -> None:
        offenders = [name for name in headers if "mcp" in name]
        assert not offenders, (
            f"SDK emitted an MCP-specific header: {offenders}. "
            "X-MCP-Attribution is the MCP server's responsibility."
        )

    def test_not_sent_with_no_attribution_args(self):
        self._assert_absent(_search_headers())

    def test_not_sent_with_attribution_args(self):
        self._assert_absent(
            _search_headers(app_title="MyAgent", app_url="https://example.com")
        )

    @pytest.mark.asyncio
    async def test_not_sent_on_async_path(self):
        """The async path builds its request through the same
        ``_build_request_with_client``, but assert it rather than assume it."""
        captured: dict = {}

        def handler(request):
            captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
            )

        async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        try:
            async with You(
                api_key_auth="k",
                server_url="http://mock.local",
                async_client=async_client,
                timeout_ms=10_000,
                app_title="MyAgent",
            ) as you:
                await you.search_async(query="q")
        finally:
            await async_client.aclose()

        assert "x-client-info" in captured["headers"]
        self._assert_absent(captured["headers"])


class TestVersionResolution:
    """``client=youdotcom/<version>`` tracks the resolved version.

    DX-777 requires the segment to come from ``youdotcom.__version__``
    (resolved through ``importlib.metadata`` so editable / PEP 660 installs
    report the installed distribution version) rather than a literal baked
    into the header builder.
    """

    def test_client_segment_tracks_resolved_version(self):
        """Patching the resolved version changes the header, proving no
        hardcoded literal in ``build_client_info_header``."""
        with mock.patch("youdotcom.__version__", "9.9.9-synthetic"):
            assert "client=youdotcom/9.9.9-synthetic" in build_client_info_header()

    def test_version_prefers_installed_distribution_metadata(self):
        """``_version.py`` overrides its literal with the installed metadata.

        Reloaded under a patched ``importlib.metadata.version`` so the test
        does not depend on what is actually installed. Restores the real
        module afterwards so later tests see the true version.
        """
        import youdotcom._version as version_module

        try:
            with mock.patch(
                "importlib.metadata.version", return_value="4.5.6-from-metadata"
            ):
                reloaded = importlib.reload(version_module)
                assert reloaded.__version__ == "4.5.6-from-metadata"
                assert reloaded.__user_agent__.endswith("4.5.6-from-metadata")
        finally:
            importlib.reload(version_module)

    def test_missing_distribution_falls_back_to_literal(self):
        """An uninstalled source checkout keeps the literal instead of raising."""
        import youdotcom._version as version_module

        try:
            with mock.patch(
                "importlib.metadata.version",
                side_effect=importlib.metadata.PackageNotFoundError,
            ):
                reloaded = importlib.reload(version_module)
                assert reloaded.__version__
        finally:
            importlib.reload(version_module)
