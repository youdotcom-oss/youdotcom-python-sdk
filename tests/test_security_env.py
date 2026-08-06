"""Tests for API-key resolution.

`get_security_from_env` reads `YDC_API_KEY` first and falls back to
`YOU_API_KEY_AUTH` for backward compatibility with the 2.3.x env-var name.
These tests lock in the precedence so accidental regressions are caught
by CI immediately.

`TestConstructorKeyResolution` covers the constructor side: how
`You(api_key_auth=...)` interacts with that env fallback. `TestEmptyKeyRejected`
pins the rejection of empty keys, which is what keeps a missing key from
silently resolving to a different identity.
"""

import json
import os

import httpx
import pytest

from youdotcom import You
from youdotcom.models import Security
from youdotcom.utils.security import get_security_from_env


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Strip both env vars before every test so no leaked value contaminates precedence."""
    monkeypatch.delenv("YDC_API_KEY", raising=False)
    monkeypatch.delenv("YOU_API_KEY_AUTH", raising=False)


def test_ydc_api_key_is_primary_when_set(monkeypatch):
    monkeypatch.setenv("YDC_API_KEY", "primary-key")
    monkeypatch.setenv("YOU_API_KEY_AUTH", "fallback-key")

    result = get_security_from_env(None, Security)

    assert result is not None
    assert result.api_key_auth == "primary-key"


def test_you_api_key_auth_fallback_when_ydc_unset(monkeypatch):
    monkeypatch.setenv("YOU_API_KEY_AUTH", "fallback-key")

    result = get_security_from_env(None, Security)

    assert result is not None
    assert result.api_key_auth == "fallback-key"


def test_no_env_returns_none():
    result = get_security_from_env(None, Security)
    assert result is None


def test_explicit_security_overrides_env(monkeypatch):
    monkeypatch.setenv("YDC_API_KEY", "env-key")

    explicit = Security(api_key_auth="explicit-key")
    result = get_security_from_env(explicit, Security)

    assert result is not None
    assert result.api_key_auth == "explicit-key"


_SEARCH_BODY = json.dumps({"results": {"web": []}})


def _sent_api_key(**client_kwargs) -> str | None:
    """Run one search through a mock transport and report the X-API-Key sent."""
    captured: dict = {}

    def handler(request):
        captured["key"] = request.headers.get("x-api-key")
        return httpx.Response(
            200, headers={"content-type": "application/json"}, content=_SEARCH_BODY
        )

    # Caller-supplied transports are never closed by the SDK, so close it here.
    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(
            server_url="http://mock.local",
            client=client,
            **client_kwargs,
        ) as you:
            you.search(query="x")
    finally:
        client.close()
    return captured["key"]


class TestConstructorKeyResolution:
    """`You(api_key_auth=...)` vs. the env-var fallback."""

    def test_explicit_key_is_sent(self):
        assert _sent_api_key(api_key_auth="explicit-key") == "explicit-key"

    def test_none_falls_back_to_env(self, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "env-key")
        assert _sent_api_key(api_key_auth=None) == "env-key"

    def test_omitted_falls_back_to_legacy_env(self, monkeypatch):
        monkeypatch.setenv("YOU_API_KEY_AUTH", "legacy-key")
        assert _sent_api_key() == "legacy-key"

    def test_callable_key_is_sent(self):
        assert _sent_api_key(api_key_auth=lambda: "from-callable") == "from-callable"


class TestEmptyKeyRejected:
    """An empty key is a caller mistake, and is rejected where it happens.

    Every endpoint requires a key, so `""` is never a valid argument — it
    means someone believed they were passing a key and weren't, nearly always
    `os.getenv("YDC_API_KEY", "")` with the variable unset. Falling back to
    the environment there would run the request under whatever identity the
    environment holds rather than the one the code asked for, so the SDK
    raises instead.
    """

    def test_empty_string_raises_at_construction(self):
        with pytest.raises(ValueError, match="api_key_auth was an empty string"):
            You(api_key_auth="")

    @pytest.mark.parametrize("value", ["", " ", "\n", "\t  "])
    def test_blank_strings_all_rejected(self, value):
        with pytest.raises(ValueError):
            You(api_key_auth=value)

    def test_raises_even_when_env_is_set(self, monkeypatch):
        """The environment must not paper over the mistake."""
        monkeypatch.setenv("YDC_API_KEY", "env-key")
        monkeypatch.setenv("YOU_API_KEY_AUTH", "legacy-key")
        with pytest.raises(ValueError):
            You(api_key_auth="")

    def test_message_points_at_the_likely_cause(self):
        with pytest.raises(ValueError) as excinfo:
            You(api_key_auth="")
        message = str(excinfo.value)
        assert 'os.getenv("YDC_API_KEY")' in message
        assert "pass None or omit the argument" in message

    def test_callable_returning_empty_raises_when_called(self):
        """A callable is resolved lazily, so it can only be checked on use."""
        # A mock transport guarantees the assertion can't depend on a network
        # call: the raise has to happen while the request is being built.
        client = httpx.Client(
            transport=httpx.MockTransport(lambda req: httpx.Response(200, json={}))
        )
        try:
            with You(api_key_auth=lambda: "", client=client) as you:  # construction is fine
                with pytest.raises(ValueError, match="callable returned an empty API key"):
                    you.search(query="x")
        finally:
            client.close()

    def test_none_is_still_the_way_to_use_the_environment(self, monkeypatch):
        monkeypatch.setenv("YDC_API_KEY", "env-key")
        assert _sent_api_key(api_key_auth=None) == "env-key"
