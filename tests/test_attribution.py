"""Tests for the ``X-Client-Info`` attribution header.

Locks two contracts:

1. ``youdotcom.utils.attribution.build_client_info_header`` produces the
   exact wire format — leading ``python-sdk`` token,
   the four optional segments in the canonical order, ``"; "`` separator
   throughout, no leading/trailing separators, no empty segments when
   the optional args are ``None``. Each token survives ``=`` characters
   in the value (e.g. ``url=https://example.com?x=1``) and ``;``
   characters never leak into a value.

2. ``BaseSDK._build_request_with_client`` writes ``X-Client-Info`` at
   the same site as ``User-Agent``, every endpoint routes through it,
   so a per-endpoint drift is impossible. Exercised via ``MockTransport``
   round-trips since the established test pattern calls
   ``You.search(...)`` against a mock and inspects
   ``request.headers``.
"""

from __future__ import annotations

import json
import sys

import httpx
import pytest

from youdotcom import You
from youdotcom.utils.attribution import build_client_info_header


_SEARCH_BODY = json.dumps({"results": {"web": []}})


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


# ---------------------------------------------------------------------------
# Round-trip tests — header makes it onto the wire via _build_request_with_client.
# ---------------------------------------------------------------------------


class TestWireRoundTrip:
    """``X-Client-Info`` must land on the wire for every outbound request."""

    def test_search_sets_x_client_info(self):
        captured: dict = {}

        def handler(request):
            captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=_SEARCH_BODY,
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with You(
                api_key_auth="k",
                server_url="http://mock.local",
                client=client,
                timeout_ms=10_000,
            ) as you:
                you.search(query="q")
        finally:
            client.close()

        assert "x-client-info" in captured["headers"], (
            f"X-Client-Info not on the wire. Headers: {sorted(captured['headers'].keys())}"
        )
        # And the value matches the helper's output for default args.
        from youdotcom import __version__

        expected = (
            f"python-sdk; client=youdotcom/{__version__}; "
            f"ua=python/{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro} httpx/{httpx.__version__}"
        )
        assert captured["headers"]["x-client-info"] == expected

    def test_app_title_and_url_propagate_to_wire(self):
        captured: dict = {}

        def handler(request):
            captured["headers"] = {k.lower(): v for k, v in request.headers.items()}
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=_SEARCH_BODY,
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with You(
                api_key_auth="k",
                server_url="http://mock.local",
                client=client,
                timeout_ms=10_000,
                app_title="MyAgent",
                app_url="https://example.com",
            ) as you:
                you.search(query="q")
        finally:
            client.close()

        info = captured["headers"]["x-client-info"]
        assert "title=MyAgent" in info
        assert "url=https://example.com" in info
        # Order: python-sdk; client=; title=; url=; ua=
        parts = info.split("; ")
        assert parts[0] == "python-sdk"
        assert parts[2] == "title=MyAgent"
        assert parts[3] == "url=https://example.com"
