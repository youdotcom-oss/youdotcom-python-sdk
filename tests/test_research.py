import os
import uuid
import pytest

import httpx

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    ResearchForbiddenError,
    ResearchInternalServerError,
    ResearchUnauthorizedError,
    UnprocessableEntityError,
    YouDefaultError,
)
from youdotcom.models import (
    ResearchEffort,
    ResearchResponse,
)


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestResearchBasic:
    def test_basic_research(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What are the latest advances in quantum computing?",
                research_effort=ResearchEffort.STANDARD,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    def test_research_lite_effort(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.LITE,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None

    def test_research_deep_effort(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="Explain the tradeoffs between transformer and SSM architectures",
                research_effort=ResearchEffort.DEEP,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    def test_research_exhaustive_effort(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="Compare global approaches to AI regulation across the US, EU, and China",
                research_effort=ResearchEffort.EXHAUSTIVE,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    def test_research_with_sources(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What are the benefits of renewable energy?",
                research_effort=ResearchEffort.STANDARD,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.sources is not None
            assert len(res.output.sources) > 0
            for source in res.output.sources:
                assert source.url is not None


class TestResearchAsync:
    @pytest.mark.asyncio
    async def test_basic_research_async(self, server_url, api_key):
        async_client = httpx.AsyncClient(
            headers={
                "x-speakeasy-test-name": "post_/v1/research",
                "x-speakeasy-test-instance-id": str(uuid.uuid4()),
            },
            follow_redirects=True,
        )

        async with You(server_url=server_url, async_client=async_client, api_key_auth=api_key) as you:
            res = await you.research_async(
                input="What are the latest advances in quantum computing?",
                research_effort=ResearchEffort.STANDARD,
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0


class TestResearchErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/research-unauthorized")

        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises((ResearchUnauthorizedError, YouDefaultError)):
                you.research(
                    input="test",
                    server_url=server_url,
                )

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research-forbidden")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises((ResearchForbiddenError, YouDefaultError)):
                you.research(
                    input="test",
                    server_url=server_url,
                )

    def test_unprocessable_entity(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research-unprocessable")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises((UnprocessableEntityError, YouDefaultError)):
                you.research(
                    input="",
                    server_url=server_url,
                )

    def test_internal_server_error(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research-internal-error")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises((ResearchInternalServerError, YouDefaultError)):
                you.research(
                    input="test",
                    server_url=server_url,
                )
