"""Tests for the hand-applied env-var precedence in `get_security_from_env`.

`get_security_from_env` reads `YDC_API_KEY` first and falls back to
`YOU_API_KEY_AUTH` for backward compatibility with the 2.3.x env-var name.
These tests lock in the precedence so a future Speakeasy regen (which
would revert this hand-edit) is caught by CI immediately.
"""

import os

import pytest

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
