"""
Comprehensive performance test suite for You.com Python SDK.

This module tests all supported endpoint combinations to measure SDK latency vs API latency:
- Search: with various filters, livecrawl options, pagination
- Agents: different agent types, tool combinations, streaming vs non-streaming
- Contents: different formats, single vs multiple URLs

Environment variables:
- PERF_TEST_TARGET: mock|custom (default: mock)
- PERF_TEST_SERVER_URL: server URL when using custom target (required for custom)
- PERF_TEST_ITERATIONS: number of iterations per test (default: 5 for mock, 1 for custom)
- PERF_TEST_API_KEY: API key for custom server tests
- PERF_OUTPUT_FORMAT: console|csv|json (default: console)
- PERF_DETAILED: show detailed metrics for each test (default: false)
"""

import os
import time
import uuid
from typing import List

import pytest

from tests.metrics import (
    PerformanceMetrics,
    calculate_metrics,
    export_metrics_csv,
    print_detailed_metrics,
    print_metrics_table,
)
from tests.timing_client import SDKCallTiming, TimingHTTPClient
from youdotcom import You
from youdotcom.models import (
    ComputeTool,
    ResearchTool,
    WebSearchTool,
    Country,
    ContentsFormats,
    Freshness,
    Language,
    LiveCrawl,
    LiveCrawlFormats,
    SafeSearch,
    SearchEffort,
    ReportVerbosity,
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
)


# ============================================================================
# Test Configuration
# ============================================================================

@pytest.fixture
def test_target():
    """Get test target from environment."""
    return os.getenv("PERF_TEST_TARGET", "mock")


@pytest.fixture
def iterations(test_target):
    """Get number of iterations from environment."""
    # Default to 1 iteration for custom targets to avoid overwhelming external servers
    # Default to 5 for mock server
    default_iterations = "1" if test_target == "custom" else "5"
    return int(os.getenv("PERF_TEST_ITERATIONS", default_iterations))


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("PERF_TEST_API_KEY", "test-api-key")


@pytest.fixture
def server_url(test_target):
    """Get server URL based on test target."""
    if test_target == "custom":
        url = os.getenv("PERF_TEST_SERVER_URL")
        if not url:
            raise ValueError("PERF_TEST_SERVER_URL must be set when using PERF_TEST_TARGET=custom")
        return url
    elif test_target == "mock":
        return os.getenv("TEST_SERVER_URL", "http://localhost:18080")
    else:
        raise ValueError(f"Unknown test target: {test_target}. Use 'mock' or 'custom'.")


@pytest.fixture
def show_detailed():
    """Whether to show detailed metrics."""
    return os.getenv("PERF_DETAILED", "false").lower() == "true"


# Store all metrics for final summary
ALL_METRICS: List[PerformanceMetrics] = []


def create_timing_client(test_name: str) -> TimingHTTPClient:
    """Create a TimingHTTPClient with test headers."""
    return TimingHTTPClient(
        follow_redirects=True,
        headers={
            "x-speakeasy-test-name": test_name,
            "x-speakeasy-test-instance-id": str(uuid.uuid4()),
        }
    )


def measure_sdk_call(func, timing_client: TimingHTTPClient, iterations: int, endpoint_name: str) -> PerformanceMetrics:
    """
    Measure SDK call performance over multiple iterations.
    
    Args:
        func: Function to call (should make one SDK call)
        timing_client: Timing HTTP client to track requests
        iterations: Number of times to run the test
        endpoint_name: Descriptive name for this endpoint/test
    
    Returns:
        PerformanceMetrics with statistical analysis
    """
    timings: List[SDKCallTiming] = []
    
    for i in range(iterations):
        # Clear previous timing
        timing_client.clear_timings()
        
        # Measure SDK call
        sdk_start = time.perf_counter()
        try:
            func()
            sdk_end = time.perf_counter()
            
            # Get HTTP timing
            request_timing = timing_client.get_last_timing()
            if request_timing is None:
                raise RuntimeError(f"No HTTP timing captured for {endpoint_name} iteration {i}")
            
            # Create combined timing
            sdk_timing = SDKCallTiming(
                endpoint=endpoint_name,
                sdk_start=sdk_start,
                sdk_end=sdk_end,
                request_timing=request_timing,
            )
            timings.append(sdk_timing)
            
        except Exception as e:
            print(f"Error in {endpoint_name} iteration {i}: {e}")
            # Skip this iteration
            continue
    
    if not timings:
        raise RuntimeError(f"No successful timings for {endpoint_name}")
    
    return calculate_metrics(endpoint_name, timings)


