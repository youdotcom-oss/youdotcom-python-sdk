import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    SearchForbiddenError,
    SearchUnauthorizedError,
)
from youdotcom.models import (
    Country,
    Freshness,
    LiveCrawl,
    LiveCrawlFormats,
    SafeSearch,
)


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestSearchBasic:
    def test_basic_search(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(query="latest AI developments", server_url=server_url)
            
            assert res.results is not None
            assert res.metadata is not None
            assert res.metadata.query is not None
            assert res.results.web or res.results.news


class TestSearchFilters:
    def test_search_with_filters(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="renewable energy",
                count=10,
                freshness=Freshness.WEEK,
                country=Country.US,
                safesearch=SafeSearch.MODERATE,
                server_url=server_url,
            )
            
            assert res.results is not None
            assert res.metadata is not None

    def test_search_with_pagination(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="python programming",
                count=5,
                offset=1,
                server_url=server_url,
            )
            
            assert res.results is not None
            assert res.metadata is not None

    def test_search_with_livecrawl(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="machine learning tutorials",
                count=3,
                livecrawl=LiveCrawl.WEB,
                livecrawl_formats=LiveCrawlFormats.MARKDOWN,
                server_url=server_url,
            )
            
            assert res.results is not None
            
            if res.results.web:
                for result in res.results.web:
                    if hasattr(result, "contents") and result.contents:
                        assert result.contents.markdown is not None

    def test_search_all_parameters(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="quantum computing",
                count=20,
                offset=0,
                freshness=Freshness.MONTH,
                country=Country.GB,
                safesearch=SafeSearch.STRICT,
                livecrawl=LiveCrawl.WEB,
                livecrawl_formats=LiveCrawlFormats.HTML,
                server_url=server_url,
            )
            
            assert res.results is not None
            assert res.metadata is not None
            
            if res.results.web:
                for result in res.results.web:
                    if hasattr(result, "contents") and result.contents:
                        assert result.contents.html is not None

    def test_search_news_with_livecrawl(self, server_url, api_key):
        """Test that news results can have contents when livecrawl is enabled (new in 2.2.0)."""
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="technology news",
                count=5,
                livecrawl=LiveCrawl.NEWS,
                livecrawl_formats=LiveCrawlFormats.MARKDOWN,
                server_url=server_url,
            )
            
            assert res.results is not None
            
            # News results can now have contents field when livecrawl is enabled
            if res.results.news:
                for news_item in res.results.news:
                    # Contents field is optional but should be accessible
                    if hasattr(news_item, "contents") and news_item.contents:
                        # If contents exists, it should have markdown when requested
                        assert news_item.contents.markdown is not None or news_item.contents.html is not None

    def test_search_livecrawl_all_with_news_contents(self, server_url, api_key):
        """Test livecrawl=ALL returns contents for both web and news results."""
        client = create_test_http_client("get_/v1/search")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.search.unified(
                query="breaking tech news",
                count=3,
                livecrawl=LiveCrawl.ALL,
                livecrawl_formats=LiveCrawlFormats.HTML,
                server_url=server_url,
            )
            
            assert res.results is not None
            
            # Both web and news can have contents with livecrawl=ALL
            if res.results.web:
                for result in res.results.web:
                    if hasattr(result, "contents") and result.contents:
                        assert result.contents.html is not None
            
            if res.results.news:
                for news_item in res.results.news:
                    if hasattr(news_item, "contents") and news_item.contents:
                        assert news_item.contents.html is not None


class TestSearchErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("get_/v1/search-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises((SearchUnauthorizedError, SearchForbiddenError)):
                you.search.unified(query="test", server_url=server_url)

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises(SearchForbiddenError):
                you.search.unified(query="test", server_url=server_url)
