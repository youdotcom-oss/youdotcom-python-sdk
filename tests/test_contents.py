import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    ContentsForbiddenError,
    ContentsUnauthorizedError,
)
from youdotcom.models import ContentsFormats


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestContentsBasic:
    def test_html_format(self, server_url, api_key):
        """Test fetching content in HTML format using the new formats array."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org", "https://www.example.com"],
                formats=[ContentsFormats.HTML],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
            assert res[0].url is not None

    def test_markdown_format(self, server_url, api_key):
        """Test fetching content in Markdown format using the new formats array."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org"],
                formats=[ContentsFormats.MARKDOWN],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_metadata_format(self, server_url, api_key):
        """Test fetching metadata (json+ld, opengraph info) using the new formats array."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org"],
                formats=[ContentsFormats.METADATA],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
            # Metadata should be returned when metadata format is requested
            assert res[0].metadata is not None

    def test_multiple_formats(self, server_url, api_key):
        """Test fetching multiple formats at once (html, markdown, metadata)."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org"],
                formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN, ContentsFormats.METADATA],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_multiple_urls(self, server_url, api_key):
        """Test fetching content from multiple URLs."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=[
                    "https://www.you.com",
                    "https://www.github.com",
                    "https://www.python.org",
                ],
                formats=[ContentsFormats.MARKDOWN],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_single_url(self, server_url, api_key):
        """Test fetching content from a single URL."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.HTML],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_without_formats(self, server_url, api_key):
        """Test fetching content without specifying formats (should use default)."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_crawl_timeout(self, server_url, api_key):
        """Test the crawl_timeout parameter (1-60 seconds)."""
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                formats=[ContentsFormats.HTML],
                crawl_timeout=30,  # Set timeout to 30 seconds
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0


class TestContentsErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/contents-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises(ContentsUnauthorizedError):
                you.contents.generate(
                    urls=["https://www.example.com"],
                    server_url=server_url,
                )

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises(ContentsForbiddenError):
                you.contents.generate(
                    urls=["https://www.example.com"],
                    server_url=server_url,
                )

    def test_empty_urls(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=[],
                formats=[ContentsFormats.HTML],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
