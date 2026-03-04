"""Test utilities for the You.com Python SDK test suite."""

import httpx
import uuid


def create_test_http_client(test_name: str) -> httpx.Client:
    return httpx.Client(
        headers={
            "x-speakeasy-test-name": test_name,
            "x-speakeasy-test-instance-id": str(uuid.uuid4()),
        }
    )
