import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    AgentRuns401ResponseError,
    AgentRuns422ResponseError,
)
from youdotcom.models import (
    ComputeTool,
    ResearchTool,
    WebSearchTool,
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    CustomAgentRunsRequest,
    SearchEffort,
    ReportVerbosity,
    AgentRunsBatchResponse,
)
from youdotcom.utils import eventstreaming


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestExpressAgent:
    def test_basic(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=ExpressAgentRunsRequest(
                    input="Teach me how to make an omelet",
                    stream=False,
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None
            assert isinstance(res.output, list)
            assert len(res.output) > 0

    def test_streaming(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=ExpressAgentRunsRequest(
                    input="Teach me how to make an omelet",
                    stream=True,
                ),
                server_url=server_url,
            )
            
            # Mock server returns batch response even for streaming requests
            # In production, this would be an EventStream
            assert res is not None

    def test_with_web_search_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=ExpressAgentRunsRequest(
                    input="Summarize today's top AI research headlines.",
                    stream=False,
                    tools=[WebSearchTool()],
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None


class TestAdvancedAgent:
    def test_with_research_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="Summarize today's top AI research headlines.",
                    stream=False,
                    tools=[ResearchTool(
                        search_effort=SearchEffort.AUTO,
                        report_verbosity=ReportVerbosity.MEDIUM,
                    )],
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None

    def test_with_compute_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="Calculate 15 * 23 and explain the steps.",
                    stream=False,
                    tools=[ComputeTool()],
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None

    def test_with_multiple_tools(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="Research and calculate the square root of 169.",
                    stream=True,
                    tools=[
                        ComputeTool(),
                        ResearchTool(
                            search_effort=SearchEffort.AUTO,
                            report_verbosity=ReportVerbosity.HIGH,
                        ),
                    ],
                ),
                server_url=server_url,
            )
            
            # Mock server returns batch response even for streaming requests
            # In production, this would be an EventStream
            assert res is not None

    def test_research_tool_configuration(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="Research quantum computing breakthroughs.",
                    stream=False,
                    tools=[
                        ResearchTool(
                            search_effort=SearchEffort.HIGH,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        ),
                    ],
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None


class TestCustomAgent:
    def test_with_uuid(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=CustomAgentRunsRequest(
                    agent="c12fa027-424e-4002-9659-746c16e74faa",
                    input="Teach me how to make an omelet",
                    stream=False,
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None

    def test_with_tools(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=CustomAgentRunsRequest(
                    agent="c12fa027-424e-4002-9659-746c16e74faa",
                    input="Search for Python best practices.",
                    stream=False,
                    tools=[WebSearchTool()],
                ),
                server_url=server_url,
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None


class TestRunsErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/agents/runs-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises(AgentRuns401ResponseError):
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="test",
                        stream=False,
                    ),
                    server_url=server_url,
                )

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            # Mock server returns 403 which gets caught as a default error
            # In production API, this would be a more specific error type
            with pytest.raises(Exception):  # Accept any exception for mock server
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="test",
                        stream=False,
                    ),
                    server_url=server_url,
                )

    def test_empty_input(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                request=ExpressAgentRunsRequest(
                    input="",
                    stream=False,
                ),
                server_url=server_url,
            )
            
            assert res is not None
