import os
import uuid
import pytest

import httpx

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    FinanceResearchUnauthorizedError,
    ResearchForbiddenError,
    ResearchInternalServerError,
    ResearchUnauthorizedError,
    ResearchUnprocessableEntityError,
    UnprocessableEntityResponseError,
    YouDefaultError,
)
from youdotcom.models import (
    FinanceResearchEffort,
    ResearchEffort,
    ResearchResponse,
    TaskResponse,
)


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return "test-api-key"


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
            with pytest.raises((ResearchUnprocessableEntityError, UnprocessableEntityResponseError, YouDefaultError)):
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


class TestFinanceResearch:
    def test_basic_finance_research(self, server_url, api_key):
        client = create_test_http_client("post_/v1/finance_research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.finance_research(
                input="What was NVIDIA's FY2025 revenue?",
                research_effort=FinanceResearchEffort.DEEP,
                server_url=server_url,
            )

            assert res.output is not None
            assert res.output.content is not None
            assert "NVIDIA" in res.output.content
            # Finance sources intentionally never include the `snippets` field.
            assert res.output.sources is not None
            assert len(res.output.sources) > 0
            for source in res.output.sources:
                assert source.url is not None
                assert source.title is not None

    def test_finance_research_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/finance_research-unauthorized")

        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises((FinanceResearchUnauthorizedError, YouDefaultError)):
                you.finance_research(
                    input="test",
                    server_url=server_url,
                )


class TestResearchBackground:
    """Direct coverage for the auto-generated background/stream SDK methods."""

    def test_research_background_returns_task_response(self, server_url, api_key):
        client = create_test_http_client("post_/v1/research-background")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.STANDARD,
                background=True,
                server_url=server_url,
            )

            assert isinstance(res, TaskResponse)
            assert res.task_id == "00000000-0000-0000-0000-000000000001"
            assert res.status.value == "queued"
            assert res.stream_url is not None
            assert res.created_at is not None

    def test_get_research_task_returns_task_detail(self, server_url, api_key):
        client = create_test_http_client("get_/v1/research/{task_id}")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            detail = you.get_research_task(
                task_id="00000000-0000-0000-0000-000000000001",
                server_url=server_url,
            )

            assert detail.id == "00000000-0000-0000-0000-000000000001"
            assert detail.task_type == "research"
            assert detail.status.value == "completed"
            assert detail.created_at is not None
            assert detail.completed_at is not None
            # result is populated server-side; the typed Result model itself
            # has no fields (extra=ignore), so we only assert presence here.
            assert detail.result is not None


# ---------------------------------------------------------------------------
# 2.4.0 beta params: output_schema (structured output_content) and
# source_control (domain constraints / freshness / country).
# ---------------------------------------------------------------------------

import json


class TestResearchOutputSchema:
    """``output_schema=`` request flips ``output.content_type`` to ``object``
    and the server-side `output.content` becomes a structured JSON object
    matching the schema.

    The default Go mockserver returns ``content_type=text`` regardless of
    the request body, so this test uses ``httpx.MockTransport`` to inject a
    realistic server response with ``content_type=object`` and asserts the
    SDK correctly deserializes both the ``content_type`` slot and the
    structured payload (preserved via ``extra="allow"`` on the ``Content``
    model).
    """

    def test_output_schema_sets_content_type_to_object(self, server_url, api_key):
        structured_payload = {
            "same_entity": True,
            "confidence": 0.95,
            "evidence": ["https://acme-logistics.com/about"],
        }

        def handler(request):
            body = json.loads(request.content)
            assert "output_schema" in body
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({
                    "output": {
                        "content": structured_payload,
                        "content_type": "object",
                        "sources": [],
                    },
                }),
            )

        transport = httpx.MockTransport(handler)
        sdk_client = httpx.Client(transport=transport)
        you = You(
            server_url=server_url,
            client=sdk_client,
            api_key_auth=api_key,
        )

        res = you.research(
            input="Are 'Acme Logistics LLC' (Delaware) and 'Acme Logistics' (Newark, NJ) the same business?",
            research_effort=ResearchEffort.STANDARD,
            output_schema={
                "type": "object",
                "properties": {
                    "same_entity": {"type": "boolean"},
                    "confidence": {"type": "number"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["same_entity", "confidence", "evidence"],
                "additionalProperties": False,
            },
        )

        assert isinstance(res, ResearchResponse)
        assert res.output.content_type.value == "object"
        # With extra="allow" on the Content model, the structured payload
        # is preserved. res.output.content is a Content instance whose
        # model_dump() returns the full structured dict.
        assert res.output.content is not None
        assert res.output.content.model_dump() == structured_payload
        assert res.output.content.same_entity is True


class TestResearchSourceControl:
    """``source_control=`` accepts the documented shape (include_domains,
    exclude_domains, boost_domains, freshness, country) and is forwarded
    to the server. The Go mockserver doesn't validate the request body,
    so this is an end-to-end smoke test that all five fields serialize
    and round-trip without complaint.
    """

    def test_source_control_with_include_domains(self, server_url, api_key):
        """include_domains alone is valid per the SDK docstring."""
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What did the Federal Reserve do in 2024?",
                research_effort=ResearchEffort.STANDARD,
                source_control={
                    "include_domains": ["federalreserve.gov"],
                },
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None

    def test_source_control_with_boost_and_exclude(self, server_url, api_key):
        """boost_domains + exclude_domains is the only valid two-way pair."""
        client = create_test_http_client("post_/v1/research")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.research(
                input="What happened in the AI industry this year?",
                research_effort=ResearchEffort.STANDARD,
                source_control={
                    "boost_domains": ["nytimes.com", "wired.com"],
                    "exclude_domains": ["reddit.com"],
                    "country": "US",
                    "freshness": "month",
                },
                server_url=server_url,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None



