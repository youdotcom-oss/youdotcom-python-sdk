"""Test utilities for the You.com Python SDK test suite."""

import httpx
import uuid


def create_test_http_client(test_name: str) -> httpx.Client:
    """Create a test HTTP client with tracking headers.

    The returned client is treated as SDK-supplied (not closed by You.__exit__).
    Call ``client.close()`` after use, or use within a ``with You(...) as you:`` block
    and close the client afterward.
    """
    return httpx.Client(
        headers={
            "x-test-name": test_name,
            "x-test-instance-id": str(uuid.uuid4()),
        }
    )
