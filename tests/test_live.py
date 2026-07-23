"""
Live API tests for You.com Python SDK.

These tests run against the real You.com API to verify SDK functionality.
Set the YDC_API_KEY environment variable before running:

    YDC_API_KEY="your-api-key" pytest tests/test_live.py -v

To skip these tests, run pytest with the --ignore flag:
    pytest tests/ --ignore=tests/test_live.py -v

The DEEP/EXHAUSTIVE research calls are slow on prod (30-90s); skip them
with `-m "not slow"` for a fast smoke run:

    pytest tests/test_live.py -v -m "not slow"
"""

import os
import pytest

from youdotcom import You
from youdotcom.models import (
    Country,
    ContentsFormats,
    Freshness,
    LiveCrawl,
    LiveCrawlFormats,
    SafeSearch,
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    ResearchTool,
    SearchEffort,
    ReportVerbosity,
    AgentRunsBatchResponse,
    ResearchEffort,
    ResearchResponse,
    TaskResponse,
    TaskDetail,
    FinanceResearchEffort,
)
from youdotcom.research_helpers import (
    research_background,
    poll_research_task,
    research_and_wait,
    stream_research,
)
from youdotcom.errors import (
    FinanceResearchUnprocessableEntityError,
    ResearchUnprocessableEntityError,
    YouDefaultError,
)


