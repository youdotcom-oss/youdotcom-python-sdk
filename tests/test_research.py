"""
Tests for research functionality via the Agents API.

The standalone Research API endpoint (POST /v1/research) was removed in 2.3.1.
Research is now performed via the Agents API using AdvancedAgentRunsRequest with ResearchTool.
"""

import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.models import (
    AdvancedAgentRunsRequest,
    AgentRunsBatchResponse,
    ReportVerbosity,
    ResearchTool,
    SearchEffort,
)


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestResearchViaAgents:
    def test_research_via_advanced_agent(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="What are the latest advances in quantum computing?",
                    stream=False,
                    tools=[ResearchTool(
                        search_effort=SearchEffort.LOW,
                        report_verbosity=ReportVerbosity.MEDIUM,
                    )],
                ),
                server_url=server_url,
            )

            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None
            assert len(res.output) > 0

    def test_research_with_high_effort(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")

        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="Explain the tradeoffs between transformer and SSM architectures",
                    stream=False,
                    tools=[ResearchTool(
                        search_effort=SearchEffort.HIGH,
                        report_verbosity=ReportVerbosity.HIGH,
                    )],
                ),
                server_url=server_url,
            )

            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None
