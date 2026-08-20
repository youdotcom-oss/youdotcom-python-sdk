"""Tests for the ``X-Client-Info`` attribution header.

Locks two contracts:

1. ``youdotcom.utils.attribution.build_client_info_header`` produces the
   exact wire format — leading ``sdk`` token, the three optional
   segments (``client=``, ``title=``, ``url=``) in the canonical order,
   ``"; "`` separator throughout, no leading/trailing separators, no empty
   segments when the optional args are falsy. Values must be printable
   ASCII excluding ``;``, and ``app_name`` / ``app_version`` also exclude
   ``/``; non-ASCII, control characters and delimiters are rejected to
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
import pathlib
import re
import importlib.metadata
import json
import sys
from unittest import mock

import httpx
import pytest

from youdotcom import You
from youdotcom.utils.attribution import (
    build_client_info_header,
    validate_attribution_arg,
)


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


def _expected_default_header() -> str:
    """The canonical header value when no attribution args are supplied."""
    return (
        f"sdk; ua=python/{sys.version_info.major}.{sys.version_info.minor}."
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

    def test_leading_token_is_sdk(self):
        """The source token names the channel, matching `mcp` / `skill`.

        A single lowercase word is also the only shape that parses under the
        analytics recipe as written; a hyphenated token makes the source column
        come back empty on every SDK row.
        """
        out = build_client_info_header()
        assert out.startswith("sdk; "), out
        assert out.split("; ")[0] == "sdk"

    def test_default_call_has_only_required_segments(self):
        """Undeclared callers emit just the source token and the runtime.

        Mirrors the MCP server's `mcp; ua=...` row: `client=` is dropped
        entirely rather than filled with the SDK's own identity, which would
        make the column constant across every row.
        """
        out = build_client_info_header()
        assert out == (
            f"sdk; ua=python/{sys.version_info.major}.{sys.version_info.minor}."
            f"{sys.version_info.micro} httpx/{httpx.__version__}"
        )
        assert "client=" not in out

    def test_app_title_appended_after_client(self):
        out = build_client_info_header(
            app_name="acme-bot", app_version="2.4.0", app_title="MyAgent"
        )
        # title= comes after client= and before ua=
        parts = out.split("; ")
        assert parts[0] == "sdk"
        assert parts[1] == "client=acme-bot/2.4.0"
        assert "title=MyAgent" in parts
        # ua= stays at the end
        assert parts[-1].startswith("ua=python/")

    def test_app_url_appended_after_title(self):
        out = build_client_info_header(
            app_name="acme-bot",
            app_version="2.4.0",
            app_title="MyAgent",
            app_url="https://example.com",
        )
        # canonical order: sdk, client=, title=, url=, ua=
        parts = out.split("; ")
        assert parts[0] == "sdk"
        assert parts[1] == "client=acme-bot/2.4.0"
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

    def test_client_segment_never_names_the_sdk_itself(self):
        """`client=` is caller identity, never the SDK's own.

        The SDK's identity and version travel in the `User-Agent`; duplicating
        them here would make the segment constant for all SDK traffic. The
        MCP server applies the same rule -- it never emits `client=mcp/...`.
        """
        import youdotcom

        out = build_client_info_header()
        assert "youdotcom" not in out
        assert youdotcom.__version__ not in out

    def test_language_is_recoverable_from_the_ua_segment(self):
        """`sdk` names the channel, so the language must come from `ua=`.

        This is the signal that distinguishes the Python SDK from the
        TypeScript one (which reports `node/...`), and unlike the
        `User-Agent` it cannot be overridden by a wrapping integration.
        """
        out = build_client_info_header(app_name="youdotcom-temporal", app_version="1.0.1")
        ua_seg = out[out.index("ua=") + len("ua="):]
        assert ua_seg.startswith("python/")


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
        out = build_client_info_header(
            app_name="acme-bot", app_version="2.4.0", app_title=title, app_url=url
        )
        parts = out.split("; ")
        assert parts[0] == "sdk"
        assert parts[1] == "client=acme-bot/2.4.0"
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
        headers = _search_headers()
        assert "x-client-info" in headers, (
            f"X-Client-Info not on the wire. Headers: {sorted(headers)}"
        )
        assert headers["x-client-info"] == _expected_default_header()

    def test_app_title_and_url_propagate_to_wire(self):
        headers = _search_headers(
            app_name="acme-bot",
            app_version="2.4.0",
            app_title="MyAgent",
            app_url="https://example.com",
        )
        info = headers["x-client-info"]
        assert "title=MyAgent" in info
        assert "url=https://example.com" in info
        # Order: sdk; client=; title=; url=; ua=
        parts = info.split("; ")
        assert parts[0] == "sdk"
        assert parts[1] == "client=acme-bot/2.4.0"
        assert parts[2] == "title=MyAgent"
        assert parts[3] == "url=https://example.com"

    def test_integration_is_distinguishable_from_direct_sdk_use(self):
        """The three traffic segments must be separable on the wire.

        Raw-HTTP callers send no header at all, so the interesting pair is
        direct SDK use vs a first-party integration wrapping the SDK. `client=`
        carries that distinction structurally, rather than depending on an
        integration remembering to set a free-text title.
        """
        direct = _search_headers()["x-client-info"]
        wrapped = _search_headers(
            app_name="youdotcom-temporal", app_version="1.0.1"
        )["x-client-info"]

        assert "client=" not in direct
        assert "client=youdotcom-temporal/1.0.1" in wrapped
        # Both are still identifiably the Python SDK.
        for info in (direct, wrapped):
            assert info.split("; ")[0] == "sdk"
            assert "; ua=python/" in info

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
    """The SDK version resolves through ``importlib.metadata``.

    It reaches the wire via the ``User-Agent``, not ``X-Client-Info``:
    ``client=`` carries the *caller*, so duplicating the SDK's own version
    there would make the segment constant for all SDK traffic. These tests
    pin the resolution path (editable / PEP 660 installs must report the
    installed distribution version) and that split.
    """

    def test_sdk_version_is_carried_by_the_user_agent_not_the_header(self):
        """The SDK version lives in ``User-Agent``, not ``X-Client-Info``.

        ``client=`` is caller identity, so the SDK's own version has exactly one
        home. This pins that split, and the ``User-Agent`` half is what an
        integration must preserve (append, not replace) to keep it visible.
        """
        import youdotcom
        from youdotcom._version import __user_agent__

        assert youdotcom.__version__ in __user_agent__
        assert youdotcom.__version__ not in build_client_info_header()

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
                # Compare against pyproject, not just truthiness: a stale but
                # non-empty literal is exactly the drift that shipped on 3.1.1.
                pyproject = pathlib.Path(__file__).parent.parent / "pyproject.toml"
                declared = re.search(
                    r'^version = "([^"]+)"', pyproject.read_text(), re.M
                ).group(1)
                assert reloaded.__version__ == declared
        finally:
            importlib.reload(version_module)


class TestClientSegmentValidation:
    """`app_name` / `app_version` rules.

    These two feed `client=<name>/<version>`, which the analytics side splits
    on `/` to derive `client_name` and `client_version`. A `/` inside either
    half therefore corrupts both columns silently, so it is rejected the same
    way `;` is -- fail at construction, not silently downstream.
    """

    def test_name_without_version_emits_bare_name(self):
        out = build_client_info_header(app_name="acme-bot")
        assert "; client=acme-bot; " in out

    def test_name_and_version_join_with_slash(self):
        out = build_client_info_header(app_name="acme-bot", app_version="2.4.0")
        assert "; client=acme-bot/2.4.0; " in out

    def test_version_without_name_is_dropped_by_the_builder(self):
        """The builder has no slot for a bare version, so it emits nothing.

        `You.__init__` rejects this combination outright; the builder stays
        permissive so it is never the thing that raises mid-request.
        """
        out = build_client_info_header(app_version="2.4.0")
        assert "client=" not in out

    @pytest.mark.parametrize("bad", ["acme/bot", "acme;bot", "acmé", "acme\nbot"])
    def test_invalid_app_name_raises(self, bad):
        with pytest.raises(ValueError, match="app_name"):
            build_client_info_header(app_name=bad)

    @pytest.mark.parametrize("bad", ["2/4", "2;4", "2.4.0é"])
    def test_invalid_app_version_raises(self, bad):
        with pytest.raises(ValueError, match="app_version"):
            build_client_info_header(app_name="acme-bot", app_version=bad)

    def test_version_without_name_raises_at_construction(self):
        with pytest.raises(ValueError, match="app_version requires app_name"):
            You(api_key_auth="k", app_version="2.4.0")

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"app_name": "acme/bot"},
            {"app_name": "acme-bot", "app_version": "2/4"},
        ],
    )
    def test_slash_rejected_at_construction(self, kwargs):
        with pytest.raises(ValueError, match="client=<name>/<version>"):
            You(api_key_auth="k", **kwargs)


class TestConstructorSignature:
    """The attribution args are keyword-only; the pre-existing ones are not.

    Pinning both halves. The four attribution parameters are new in 3.1.2, so
    making them keyword-only costs no caller anything and leaves room to add or
    reorder attribution args later without a breaking change. The nine
    parameters before them must stay positional-or-keyword, because
    `You("api-key")` is a shape released callers may already depend on.
    """

    def test_attribution_args_are_keyword_only(self):
        import inspect

        params = inspect.signature(You.__init__).parameters
        for name in ("app_name", "app_version", "app_title", "app_url"):
            assert params[name].kind is inspect.Parameter.KEYWORD_ONLY, name

    def test_api_key_still_accepted_positionally(self):
        """Guards against a `*` creeping further up the signature."""
        import inspect

        params = inspect.signature(You.__init__).parameters
        # All nine, not just the first: a `*` creeping up the signature would
        # demote the rest and break `You(key, 0)` for released callers, which an
        # api_key_auth-only assertion cannot see.
        for name in (
            "api_key_auth",
            "server_idx",
            "url_params",
            "server_url",
            "client",
            "async_client",
            "retry_config",
            "timeout_ms",
            "debug_logger",
        ):
            assert (
                params[name].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            ), f"{name} must stay positional-or-keyword"
        # `with` so the SDK-owned transports are closed; this suite runs under
        # `error::ResourceWarning`.
        with You("some-key") as client:
            assert client.sdk_configuration.security is not None


class TestFalsyAttributionArgs:
    """Falsy values must not slip past the pairing guard.

    The builder drops `client=` for any *falsy* `app_name`, so a guard written
    against `is None` leaves a hole: `app_name=""` with a version passes
    validation and then emits no `client=` at all, losing both values with no
    error. `os.getenv("APP_NAME", "")` produces exactly that shape.
    """

    def test_empty_name_with_version_raises_at_construction(self):
        with pytest.raises(ValueError, match="app_version requires app_name"):
            You(api_key_auth="k", app_name="", app_version="2.4.0")

    def test_empty_name_with_version_omits_segment_in_the_builder(self):
        """The builder stays permissive -- it must not raise, nor invent a segment.

        Only ``You.__init__`` rejects this combination; the builder runs
        per-request, so it must never be the thing that raises mid-flight.
        """
        out = build_client_info_header(app_name="", app_version="2.4.0")
        assert "client=" not in out

    def test_empty_version_with_name_keeps_the_name(self):
        """A falsy version is simply unset, which is a supported shape."""
        out = build_client_info_header(app_name="acme", app_version="")
        assert "; client=acme; " in out

    def test_both_falsy_is_accepted_and_omits_the_segment(self):
        with You(api_key_auth="k", app_name="", app_version="") as client:
            assert client.sdk_configuration.app_name == ""
        assert "client=" not in build_client_info_header(app_name="", app_version="")


class TestSemicolonAlwaysRejected:
    """`;` rejection must survive a `forbidden` override.

    `forbidden` adds to the rejected set rather than replacing it. If it
    replaced it, a caller passing `forbidden="/"` would silently lose the `;`
    check -- reopening segment forgery on the one path this validator exists to
    protect.
    """

    @pytest.mark.parametrize("forbidden", ["", "/", "@#"])
    def test_semicolon_rejected_regardless_of_override(self, forbidden):
        with pytest.raises(ValueError, match="the segment delimiter"):
            validate_attribution_arg("x", "a;b", forbidden=forbidden)

    def test_override_is_additive_not_a_replacement(self):
        """One call must reject BOTH the override char and the always-on ``;``.

        Asserting only that ``forbidden="/"`` rejects ``/`` passes under
        replacement semantics too, so it proves nothing about additivity. The
        discriminating assertion is that ``;`` is still rejected by that same
        call.
        """
        validate_attribution_arg("x", "a/b")  # `/` is not forbidden by default
        with pytest.raises(ValueError, match="the client=<name>/<version>"):
            validate_attribution_arg("app_name", "a/b", forbidden="/")
        with pytest.raises(ValueError, match="the segment delimiter"):
            validate_attribution_arg("app_name", "a;b", forbidden="/")


class TestAttributionValueTypesAndWhitespace:
    """Values are interpolated verbatim, so shape errors must fail fast.

    Every doc surface promises `ValueError` at construction time. Without a type
    guard a non-`str` either raises an opaque `TypeError` from inside the
    character loop, or -- worse -- a list of single characters passes every
    check and ships `title=['a', 'b']`. Whitespace is the same class: falsy
    gates downstream treat `" "` as absent, so it ships `client= /1.0`, and a
    padded value becomes an analytics key that never groups with its unpadded
    rows.
    """

    @pytest.mark.parametrize("bad", [["a", "b"], 123, 2.4, b"acme", None.__class__])
    def test_non_str_raises_value_error_naming_the_param(self, bad):
        with pytest.raises(ValueError, match="app_title must be a str"):
            build_client_info_header(app_title=bad)

    def test_list_of_chars_does_not_slip_through(self):
        """Each element is a 1-char printable string, so the loop alone passes."""
        with pytest.raises(ValueError, match="must be a str"):
            build_client_info_header(app_title=["a", "b"])

    @pytest.mark.parametrize("bad", [" ", "  ", "\t", " acme ", "acme "])
    def test_whitespace_padded_or_only_raises(self, bad):
        with pytest.raises(ValueError, match="whitespace"):
            build_client_info_header(app_name=bad)

    def test_interior_space_is_still_allowed(self):
        """Only the edges are rejected; `title=Acme Bot` is a legitimate value."""
        assert "title=Acme Bot" in build_client_info_header(app_title="Acme Bot")
        assert "client=acme bot" in build_client_info_header(app_name="acme bot")

    def test_whitespace_name_with_version_cannot_ship_an_empty_client(self):
        with pytest.raises(ValueError, match="whitespace"):
            You(api_key_auth="k", app_name=" ", app_version="1.0")


class TestGeneratedUaSegmentIsDefensive:
    """The one segment the builder generates itself must never break a request.

    `httpx.__version__` is interpolated without caller involvement, so a
    vendored, forked or distro-patched httpx could inject `;` (forging a
    segment) or non-ASCII (dying inside httpx header encoding, with no SDK
    frame in the traceback), or omit the dunder entirely.
    """

    @pytest.mark.parametrize(
        "version", ["0.28.1; client=forged/9.9.9", "0.28.1-café", "1.0/2"]
    )
    def test_malformed_httpx_version_degrades_to_unknown(self, version):
        with mock.patch.object(httpx, "__version__", version):
            out = build_client_info_header()
        assert out.endswith("httpx/unknown")
        assert out.count(";") == 1  # only the sdk -> ua separator

    def test_missing_dunder_does_not_raise(self):
        with mock.patch.object(httpx, "__version__", None):
            delattr(httpx, "__version__")
            try:
                assert build_client_info_header().endswith("httpx/unknown")
            finally:
                httpx.__version__ = httpx.__dict__.get("__version__") or "0.28.1"

    def test_normal_version_is_passed_through(self):
        with mock.patch.object(httpx, "__version__", "0.28.1"):
            assert build_client_info_header().endswith("httpx/0.28.1")