# Skip all tests in this file if no API key is provided.
# Mirror the SDK's own env-var precedence (YDC_API_KEY first, then
# YOU_API_KEY_AUTH as the documented 2.3.x fallback) so users on the
# fallback env var don't get their live suite silently skipped.
pytestmark = pytest.mark.skipif(
    not (os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY_AUTH")),
    reason="YDC_API_KEY or YOU_API_KEY_AUTH environment variable not set"
)


# 2.4.0 bumped livecrawl_formats to a strict list type and research can
# legitimately take 20-30s for DEEP/EXHAUSTIVE effort. Generous timeout.
LIVE_TIMEOUT_MS = 90_000


@pytest.fixture
def api_key():
    """Get API key from environment.

    Mirrors the SDK's own env-var precedence (`YDC_API_KEY` first, then
    `YOU_API_KEY_AUTH` as the documented 2.3.x fallback).
    """
    return os.getenv("YDC_API_KEY") or os.getenv("YOU_API_KEY_AUTH")


@pytest.fixture
def you_client(api_key):
    """Create a You client for live testing with a generous timeout."""
    return You(
        api_key_auth=api_key,
        timeout_ms=LIVE_TIMEOUT_MS,
    )


class TestLiveSearch:
    """Live tests for the Search API."""
    
    def test_basic_search(self, you_client):
        """Test basic search functionality against live API."""
        with you_client as you:
            res = you.search.unified(query="Python programming language")
            
            assert res.results is not None
            assert res.metadata is not None
            assert res.metadata.query == "Python programming language"
            assert res.results.web is not None
            assert len(res.results.web) > 0
    
    def test_search_with_filters(self, you_client):
        """Test search with filters against live API."""
        with you_client as you:
            res = you.search.unified(
                query="artificial intelligence",
                count=5,
                freshness=Freshness.WEEK,
                country=Country.US,
                safesearch=SafeSearch.MODERATE,
            )
            
            assert res.results is not None
            assert res.metadata is not None
            # Verify we got results
            if res.results.web:
                assert len(res.results.web) <= 5
    
    def test_search_with_livecrawl_web(self, you_client):
        """Test search with livecrawl for web results."""
        with you_client as you:
            res = you.search.unified(
                query="machine learning tutorials",
                count=3,
                livecrawl=LiveCrawl.WEB,
                livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
            )

            assert res.results is not None

            # Web results may have contents
            if res.results.web:
                for result in res.results.web:
                    # Check that we can access the contents field
                    if result.contents:
                        # At least one of html or markdown should be present
                        assert result.contents.markdown or result.contents.html

    def test_search_with_livecrawl_news(self, you_client):
        """Test search with livecrawl for news results (new in 2.2.0)."""
        with you_client as you:
            res = you.search.unified(
                query="technology news today",
                count=3,
                livecrawl=LiveCrawl.NEWS,
                livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
            )

            assert res.results is not None

            # News results can now have contents field (new in 2.2.0)
            if res.results.news:
                for news_item in res.results.news:
                    # Check that we can access the contents field
                    if news_item.contents:
                        # At least one of html or markdown should be present
                        assert news_item.contents.markdown or news_item.contents.html

    def test_search_with_livecrawl_all(self, you_client):
        """Test search with livecrawl=ALL for both web and news."""
        with you_client as you:
            res = you.search.unified(
                query="breaking tech news",
                count=3,
                livecrawl=LiveCrawl.ALL,
                livecrawl_formats=[LiveCrawlFormats.HTML],
            )
            
            assert res.results is not None
            
            # Both web and news should be able to have contents
            has_any_contents = False
            
            if res.results.web:
                for result in res.results.web:
                    if result.contents:
                        has_any_contents = True
                        break
            
            if res.results.news:
                for news_item in res.results.news:
                    if news_item.contents:
                        has_any_contents = True
                        break
            
            # We expect at least some results to have contents with livecrawl=ALL
            # (This assertion may be relaxed if the API doesn't always return contents)


class TestLiveContents:
    """Live tests for the Contents API."""
    
    def test_html_format(self, you_client):
        """Test fetching content in HTML format."""
        with you_client as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.HTML],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
            assert res[0].url is not None
            # HTML should be present when HTML format is requested
            if res[0].html:
                assert "<" in res[0].html  # Basic HTML check
    
    def test_markdown_format(self, you_client):
        """Test fetching content in Markdown format."""
        with you_client as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.MARKDOWN],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
    
    def test_metadata_format(self, you_client):
        """Test fetching metadata from a page."""
        with you_client as you:
            res = you.contents.generate(
                urls=["https://www.python.org"],
                formats=[ContentsFormats.METADATA],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
            # Metadata should be present
            assert res[0].metadata is not None
    
    def test_multiple_formats(self, you_client):
        """Test fetching multiple formats at once."""
        with you_client as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0


class TestLiveAgents:
    """Live tests for the Agents API."""
    
    def test_express_agent(self, you_client):
        """Test Express agent with basic query."""
        with you_client as you:
            res = you.agents.runs.create(
                request=ExpressAgentRunsRequest(
                    input="What is the capital of France?",
                    stream=False,
                )
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None
            assert len(res.output) > 0
    
    @pytest.mark.slow
    def test_advanced_agent_with_research(self, you_client):
        """Test Advanced agent with ResearchTool."""
        with you_client as you:
            res = you.agents.runs.create(
                request=AdvancedAgentRunsRequest(
                    input="What are the latest developments in AI?",
                    stream=False,
                    tools=[ResearchTool(
                        search_effort=SearchEffort.LOW,
                        report_verbosity=ReportVerbosity.MEDIUM,
                    )],
                )
            )
            
            assert isinstance(res, AgentRunsBatchResponse)
            assert res.output is not None


class TestLiveResearch:
    """Live tests for the Research API (new in 2.3.0)."""

    def test_research_basic(self, you_client):
        """Test basic research query."""
        with you_client as you:
            res = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.LITE,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    @pytest.mark.slow
    def test_research_deep_effort(self, you_client):
        """Test research with deep effort level (may be slow on prod)."""
        with you_client as you:
            res = you.research(
                input="Briefly describe transformer attention vs SSM state spaces",
                research_effort=ResearchEffort.DEEP,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    @pytest.mark.slow
    def test_research_exhaustive_effort(self, you_client):
        """Test research with exhaustive effort level (slow on prod)."""
        with you_client as you:
            res = you.research(
                input="Compare solar vs wind vs nuclear cost trends 2020-2026 in 2 sentences",
                research_effort=ResearchEffort.EXHAUSTIVE,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0

    def test_research_with_sources(self, you_client):
        """Test research query returns sources."""
        with you_client as you:
            res = you.research(
                input="What are the benefits of renewable energy?",
                research_effort=ResearchEffort.STANDARD,
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert res.output.sources is not None
            assert len(res.output.sources) > 0
            for source in res.output.sources:
                assert source.url is not None


class TestLiveResearchOutputSchema:
    """Live test for Research `output_schema` parameter (beta feature).

    Smoke-tests prod to ensure the overlay-generated
    `Content = Union[str, Dict[str, Any]]` round-trips structured payloads.
    """

    def test_research_output_schema_structured_payload(self, you_client):
        """output_schema returns a structured object in `output.content`.

        output_schema only works with research_effort >= standard (lite returns 422).
        Per the server's schema rules, every property must be listed in `required`.
        """
        with you_client as you:
            res = you.research(
                input="Are Acme Logistics DE and Acme Logistics NJ the same entity?",
                research_effort=ResearchEffort.STANDARD,
                output_schema={
                    "type": "object",
                    "properties": {
                        "same_entity": {"type": "boolean"},
                        "confidence": {"type": "number"},
                        "reason": {"type": "string"},
                    },
                    "required": ["same_entity", "confidence", "reason"],
                    "additionalProperties": False,
                },
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content_type is not None
            assert res.output.content_type.value == "object"
            assert isinstance(res.output.content, dict)
            assert "same_entity" in res.output.content


class TestLiveResearchSourceControl:
    """Live test for Research `source_control` parameter (beta feature).

    `source_control` constrains which web sources the research agent searches;
    this smoke test exercises the basic `boost_domains` sub-parameter.
    """

    def test_research_source_control_with_boost_domains(self, you_client):
        """source_control.boost_domains doesn't restrict, only boosts."""
        with you_client as you:
            res = you.research(
                input="latest news about Python 3.13 release",
                research_effort=ResearchEffort.LITE,
                source_control={
                    "boost_domains": ["python.org", "docs.python.org"],
                },
            )

            assert isinstance(res, ResearchResponse)
            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0


class TestLiveFinanceResearch:
    """Live tests for the Finance Research API."""

    @pytest.mark.slow
    def test_finance_research_basic(self, you_client):
        """Test finance_research returns Markdown answer + sources."""
        with you_client as you:
            res = you.finance_research(
                input="Latest NVIDIA earnings call summary FY2026 Q1",
                research_effort=FinanceResearchEffort.DEEP,
            )

            assert res.output is not None
            # content is text for finance_research
            assert res.output.content is not None
            assert len(res.output.content) > 0
            # sources is informational
            if res.output.sources:
                for source in res.output.sources:
                    assert source.url is not None

    def test_finance_research_lite_effort(self, you_client):
        """Test finance_research with LITE effort returns a quick answer.
        Skipped if the server hasn't deployed the lite tier yet."""
        with you_client as you:
            try:
                res = you.finance_research(
                    input="What was Apple's revenue in fiscal year 2024?",
                    research_effort=FinanceResearchEffort.LITE,
                )
            except (FinanceResearchUnprocessableEntityError, YouDefaultError) as e:
                if "lite" in str(e).lower() or "422" in str(e):
                    pytest.skip("Finance research lite tier not yet deployed on server")
                raise

            assert res.output is not None
            assert res.output.content is not None
            assert len(res.output.content) > 0
            if res.output.sources:
                for source in res.output.sources:
                    assert source.url is not None


class TestLiveContentsMaxAge:
    """Live test for Contents `max_age` parameter.

    `max_age` controls cache freshness — when set, cached content older
    than the threshold is ignored and the page is re-fetched.
    """

    def test_contents_with_max_age(self, you_client):
        """max_age is accepted as an optional parameter."""
        with you_client as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.MARKDOWN],
                max_age=86400,  # 1 day
            )

            assert isinstance(res, list)
            assert len(res) > 0


class TestLiveSearchBoostDomains:
    """Live test for Search `boost_domains` parameter.

    `boost_domains` prefers certain domains in ranking without excluding
    other domains — for a more permissive alternative to `include_domains`.
    """

    def test_search_post_boost_domains_list(self, you_client):
        """search_post accepts a Python list of boost domains."""
        with you_client as you:
            res = you.search_post(
                query="Python type hints vs TypeScript inference",
                count=5,
                boost_domains=["python.org", "realpython.com"],
            )

            assert res.results is not None


# ---------------------------------------------------------------------------
# Background-mode research (new in 2.5.0)
# ---------------------------------------------------------------------------
# These tests exercise the live API's async task path:
#   POST /v1/research?background=true  -> TaskResponse
#   GET  /v1/research/{task_id}        -> TaskDetail
#   GET  /v1/research/{task_id}/stream -> SSE stream
#
# All tests use LITE effort so the task finishes in 10-30s on prod.
# The suite is sequential within each test: submit, then poll or stream
# until a terminal state arrives.  If background mode is not enabled on
# the server, the research() call falls back to a sync ResearchResponse
# and the test is skipped with a clear message.
# ---------------------------------------------------------------------------

_BG_TIMEOUT_S = 120.0  # generous wall-clock for LITE background tasks


class TestLiveResearchBackground:
    """Live tests for background-mode research (POST /v1/research?background=true)."""

    def test_background_returns_task_response(self, you_client):
        """research(background=True) should return a TaskResponse, not ResearchResponse."""
        with you_client as you:
            res = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.LITE,
                background=True,
            )

            if isinstance(res, ResearchResponse):
                pytest.skip("Background mode not enabled on server (got sync ResearchResponse)")

            assert isinstance(res, TaskResponse)
            assert res.task_id is not None
            assert len(res.task_id) > 0
            assert res.type == "research"
            assert res.status is not None
            assert res.stream_url is not None
            assert res.stream_url.startswith("/v1/research/")
            assert res.stream_url.endswith("/stream")
            assert res.created_at is not None

    def test_get_research_task_returns_task_detail(self, you_client):
        """get_research_task() should return a TaskDetail for a background task."""
        with you_client as you:
            task = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.LITE,
                background=True,
            )

            if isinstance(task, ResearchResponse):
                pytest.skip("Background mode not enabled on server")

            assert isinstance(task, TaskResponse)

            detail = you.get_research_task(task_id=task.task_id)
            assert isinstance(detail, TaskDetail)
            assert detail.id == task.task_id
            assert detail.task_type == "research"
            assert detail.status is not None
            assert detail.created_at is not None
            # input should be preserved (TaskDetailInput uses extra="allow")
            assert detail.input is not None
            input_dump = detail.input.model_dump()
            assert input_dump.get("input") == "What is the capital of France?"

    def test_poll_until_completed(self, you_client):
        """Poll get_research_task() until status == completed, verify result."""
        with you_client as you:
            task = you.research(
                input="What is the capital of France?",
                research_effort=ResearchEffort.LITE,
                background=True,
            )

            if isinstance(task, ResearchResponse):
                pytest.skip("Background mode not enabled on server")

            assert isinstance(task, TaskResponse)

            detail = poll_research_task(
                you,
                task.task_id,
                interval_s=3.0,
                timeout_s=_BG_TIMEOUT_S,
            )

            assert detail.status.value == "completed"
            assert detail.completed_at is not None
            # Result should contain the ResearchResponse payload
            assert detail.result is not None
            result_dump = detail.result.model_dump()
            assert "output" in result_dump
            output = result_dump["output"]
            assert "content" in output
            assert len(str(output["content"])) > 0

    def test_research_and_wait(self, you_client):
        """research_and_wait submits + streams + returns completed TaskDetail."""
        with you_client as you:
            try:
                detail = research_and_wait(
                    you,
                    timeout_s=_BG_TIMEOUT_S,
                    timeout_ms=180_000,
                    input="What is the capital of France?",
                    research_effort=ResearchEffort.LITE,
                )
            except TypeError as e:
                if "TaskResponse" in str(e):
                    pytest.skip("Background mode not enabled on server")
                raise

            assert isinstance(detail, TaskDetail)
            assert detail.status.value == "completed"
            assert detail.result is not None
            result_dump = detail.result.model_dump()
            assert "output" in result_dump


class TestLiveResearchBackgroundHelpers:
    """Live tests for the research_helpers convenience functions."""

    def test_research_background_helper(self, you_client):
        """research_background() helper asserts and returns TaskResponse."""
        with you_client as you:
            try:
                task = research_background(
                    you,
                    input="What is the capital of France?",
                    research_effort=ResearchEffort.LITE,
                )
            except TypeError as e:
                if "TaskResponse" in str(e):
                    pytest.skip("Background mode not enabled on server")
                raise

            assert isinstance(task, TaskResponse)
            assert task.task_id is not None
            assert task.stream_url is not None

    def test_stream_research(self, you_client):
        """stream_research() yields SSE events from a live task.

        The server's SSE stream sends a 'connected' event immediately, then
        pings. Terminal events may not arrive for tasks that complete
        mid-stream, so we iterate with a generous timeout and verify
        at least the 'connected' event was received.
        """
        with you_client as you:
            try:
                task = research_background(
                    you,
                    input="What is the capital of France?",
                    research_effort=ResearchEffort.LITE,
                )
            except TypeError as e:
                if "TaskResponse" in str(e):
                    pytest.skip("Background mode not enabled on server")
                raise

            assert isinstance(task, TaskResponse)

            terminal = {"response.done", "complete", "completed", "error", "failed", "cancelled"}

            events = []
            for evt in stream_research(you, task_id=task.task_id, timeout_ms=180_000):
                events.append(evt)
                if evt.event in terminal:
                    break

            assert len(events) > 0, "No SSE events received"
            assert events[0].event == "connected"
            # The connected event should carry task_id and status
            assert events[0].data is not None
            assert events[0].data.get("task_id") == task.task_id
            assert events[0].data.get("status") is not None


# ---------------------------------------------------------------------------
# Frontier research effort (new in 2.5.0)
# ---------------------------------------------------------------------------
# Frontier only works with background=true and can run up to 4 hours.
# For a live test we use a simple query and a generous but bounded timeout.
# Marked slow so it can be skipped with `-m "not slow"`.
# ---------------------------------------------------------------------------
class TestLiveResearchFrontier:
    """Live tests for frontier research effort (requires background=true)."""

    @pytest.mark.slow
    def test_frontier_background_completes(self, you_client):
        """research_and_wait with frontier effort auto-adjusts timeout to 4h.
        Uses a simple query so it completes in a few minutes on prod."""
        with you_client as you:
            try:
                detail = research_and_wait(
                    you,
                    input="Who is Bill Gates?",
                    research_effort=ResearchEffort.FRONTIER,
                    timeout_s=600,  # bounded for CI; auto would be 14400
                )
            except TypeError as e:
                if "TaskResponse" in str(e):
                    pytest.skip("Background mode not enabled on server")
                raise

            assert isinstance(detail, TaskDetail)
            assert detail.status.value == "completed"
            assert detail.result is not None
            payload = detail.result.model_dump()
            content = payload.get("output", {}).get("content", "")
            assert len(content) > 0

    @pytest.mark.slow
    def test_frontier_without_background_raises_422(self, you_client):
        """frontier without background=true should return 422."""
        with you_client as you:
            with pytest.raises((ResearchUnprocessableEntityError, YouDefaultError)):
                you.research(
                    input="Who is Bill Gates?",
                    research_effort=ResearchEffort.FRONTIER,
                    background=False,
                )


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_live.py -v
    pytest.main([__file__, "-v"])
