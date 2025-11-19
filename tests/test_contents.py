import os
import pytest

from tests.test_client import create_test_http_client
from youdotcom import You
from youdotcom.errors import (
    PostV1ContentsForbiddenError,
    PostV1ContentsUnauthorizedError,
)
from youdotcom.types.typesafe_models import Format


@pytest.fixture
def server_url():
    return os.getenv("TEST_SERVER_URL", "http://localhost:18080")


@pytest.fixture
def api_key():
    return os.getenv("YOU_API_KEY_AUTH", "test-api-key")


class TestContentsBasic:
    def test_html_format(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org", "https://www.example.com"],
                format_=Format.HTML,
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0
            assert res[0].url is not None

    def test_markdown_format(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.python.org"],
                format_=Format.MARKDOWN,
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_multiple_urls(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=[
                    "https://www.you.com",
                    "https://www.github.com",
                    "https://www.python.org",
                ],
                format_=Format.MARKDOWN,
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_single_url(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                format_=Format.HTML,
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0

    def test_without_format(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=["https://www.example.com"],
                server_url=server_url,
            )
            
            assert isinstance(res, list)
            assert len(res) > 0


class TestContentsErrors:
    def test_unauthorized(self, server_url):
        client = create_test_http_client("post_/v1/contents-unauthorized")
        
        with You(server_url=server_url, client=client, api_key_auth="invalid") as you:
            with pytest.raises(PostV1ContentsUnauthorizedError):
                you.contents.generate(
                    urls=["https://www.example.com"],
                    server_url=server_url,
                )

    def test_forbidden(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents-forbidden")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            with pytest.raises(PostV1ContentsForbiddenError):
                you.contents.generate(
                    urls=["https://www.example.com"],
                    server_url=server_url,
                )

    def test_empty_urls(self, server_url, api_key):
        client = create_test_http_client("post_/v1/contents")
        
        with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
            res = you.contents.generate(
                urls=[],
                format_=Format.HTML,
                server_url=server_url,
            )
            
            assert isinstance(res, list)
