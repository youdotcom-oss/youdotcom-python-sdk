import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    GetV1SearchForbiddenError,
    GetV1SearchUnauthorizedError,
)
from youdotcom.types.typesafe_models import (
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
            res = you.search.unified(query="latest AI developments")
            
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
            )
            
            assert res.results is not None

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
            )
            
            assert res.results is not None
            assert res.metadata is not None


class TestSearchErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("get_/v1/search-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises(GetV1SearchUnauthorizedError):
                you.search.unified(query="test")

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("get_/v1/search-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises(GetV1SearchForbiddenError):
                you.search.unified(query="test")
