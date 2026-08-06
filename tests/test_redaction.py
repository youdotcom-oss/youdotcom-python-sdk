"""Tests for debug-log header redaction.

`BaseSDK` logs full request/response headers when a debug logger is attached.
`_redact_headers` keeps credentials out of those logs. These tests exist so a
future edit that passes `req.headers` straight to the logger fails CI rather
than silently leaking API keys into a customer's log aggregator.
"""

import json
import logging

import httpx
import pytest

from youdotcom import You
from youdotcom.basesdk import _redact_headers


_SEARCH_BODY = json.dumps({"results": {"web": []}})

API_KEY = "sk-super-secret-key"


def _run_with_debug_log(**client_kwargs) -> str:
    """Issue one search with debug logging on and return everything logged."""
    records: list[str] = []

    class _Capture(logging.Handler):
        def emit(self, record):
            # getMessage() already interpolates record.args.
            records.append(record.getMessage())

    logger = logging.getLogger("youdotcom.test_redaction")
    logger.handlers = []
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    logger.addHandler(_Capture())

    def handler(request):
        return httpx.Response(
            200,
            headers={
                "content-type": "application/json",
                "set-cookie": "session=super-secret-cookie",
            },
            content=_SEARCH_BODY,
        )

    # Caller-supplied, so this helper owns closing it.
    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(
            api_key_auth=API_KEY,
            server_url="http://mock.local",
            client=client,
            debug_logger=logger,
            **client_kwargs,
        ) as you:
            you.search(query="x")
    finally:
        client.close()

    return "\n".join(records)


class TestRedactHeaders:
    """Unit-level behavior of the helper itself."""

    @pytest.mark.parametrize(
        "name",
        ["Authorization", "X-API-Key", "Cookie", "Set-Cookie"],
    )
    def test_sensitive_headers_are_redacted(self, name):
        redacted = _redact_headers(httpx.Headers({name: "secret-value"}))
        assert redacted[name] == "[REDACTED]"
        assert "secret-value" not in str(redacted)

    @pytest.mark.parametrize("name", ["x-api-key", "X-API-KEY", "AuThOrIzAtIoN"])
    def test_matching_is_case_insensitive(self, name):
        assert _redact_headers(httpx.Headers({name: "secret"}))[name] == "[REDACTED]"

    def test_non_sensitive_headers_pass_through(self):
        redacted = _redact_headers(
            httpx.Headers({"Content-Type": "application/json", "User-Agent": "ua/1.0"})
        )
        assert redacted["Content-Type"] == "application/json"
        assert redacted["User-Agent"] == "ua/1.0"

    def test_original_headers_are_not_mutated(self):
        original = httpx.Headers({"X-API-Key": "secret"})
        _redact_headers(original)
        assert original["X-API-Key"] == "secret"

    def test_repeated_sensitive_header_is_fully_redacted(self):
        headers = httpx.Headers(
            [("Set-Cookie", "a=first"), ("Set-Cookie", "b=second")]
        )
        redacted = str(_redact_headers(headers))
        assert "first" not in redacted and "second" not in redacted


class TestDebugLogRedaction:
    """End-to-end: the key never reaches the debug log."""

    def test_api_key_not_logged(self):
        assert API_KEY not in _run_with_debug_log()

    def test_redaction_marker_present(self):
        assert "[REDACTED]" in _run_with_debug_log()

    def test_response_set_cookie_not_logged(self):
        assert "super-secret-cookie" not in _run_with_debug_log()

    def test_useful_context_still_logged(self):
        """Redaction must not gut the log — the request line still has to be there."""
        logged = _run_with_debug_log()
        assert "/v1/search" in logged
        assert "POST" in logged
