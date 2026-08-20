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

import httpx
import pytest

from youdotcom import You
from youdotcom.models import (
    Country,
    ContentsFormats,
    Extraction,
    ExtractionFormat,
    ExtractionMode,
    Freshness,
    LiveCrawl,
    LiveCrawlFormats,
    SafeSearch,
    ResearchEffort,
    ResearchResponse,
    TaskResponse,
    TaskDetail,
    FinanceResearchEffort,
    AnswerResponse,
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


# Skip keyed tests if no API key is provided.
# Mirror the SDK's own env-var precedence (YDC_API_KEY first, then
# YOU_API_KEY_AUTH as the documented 2.3.x fallback) so users on the
# fallback env var don't get their live suite silently skipped.
requires_api_key = pytest.mark.skipif(
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


@requires_api_key
class TestLiveSearch:
    """Live tests for the Search API."""
    
    def test_basic_search(self, you_client):
        """Test basic search functionality against live API."""
        with you_client as you:
            res = you.search(query="Python programming language")
            
            assert res.results is not None
            assert res.metadata is not None
            assert res.metadata.query == "Python programming language"
            assert res.results.web is not None
            assert len(res.results.web) > 0
    
    def test_search_with_filters(self, you_client):
        """Test search with filters against live API."""
        with you_client as you:
            res = you.search(
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
    
    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_search_with_livecrawl_web(self, you_client):
        """Test search with livecrawl for web results.

        Deprecated: use ``extraction`` instead. Livecrawl continues to work
        (the server accepts it) but emits ``DeprecationWarning``.
        """
        with you_client as you:
            res = you.search(
                query="machine learning tutorials",
                count=3,
                livecrawl=LiveCrawl.WEB,
                livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
            )

            assert res.results is not None

            # Web results may have contents
            content_seen = [
                (result.contents.html, result.contents.markdown)
                for result in res.results.web or []
                if result.contents
                and (
                    result.contents.html is not None
                    or result.contents.markdown is not None
                )
            ]
            assert content_seen, (
                "Expected at least one result with contents.html and/or contents.markdown"
            )

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_search_with_livecrawl_news(self, you_client):
        """Test search with livecrawl for news results (new in 2.2.0).

        Deprecated: use ``extraction`` instead.
        """
        with you_client as you:
            res = you.search(
                query="technology news today",
                count=3,
                livecrawl=LiveCrawl.NEWS,
                livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
            )

            assert res.results is not None

            # News results can now have contents field (new in 2.2.0)
            content_seen = [
                (item.contents.html, item.contents.markdown)
                for item in res.results.news or []
                if item.contents
                and (item.contents.html is not None or item.contents.markdown is not None)
            ]
            assert content_seen, (
                "Expected at least one news result with contents.html and/or contents.markdown"
            )

    @pytest.mark.filterwarnings("ignore::DeprecationWarning")
    def test_search_with_livecrawl_all(self, you_client):
        """Test search with livecrawl=ALL for both web and news.

        Deprecated: use ``extraction`` instead.
        """
        with you_client as you:
            res = you.search(
                query="breaking tech news",
                count=3,
                livecrawl=LiveCrawl.ALL,
                livecrawl_formats=[LiveCrawlFormats.HTML],
            )

            assert res.results is not None

            # livecrawl=ALL covers both web and news; assert at least one
            # of each has contents.html / contents.markdown populated.
            web_content_seen = [
                (r.contents.html, r.contents.markdown)
                for r in res.results.web or []
                if r.contents
                and (r.contents.html is not None or r.contents.markdown is not None)
            ]
            news_content_seen = [
                (n.contents.html, n.contents.markdown)
                for n in res.results.news or []
                if n.contents
                and (n.contents.html is not None or n.contents.markdown is not None)
            ]
            assert web_content_seen, (
                "Expected at least one web result with contents.html and/or contents.markdown"
            )
            assert news_content_seen, (
                "Expected at least one news result with contents.html and/or contents.markdown"
            )


@requires_api_key
class TestLiveSearchExtraction:
    """Live tests for the ``extraction`` parameter (new in 3.1.0).

    ``extraction`` replaces ``livecrawl`` / ``livecrawl_formats`` on
    ``POST /v1/search``. Two modes:

    - ``extraction_mode="highlights"`` — query-relevant excerpts land in
      ``results.web[].contents.highlights``; snippets are omitted.
    - ``extraction_mode="full_page"`` — full HTML and/or Markdown in
      ``results.web[].contents.html`` / ``.markdown``.
    """

    def test_highlights_mode(self, you_client):
        """Test extraction_mode=highlights returns excerpts in contents.highlights."""
        with you_client as you:
            res = you.search(
                query="Python type hints guide",
                count=3,
                extraction=Extraction(
                    extraction_mode=ExtractionMode.HIGHLIGHTS,
                ),
            )

            assert res.results is not None
            # Highlights mode omits snippets; contents.highlights should be a list
            assert res.results.web
            highlights_seen = [
                result.contents.highlights
                for result in res.results.web
                if result.contents and result.contents.highlights is not None
            ]
            assert highlights_seen, "Expected at least one result with contents.highlights"
            assert all(isinstance(h, list) for h in highlights_seen)

    def test_full_page_markdown(self, you_client):
        """Test extraction_mode=full_page with markdown format."""
        with you_client as you:
            res = you.search(
                query="how does python work",
                count=3,
                extraction={
                    "extraction_mode": "full_page",
                    "full_page": {"extraction_formats": ["markdown"]},
                },
            )

            assert res.results is not None
            assert res.results.web
            markdown_seen = [
                result.contents.markdown
                for result in res.results.web
                if result.contents and result.contents.markdown is not None
            ]
            assert markdown_seen, (
                "Expected at least one result with contents.markdown"
            )

    def test_full_page_html(self, you_client):
        """Test extraction_mode=full_page with html format."""
        with you_client as you:
            res = you.search(
                query="what is a web browser",
                count=3,
                extraction={
                    "extraction_mode": "full_page",
                    "full_page": {"extraction_formats": ["html"]},
                },
            )

            assert res.results is not None
            assert res.results.web
            html_seen = [
                result.contents.html
                for result in res.results.web
                if result.contents and result.contents.html is not None
            ]
            assert html_seen, (
                "Expected at least one result with contents.html"
            )

    def test_full_page_both_formats(self, you_client):
        """Test extraction_mode=full_page with both html and markdown."""
        with you_client as you:
            res = you.search(
                query="how does the internet work",
                count=3,
                extraction={
                    "extraction_mode": "full_page",
                    "full_page": {"extraction_formats": ["html", "markdown"]},
                },
            )

            assert res.results is not None
            assert res.results.web
            content_seen = [
                (result.contents.html, result.contents.markdown)
                for result in res.results.web
                if result.contents
                and (
                    result.contents.html is not None
                    or result.contents.markdown is not None
                )
            ]
            assert content_seen, (
                "Expected at least one result with contents.html and/or contents.markdown"
            )
            for html, md in content_seen:
                if html is not None:
                    assert isinstance(html, str)
                if md is not None:
                    assert isinstance(md, str)


@requires_api_key
class TestLiveContents:
    """Live tests for the Contents API."""
    
    def test_html_format(self, you_client):
        """Test fetching content in HTML format."""
        with you_client as you:
            res = you.contents(
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
            res = you.contents(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.MARKDOWN],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
    
    def test_metadata_format(self, you_client):
        """Test fetching metadata from a page."""
        with you_client as you:
            res = you.contents(
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
            res = you.contents(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN],
            )
            
            assert isinstance(res, list)
            assert len(res) > 0


@requires_api_key
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


@requires_api_key
class TestLiveResearchOutputSchema:
    """Live test for Research `output_schema` parameter (beta feature).

    Smoke-tests prod to ensure the
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


@requires_api_key
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


@requires_api_key
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


@requires_api_key
class TestLiveContentsMaxAge:
    """Live test for Contents `max_age` parameter.

    `max_age` controls cache freshness — when set, cached content older
    than the threshold is ignored and the page is re-fetched.
    """

    def test_contents_with_max_age(self, you_client):
        """max_age is accepted as an optional parameter."""
        with you_client as you:
            res = you.contents(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.MARKDOWN],
                max_age=86400,  # 1 day
            )

            assert isinstance(res, list)
            assert len(res) > 0


@requires_api_key
class TestLiveSearchBoostDomains:
    """Live test for Search `boost_domains` parameter.

    `boost_domains` prefers certain domains in ranking without excluding
    other domains — for a more permissive alternative to `include_domains`.
    """

    def test_search_boost_domains_list(self, you_client):
        """search accepts a Python list of boost domains."""
        with you_client as you:
            res = you.search(
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


@requires_api_key
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


@requires_api_key
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
@requires_api_key
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


# ---------------------------------------------------------------------------
# Answer API (new in 3.0.0)
# ---------------------------------------------------------------------------
@requires_api_key
class TestLiveAnswer:
    """Live tests for the Answer API (POST /v1/answer).

    The Answer API returns a synthesized answer with citations and web results.
    Requires an API key.
    """

    def test_basic_answer(self, you_client):
        """Test basic answer query returns AnswerResponse with answer + citations."""
        with you_client as you:
            res = you.answer(query="What is the capital of France?")

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0
            # Citations should be present for a factual query
            assert len(res.citations) > 0
            for citation in res.citations:
                assert citation.source is not None
                assert len(citation.source) > 0
            # Web results should be present
            assert len(res.results.web) > 0
            for result in res.results.web:
                assert result.url is not None
                assert result.title is not None

    def test_answer_with_freshness(self, you_client):
        """Test answer with freshness filter."""
        with you_client as you:
            res = you.answer(
                query="Latest AI developments",
                freshness="week",
            )

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0

    def test_answer_with_country(self, you_client):
        """Test answer with country filter."""
        with you_client as you:
            res = you.answer(
                query="Best restaurants in London",
                country=Country.GB,
            )

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0

    def test_answer_with_boost_domains(self, you_client):
        """Test answer with boost_domains (can combine with exclude, not include)."""
        with you_client as you:
            res = you.answer(
                query="Python type hints",
                boost_domains=["python.org", "docs.python.org"],
            )

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0

    def test_answer_with_safesearch(self, you_client):
        """Test answer with safesearch content filter."""
        with you_client as you:
            res = you.answer(
                query="Latest science news",
                safesearch=SafeSearch.STRICT,
            )

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0

    @pytest.mark.asyncio
    async def test_async_answer(self, you_client):
        """Test async you.answer_async()."""
        # ``async with`` (not ``with``) so the async transport is closed on
        # exit; the sync context manager leaves it open, which surfaces as an
        # unclosed-socket ResourceWarning at interpreter teardown. Matches the
        # convention every other async test in the suite uses.
        async with you_client as you:
            res = await you.answer_async(query="What is 2+2?")

            assert isinstance(res, AnswerResponse)
            assert len(res.answer) > 0


@requires_api_key
class TestLiveAttribution:
    """The ``X-Client-Info`` header on real requests (DX-777).

    The mock-transport tests in ``tests/test_attribution.py`` pin the wire
    format; what they cannot show is that the real API *accepts* the header.
    An unknown header that tripped a WAF rule or a strict gateway would fail
    only against prod, so this asserts both halves: the header went out on
    every request, and the live call still succeeded.

    Uses an ``httpx`` request event hook to observe the outbound headers,
    accumulating them into a list and asserting on the accumulated matches --
    the contract-list pattern AGENTS.md prescribes for live tests.
    """

    @staticmethod
    def _client_with_hook(observed: list):
        """A real httpx client that records the headers of each request."""

        def record(request: httpx.Request) -> None:
            # Lowercase the keys on the way in. httpx already normalizes, but
            # HTTP header names are case-insensitive, so pinning the casing
            # here is what lets every assertion below index directly instead
            # of guarding each lookup.
            observed.append({k.lower(): v for k, v in request.headers.items()})

        return httpx.Client(
            follow_redirects=True, event_hooks={"request": [record]}
        )

    def test_x_client_info_sent_and_accepted_live(self, api_key):
        observed: list = []
        http_client = self._client_with_hook(observed)
        try:
            with You(
                api_key_auth=api_key,
                timeout_ms=LIVE_TIMEOUT_MS,
                client=http_client,
                app_name="sdk-live-test",
                app_version="0.0.1",
                app_title="sdk-live-test",
                app_url="https://example.com/live?x=1",
            ) as you:
                res = you.search(query="You.com Python SDK")

            # The live call itself must succeed -- i.e. the header did not
            # trip a gateway or WAF rule on the way in.
            assert res.results is not None

            matches = [h["x-client-info"] for h in observed if "x-client-info" in h]
            assert matches, (
                "no request carried X-Client-Info; "
                f"headers seen: {[sorted(h) for h in observed]}"
            )
            for value in matches:
                assert value.startswith("sdk; client=sdk-live-test/0.0.1")
                assert "title=sdk-live-test" in value
                # Query strings must survive the segment delimiter.
                assert "url=https://example.com/live?x=1" in value
                assert "; ua=python/" in value
                assert "httpx/" in value
        finally:
            http_client.close()

    def test_x_mcp_attribution_absent_live(self, api_key):
        """The SDK never sets the MCP-side header, on a real request either."""
        observed: list = []
        http_client = self._client_with_hook(observed)
        try:
            with You(
                api_key_auth=api_key,
                timeout_ms=LIVE_TIMEOUT_MS,
                client=http_client,
            ) as you:
                you.search(query="You.com Python SDK")

            assert observed, "no request was observed"
            offenders = [
                name for headers in observed for name in headers if "mcp" in name
            ]
            assert not offenders, f"SDK emitted MCP-specific headers: {offenders}"
        finally:
            http_client.close()


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_live.py -v
    pytest.main([__file__, "-v"])