# ============================================================================
# Search Endpoint Tests
# ============================================================================

class TestSearchPerformance:
    """Performance tests for the Search API."""
    
    def test_search_basic(self, server_url, api_key, iterations, show_detailed):
        """Basic search with query only."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="latest AI developments", server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: basic query")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_count(self, server_url, api_key, iterations, show_detailed):
        """Search with result count limit."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="python programming", count=10, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: with count=10")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_freshness_day(self, server_url, api_key, iterations, show_detailed):
        """Search with freshness filter (day)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="breaking news", freshness=Freshness.DAY, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: freshness=DAY")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_freshness_week(self, server_url, api_key, iterations, show_detailed):
        """Search with freshness filter (week)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="renewable energy", freshness=Freshness.WEEK, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: freshness=WEEK")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_country_us(self, server_url, api_key, iterations, show_detailed):
        """Search with country filter (US)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="local restaurants", country=Country.US, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: country=US")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_country_gb(self, server_url, api_key, iterations, show_detailed):
        """Search with country filter (GB)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="football news", country=Country.GB, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: country=GB")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_language_en(self, server_url, api_key, iterations, show_detailed):
        """Search with language filter (English)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="machine learning", language=Language.EN, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: language=EN")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_language_es(self, server_url, api_key, iterations, show_detailed):
        """Search with language filter (Spanish)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="tecnología", language=Language.ES, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: language=ES")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_safesearch_off(self, server_url, api_key, iterations, show_detailed):
        """Search with safesearch off."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="research", safesearch=SafeSearch.OFF, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: safesearch=OFF")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_safesearch_moderate(self, server_url, api_key, iterations, show_detailed):
        """Search with safesearch moderate."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="family content", safesearch=SafeSearch.MODERATE, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: safesearch=MODERATE")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_safesearch_strict(self, server_url, api_key, iterations, show_detailed):
        """Search with safesearch strict."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="kids learning", safesearch=SafeSearch.STRICT, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: safesearch=STRICT")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_pagination(self, server_url, api_key, iterations, show_detailed):
        """Search with pagination (offset)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(query="python tutorials", count=5, offset=2, server_url=server_url)
            
            metrics = measure_sdk_call(call, client, iterations, "Search: with pagination (offset=2)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_web(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl enabled for web results."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="machine learning tutorials",
                    count=3,
                    livecrawl=LiveCrawl.WEB,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl=WEB")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_news(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl enabled for news results."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="tech news",
                    count=3,
                    livecrawl=LiveCrawl.NEWS,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl=NEWS")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_all(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl enabled for all results."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="quantum computing",
                    count=3,
                    livecrawl=LiveCrawl.ALL,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl=ALL")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_html(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl returning HTML format."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="AI research",
                    count=3,
                    livecrawl=LiveCrawl.WEB,
                    livecrawl_formats=LiveCrawlFormats.HTML,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl HTML format")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_markdown(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl returning Markdown format."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="documentation guides",
                    count=3,
                    livecrawl=LiveCrawl.WEB,
                    livecrawl_formats=LiveCrawlFormats.MARKDOWN,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl Markdown format")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_all_filters(self, server_url, api_key, iterations, show_detailed):
        """Search with multiple filters combined."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="quantum computing research",
                    count=10,
                    freshness=Freshness.MONTH,
                    country=Country.US,
                    language=Language.EN,
                    safesearch=SafeSearch.MODERATE,
                    offset=0,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: all filters combined")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_filters_and_livecrawl(self, server_url, api_key, iterations, show_detailed):
        """Search with filters and livecrawl combined."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="AI developments",
                    count=5,
                    freshness=Freshness.WEEK,
                    country=Country.GB,
                    livecrawl=LiveCrawl.WEB,
                    livecrawl_formats=LiveCrawlFormats.MARKDOWN,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: filters + livecrawl")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_news_livecrawl(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl for news results (news now supports contents)."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="technology news",
                    count=5,
                    livecrawl=LiveCrawl.NEWS,
                    livecrawl_formats=LiveCrawlFormats.MARKDOWN,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl=NEWS (with contents)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_search_with_livecrawl_all_news_contents(self, server_url, api_key, iterations, show_detailed):
        """Search with livecrawl=ALL for both web and news contents."""
        client = create_timing_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.search.unified(
                    query="breaking tech news",
                    count=3,
                    livecrawl=LiveCrawl.ALL,
                    livecrawl_formats=LiveCrawlFormats.HTML,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Search: livecrawl=ALL (web+news contents)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)


# ============================================================================
# Agents Endpoint Tests
# ============================================================================

class TestAgentsPerformance:
    """Performance tests for the Agents API."""
    
    def test_agents_express_no_tools(self, server_url, api_key, iterations, show_detailed):
        """Express agent without tools (non-streaming)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="Teach me how to make an omelet",
                        stream=False,
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: EXPRESS, no tools")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_express_with_websearch(self, server_url, api_key, iterations, show_detailed):
        """Express agent with WebSearchTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="What are the latest AI developments?",
                        stream=False,
                        tools=[WebSearchTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: EXPRESS + WebSearchTool")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_express_with_websearch_force(self, server_url, api_key, iterations, show_detailed):
        """Express agent with WebSearchTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="Tell me about Python",
                        stream=False,
                        tools=[WebSearchTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: EXPRESS + WebSearchTool")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_no_tools(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent without tools."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Explain quantum entanglement",
                        stream=False,
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED, no tools")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Research the latest breakthroughs in quantum computing",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.AUTO,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ResearchTool")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research_low_effort(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool (low search effort)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Quick research on AI",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.LOW,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ResearchTool (low effort)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research_high_effort(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool (high search effort)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Deep research on climate change",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.HIGH,
                            report_verbosity=ReportVerbosity.HIGH,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ResearchTool (high effort)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research_verbosity_low(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool (low verbosity)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Brief summary of AI trends",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.LOW,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ResearchTool (low verbosity)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research_verbosity_high(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool (high verbosity)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Detailed analysis of blockchain",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.HIGH,
                            report_verbosity=ReportVerbosity.HIGH,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ResearchTool (high verbosity)")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_compute(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ComputeTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Calculate the square root of 169",
                        stream=False,
                        tools=[ComputeTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + ComputeTool")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_websearch_and_research(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Find and research AI startups",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.AUTO,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        )],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + Research")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_websearch_and_compute(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ComputeTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Find stock prices and calculate averages",
                        stream=False,
                        tools=[ComputeTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + Compute")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_research_and_compute(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with ResearchTool + ComputeTool."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Research market trends and calculate growth rates",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.AUTO,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        ), ComputeTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + Research + Compute")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_advanced_with_all_tools(self, server_url, api_key, iterations, show_detailed):
        """Advanced agent with all tools."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=AdvancedAgentRunsRequest(
                        input="Research tech trends, find data, and calculate statistics",
                        stream=False,
                        tools=[ResearchTool(
                            search_effort=SearchEffort.AUTO,
                            report_verbosity=ReportVerbosity.MEDIUM,
                        ), ComputeTool()],
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: ADVANCED + all tools")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_express_verbosity_low(self, server_url, api_key, iterations, show_detailed):
        """Express agent (verbosity not supported for express)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="Brief overview of Python",
                        stream=False,
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: EXPRESS")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_agents_express_verbosity_high(self, server_url, api_key, iterations, show_detailed):
        """Express agent (verbosity not supported for express)."""
        client = create_timing_client("post_/v1/agents/runs")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.agents.runs.create(
                    request=ExpressAgentRunsRequest(
                        input="Detailed explanation of Python",
                        stream=False,
                    ),
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Agents: EXPRESS")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)


# ============================================================================
# Contents Endpoint Tests
# ============================================================================

class TestContentsPerformance:
    """Performance tests for the Contents API."""
    
    def test_contents_single_url_html(self, server_url, api_key, iterations, show_detailed):
        """Fetch single URL in HTML format."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=["https://www.python.org"],
                    formats=[ContentsFormats.HTML],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: single URL, HTML")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_single_url_markdown(self, server_url, api_key, iterations, show_detailed):
        """Fetch single URL in Markdown format."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=["https://www.python.org"],
                    formats=[ContentsFormats.MARKDOWN],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: single URL, Markdown")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_single_url_metadata(self, server_url, api_key, iterations, show_detailed):
        """Fetch single URL with metadata format (json+ld, OpenGraph)."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=["https://www.python.org"],
                    formats=[ContentsFormats.METADATA],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: single URL, Metadata")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_multiple_formats(self, server_url, api_key, iterations, show_detailed):
        """Fetch single URL with multiple formats (HTML, Markdown, Metadata)."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=["https://www.python.org"],
                    formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN, ContentsFormats.METADATA],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: single URL, all formats")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_with_crawl_timeout(self, server_url, api_key, iterations, show_detailed):
        """Fetch URL with custom crawl timeout."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=["https://www.python.org"],
                    formats=[ContentsFormats.HTML],
                    crawl_timeout=30,
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: single URL, with crawl_timeout")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_multiple_urls_html(self, server_url, api_key, iterations, show_detailed):
        """Fetch multiple URLs in HTML format."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=[
                        "https://www.python.org",
                        "https://www.github.com",
                        "https://www.example.com",
                    ],
                    formats=[ContentsFormats.HTML],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: 3 URLs, HTML")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_multiple_urls_markdown(self, server_url, api_key, iterations, show_detailed):
        """Fetch multiple URLs in Markdown format."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=[
                        "https://www.python.org",
                        "https://www.github.com",
                        "https://www.example.com",
                    ],
                    formats=[ContentsFormats.MARKDOWN],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: 3 URLs, Markdown")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)
    
    def test_contents_many_urls_html(self, server_url, api_key, iterations, show_detailed):
        """Fetch many URLs in HTML format."""
        client = create_timing_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            def call():
                you.contents.generate(
                    urls=[
                        "https://www.python.org",
                        "https://www.github.com",
                        "https://www.example.com",
                        "https://www.you.com",
                        "https://www.wikipedia.org",
                    ],
                    formats=[ContentsFormats.HTML],
                    server_url=server_url,
                )
            
            metrics = measure_sdk_call(call, client, iterations, "Contents: 5 URLs, HTML")
            ALL_METRICS.append(metrics)
            if show_detailed:
                print_detailed_metrics(metrics)


# ============================================================================
# Test Summary
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def print_final_summary(request):
    """Print final summary after all tests complete."""
    def finalize():
        if ALL_METRICS:
            test_target = os.getenv("PERF_TEST_TARGET", "mock")
            print_metrics_table(
                ALL_METRICS,
                title=f"Performance Test Results - Target: {test_target}"
            )
            
            # Export to CSV if requested
            output_format = os.getenv("PERF_OUTPUT_FORMAT", "console")
            if output_format == "csv":
                export_metrics_csv(ALL_METRICS, "performance_results.csv")
    
    request.addfinalizer(finalize)
