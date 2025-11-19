import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    PostV1AgentsRunsForbiddenError,
    PostV1AgentsRunsUnauthorizedError,
)
from youdotcom.models import ComputeTool, ResearchTool, WebSearchTool
from youdotcom.types.typesafe_models import AgentType, SearchEffort, Verbosity


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
                agent=AgentType.EXPRESS,
                input="Teach me how to make an omelet",
                stream=False,
                server_url=server_url,
            )
            
            assert res.output is not None
            assert isinstance(res.output, list)
            assert len(res.output) > 0

    def test_streaming(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.EXPRESS,
                input="Teach me how to make an omelet",
                stream=True,
                server_url=server_url,
            )
            
            assert res.output is not None

    def test_with_web_search_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.EXPRESS,
                input="Summarize today's top AI research headlines.",
                stream=False,
                tools=[WebSearchTool()],
                server_url=server_url,
            )
            
            assert res.output is not None


class TestAdvancedAgent:
    def test_with_research_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.ADVANCED,
                input="Summarize today's top AI research headlines.",
                stream=False,
                tools=[ResearchTool()],
                server_url=server_url,
            )
            
            assert res.output is not None

    def test_with_compute_tool(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.ADVANCED,
                input="Calculate 15 * 23 and explain the steps.",
                stream=False,
                tools=[ComputeTool()],
                server_url=server_url,
            )
            
            assert res.output is not None

    def test_with_multiple_tools(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.ADVANCED,
                input="Research and calculate the square root of 169.",
                stream=True,
                tools=[
                    ComputeTool(),
                    ResearchTool(
                        search_effort=SearchEffort.AUTO,
                        report_verbosity=Verbosity.HIGH,
                    ),
                ],
                server_url=server_url,
            )
            
            assert res.output is not None

    def test_research_tool_configuration(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.ADVANCED,
                input="Research quantum computing breakthroughs.",
                stream=False,
                tools=[
                    ResearchTool(
                        search_effort=SearchEffort.HIGH,
                        report_verbosity=Verbosity.MEDIUM,
                    ),
                ],
                server_url=server_url,
            )
            
            assert res.output is not None


class TestCustomAgent:
    def test_with_uuid(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent="c12fa027-424e-4002-9659-746c16e74faa",
                input="Teach me how to make an omelet",
                stream=False,
                server_url=server_url,
            )
            
            assert res.output is not None

    def test_with_tools(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent="c12fa027-424e-4002-9659-746c16e74faa",
                input="Search for Python best practices.",
                stream=False,
                tools=[WebSearchTool()],
                server_url=server_url,
            )
            
            assert res.output is not None


class TestRunsErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/agents/runs-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises(PostV1AgentsRunsUnauthorizedError):
                you.agents.runs.create(
                    agent=AgentType.EXPRESS,
                    input="test",
                    stream=False,
                    server_url=server_url,
                )

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises(PostV1AgentsRunsForbiddenError):
                you.agents.runs.create(
                    agent=AgentType.EXPRESS,
                    input="test",
                    stream=False,
                    server_url=server_url,
                )

    def test_empty_input(self, server_url, api_key):
        client = create_test_http_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.agents.runs.create(
                agent=AgentType.EXPRESS,
                input="",
                stream=False,
                server_url=server_url,
            )
            
            assert res is not None
