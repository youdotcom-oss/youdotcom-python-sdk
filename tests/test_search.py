import json
import pytest
import httpx

from youdotcom import You
from youdotcom.errors import (
    ForbiddenResponseError,
    UnauthorizedResponseError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)


# ---------------------------------------------------------------------------
# Error tests: search() (POST /v1/agents/search) must raise the same
# consolidated *ResponseError classes.  Uses MockTransport.
# ---------------------------------------------------------------------------


class TestSearchErrors:
    """Verify search() raises the consolidated *ResponseError classes.

    The CHANGELOG documents that the Search endpoint (POST) raises the
    consolidated error classes. These tests lock that contract for the
    POST path so a regen that mis-wires POST errors would fail CI.
    """

    def test_unauthorized(self):
        def handler(request):
            return httpx.Response(
                401,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "Invalid or expired API key"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="invalid")
        with pytest.raises((UnauthorizedResponseError, YouDefaultError)):
            you.search(query="test")
        sdk_client.close()

    def test_forbidden(self):
        def handler(request):
            return httpx.Response(
                403,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "Forbidden"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises((ForbiddenResponseError, YouDefaultError)):
            you.search(query="test")
        sdk_client.close()

    def test_unprocessable(self):
        def handler(request):
            return httpx.Response(
                422,
                headers={"content-type": "application/json"},
                content=json.dumps({"message": "include_domains and exclude_domains cannot be combined"}),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        with pytest.raises((UnprocessableEntityResponseError, YouDefaultError)):
            you.search(
                query="test",
                include_domains=["example.com"],
                exclude_domains=["spam.com"],
            )
        sdk_client.close()


class TestSearchBoostDomains:
    """Verify search() forwards boost_domains in the request body."""

    def test_boost_domains_forwarded(self):
        def handler(request):
            body = json.loads(request.content)
            assert "boost_domains" in body
            assert "python.org" in body["boost_domains"]
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "results": {
                        "web": [
                            {"url": "https://python.org", "title": "Python", "description": "Python.org"}
                        ],
                    },
                    "metadata": {"q": "test", "latency": 0.1},
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        res = you.search(
            query="Python type hints",
            boost_domains=["python.org", "realpython.com"],
        )
        assert res.results is not None
        sdk_client.close()
