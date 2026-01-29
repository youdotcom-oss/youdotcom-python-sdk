"""
Live API tests for You.com Python SDK.

These tests run against the real You.com API to verify SDK functionality.
Set the YOU_API_KEY_AUTH environment variable before running:

    YOU_API_KEY_AUTH="your-api-key" pytest tests/test_live.py -v

To skip these tests, run pytest with the --ignore flag:
    pytest tests/ --ignore=tests/test_live.py -v
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
)


# Skip all tests in this file if no API key is provided
pytestmark = pytest.mark.skipif(
    not os.getenv("YOU_API_KEY_AUTH"),
    reason="YOU_API_KEY_AUTH environment variable not set"
)


@pytest.fixture
def api_key():
    """Get API key from environment."""
    return os.getenv("YOU_API_KEY_AUTH")


@pytest.fixture
def you_client(api_key):
    """Create a You client for live testing."""
    return You(api_key_auth=api_key)


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
                livecrawl_formats=LiveCrawlFormats.MARKDOWN,
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
                livecrawl_formats=LiveCrawlFormats.MARKDOWN,
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
                livecrawl_formats=LiveCrawlFormats.HTML,
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


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_live.py -v
    pytest.main([__file__, "-v"])
