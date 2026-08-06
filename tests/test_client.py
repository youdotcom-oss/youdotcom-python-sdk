"""Test utilities for the You.com Python SDK test suite."""

import httpx
import uuid


# A client passed to `You(...)` is caller-supplied, and the SDK deliberately
# never closes those — so the test owns its lifetime. Rather than repeat a
# try/finally at every call site, clients built here are registered and closed
# after the test by the autouse `_close_test_clients` fixture in conftest.py.
_OPEN_CLIENTS: list[httpx.Client] = []


def register_test_client(client: httpx.Client) -> httpx.Client:
    """Track a client so the autouse fixture in conftest.py will close it."""
    _OPEN_CLIENTS.append(client)
    return client


def close_test_clients() -> None:
    """Close and forget every registered client. Called from conftest.py.

    Closing an already-closed httpx client is a no-op, so this is safe for
    tests that also close explicitly.
    """
    while _OPEN_CLIENTS:
        client = _OPEN_CLIENTS.pop()
        try:
            client.close()
        except Exception:  # pragma: no cover - teardown must not fail a test
            pass


def create_test_http_client(test_name: str) -> httpx.Client:
    """Create a test HTTP client with tracking headers.

    The client is registered for teardown, so callers do not need to close it.
    """
    return register_test_client(
        httpx.Client(
            headers={
                "x-test-name": test_name,
                "x-test-instance-id": str(uuid.uuid4()),
            }
        )
    )
