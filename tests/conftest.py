"""Shared pytest configuration for the SDK test suite."""

import gc

import pytest

from tests.test_client import close_test_clients


@pytest.fixture(autouse=True)
def _close_test_clients():
    """Close every HTTP client a test built through the test factories.

    `You` never closes caller-supplied transports — that is deliberate, since
    the caller owns anything it passes in — which means each test owns the
    clients it hands to the SDK. Doing that centrally keeps the obligation
    from being forgotten at every call site, and lets the suite run clean
    under ``-W error::ResourceWarning``.

    Clients built with ``httpx.MockTransport`` have no connection pool and so
    cannot leak sockets; they do not need to be registered.

    The ``gc.collect()`` is what gives the ``filterwarnings`` guard in
    pyproject.toml its teeth. A leaked transport only emits its
    ResourceWarning when the object is finalized, which otherwise happens at
    an arbitrary later point — often after the session, where it is reported
    against nothing and fails no test. Collecting here forces the warning to
    surface inside the test that caused it.
    """
    yield
    close_test_clients()
    gc.collect()
