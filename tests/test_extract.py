"""Tests for ``you.extract()`` on ``POST /v1/extract``.

Locks the contract:

- One ``url`` per call. Unset options stay off the wire so the API applies its
  own defaults; ``full_page`` takes a dict or an ``ExtractionFullPage``.
- The request is strict: unknown keys and an out-of-range ``timeout`` raise
  ``ValidationError`` locally, mirroring the API's 422.
- ``{}`` (nothing extracted) parses to an ``ExtractResponse`` of ``None``s.
- Every error in the API's own envelope raises ``ExtractError``; gateway bodies
  fall back to the shared error classes.
- 502 (a page that cannot be extracted) is not retried.
- Without any ``timeout_ms``, the client timeout follows the server ``timeout``.
"""

import json
from contextlib import asynccontextmanager, contextmanager

import httpx
import pytest
from pydantic import ValidationError

from youdotcom import You, errors
from youdotcom.models import (
    ExtractionFormat,
    ExtractionFullPage,
    ExtractionSource,
    ExtractResponse,
    ParseEffort,
)
from youdotcom.utils import BackoffStrategy, RetryConfig


MOCK_URL = "http://mock.local"

_PAGE = {
    "url": "https://example.com",
    "extraction_source": "blend",
    "title": "Example Domain",
    "contents": {"full_page": {"markdown": "# Example", "html": "<h1>Example</h1>"}},
    "metadata": {"site_name": None, "favicon_url": "https://example.com/favicon"},
}


def _json(status: int, body) -> httpx.Response:
    return httpx.Response(
        status, headers={"content-type": "application/json"}, content=json.dumps(body)
    )


def _envelope(code: str, retryable: bool = False, details=None) -> dict:
    error = {"code": code, "message": "m", "retryable": retryable, "request_id": "rid"}
    if details is not None:
        error["details"] = details
    return {"error": error}


@contextmanager
def _capture(response: httpx.Response = None, *, timeout_ms=None):
    """Yield (You, captured) over a mock transport; captured holds the last request."""
    captured: dict = {"calls": 0}

    def handler(request):
        captured["calls"] += 1
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["timeout"] = request.extensions.get("timeout", {}).get("read")
        captured["api_key"] = request.headers.get("x-api-key")
        return response if response is not None else _json(200, _PAGE)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(api_key_auth="k", client=client, timeout_ms=timeout_ms) as you:
            yield you, captured
    finally:
        client.close()


def _extract_body(**kwargs) -> dict:
    with _capture() as (you, captured):
        you.extract(url="https://example.com", server_url=MOCK_URL, **kwargs)
    return captured["body"]


class TestRequest:
    def test_bare_url_sends_only_url(self):
        assert _extract_body() == {"url": "https://example.com"}

    def test_explicit_none_options_stay_off_the_wire(self):
        body = _extract_body(
            full_page=None, extraction_source=None, timeout=None, parse_effort=None
        )
        assert body == {"url": "https://example.com"}

    def test_every_option_reaches_the_wire(self):
        body = _extract_body(
            full_page={"extraction_formats": ["markdown", "html"]},
            extraction_source="fetch",
            timeout=60,
            parse_effort="lite",
        )
        assert body == {
            "url": "https://example.com",
            "full_page": {"extraction_formats": ["markdown", "html"]},
            "extraction_source": "fetch",
            "timeout": 60,
            "parse_effort": "lite",
        }

    def test_model_and_enum_forms_match_the_dict_form(self):
        as_models = _extract_body(
            full_page=ExtractionFullPage(extraction_formats=[ExtractionFormat.HTML]),
            extraction_source=ExtractionSource.CACHE,
            parse_effort=ParseEffort.STANDARD,
        )
        as_strings = _extract_body(
            full_page={"extraction_formats": ["html"]},
            extraction_source="CACHE",
            parse_effort="Standard",
        )
        assert as_models == as_strings

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"timeout": 1},
            {"timeout": 101},
            {"full_page": {"formats": ["markdown"]}},
            {"full_page": {"extraction_formats": ["pdf"]}},
            {"extraction_source": "web"},
            {"parse_effort": "max"},
        ],
    )
    def test_invalid_input_raises_before_sending(self, kwargs):
        with _capture() as (you, captured):
            with pytest.raises(ValidationError):
                you.extract(url="https://example.com", server_url=MOCK_URL, **kwargs)
        assert captured["calls"] == 0

    def test_default_host_and_path(self):
        with _capture() as (you, captured):
            you.extract(url="https://example.com")
        assert captured["url"] == "https://ydc-index.io/v1/extract"

    def test_sends_the_api_key(self):
        with _capture() as (you, captured):
            you.extract(url="https://example.com", server_url=MOCK_URL)
        assert captured["api_key"] == "k"


class TestTypes:
    def test_request_typeddict_is_exported(self):
        from youdotcom.models import ExtractRequest, ExtractRequestTypedDict

        body: ExtractRequestTypedDict = {
            "url": "https://example.com",
            "full_page": {"extraction_formats": ["html"]},
            "extraction_source": "cache",
            "timeout": 60,
            "parse_effort": "lite",
        }
        assert ExtractRequest.model_validate(body).timeout == 60


class TestClientTimeout:
    def test_follows_the_server_default(self):
        with _capture() as (you, captured):
            you.extract(url="https://example.com", server_url=MOCK_URL)
        assert captured["timeout"] == 40

    def test_follows_an_explicit_server_timeout(self):
        with _capture() as (you, captured):
            you.extract(url="https://example.com", server_url=MOCK_URL, timeout=100)
        assert captured["timeout"] == 110

    def test_client_timeout_ms_wins(self):
        with _capture(timeout_ms=5_000) as (you, captured):
            you.extract(url="https://example.com", server_url=MOCK_URL, timeout=100)
        assert captured["timeout"] == 5

    def test_call_timeout_ms_wins(self):
        with _capture(timeout_ms=5_000) as (you, captured):
            you.extract(url="https://example.com", server_url=MOCK_URL, timeout_ms=7_000)
        assert captured["timeout"] == 7


class TestResponse:
    def test_parses_a_page(self):
        with _capture() as (you, _):
            res = you.extract(url="https://example.com", server_url=MOCK_URL)
        assert isinstance(res, ExtractResponse)
        assert res.title == "Example Domain"
        assert res.contents.full_page.markdown == "# Example"
        assert res.contents.full_page.html == "<h1>Example</h1>"
        assert res.metadata.site_name is None
        assert res.metadata.favicon_url == "https://example.com/favicon"

    def test_empty_object_means_nothing_extracted(self):
        with _capture(_json(200, {})) as (you, _):
            res = you.extract(url="https://example.com", server_url=MOCK_URL)
        assert res == ExtractResponse()

    def test_unknown_fields_and_values_are_tolerated(self):
        page = {**_PAGE, "extraction_source": "future_source", "future_field": 1}
        with _capture(_json(200, page)) as (you, _):
            res = you.extract(url="https://example.com", server_url=MOCK_URL)
        assert res.extraction_source == "future_source"


class TestErrors:
    @pytest.mark.parametrize(
        "status,code",
        [
            (402, "payment_required"),
            (422, "invalid_request"),
            (422, "invalid_url"),
            (500, "internal_error"),
            (502, "site_blocked"),
            (503, "service_unavailable"),
            (504, "timeout"),
        ],
    )
    def test_api_errors_raise_extract_error(self, status, code):
        with _capture(_json(status, _envelope(code))) as (you, _):
            with pytest.raises(errors.ExtractError) as exc:
                you.extract(url="https://example.com", server_url=MOCK_URL)
        assert exc.value.status_code == status
        assert exc.value.code == code
        assert exc.value.request_id == "rid"

    def test_error_details_are_typed(self):
        details = {"timeout_s": 30, "page_count": 1200}
        with _capture(_json(422, _envelope("pdf_too_large", details=details))) as (you, _):
            with pytest.raises(errors.ExtractError) as exc:
                you.extract(url="https://example.com", server_url=MOCK_URL)
        assert exc.value.data.error.details.page_count == 1200
        assert exc.value.data.error.details.timeout_s == 30

    def test_validation_fields_are_typed(self):
        details = {"fields": [{"field": "timeout", "message": "too large"}]}
        with _capture(_json(422, _envelope("invalid_request", details=details))) as (you, _):
            with pytest.raises(errors.ExtractError) as exc:
                you.extract(url="https://example.com", server_url=MOCK_URL)
        assert exc.value.data.error.details.fields[0].field == "timeout"

    @pytest.mark.parametrize(
        "status,body,error_class",
        [
            (401, {"detail": "Invalid or expired API key"}, errors.UnauthorizedResponseError),
            (
                402,
                {"error": "payment_required", "message": "m", "upgrade_url": "u"},
                errors.PaymentRequiredResponseError,
            ),
            (403, {"message": "Forbidden"}, errors.ForbiddenResponseError),
            (429, {"errors": [{"title": "Rate limit exceeded"}]}, errors.YouDefaultError),
        ],
    )
    def test_gateway_bodies_raise_shared_errors(self, status, body, error_class):
        with _capture(_json(status, body)) as (you, _):
            with pytest.raises(error_class) as exc:
                you.extract(url="https://example.com", server_url=MOCK_URL)
        assert exc.value.status_code == status

    def test_does_not_retry_502(self):
        retries = RetryConfig("backoff", BackoffStrategy(1, 1, 1.0, 100), False)
        with _capture(_json(502, _envelope("site_blocked"))) as (you, captured):
            with pytest.raises(errors.ExtractError):
                you.extract(url="https://example.com", server_url=MOCK_URL, retries=retries)
        assert captured["calls"] == 1

    def test_retries_503(self):
        retries = RetryConfig("backoff", BackoffStrategy(1, 1, 1.0, 100), False)
        with _capture(_json(503, _envelope("service_unavailable", True))) as (you, captured):
            with pytest.raises(errors.ExtractError):
                you.extract(url="https://example.com", server_url=MOCK_URL, retries=retries)
        assert captured["calls"] > 1


@asynccontextmanager
async def _async_capture(response: httpx.Response = None):
    captured: dict = {"calls": 0}

    def handler(request):
        captured["calls"] += 1
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        captured["timeout"] = request.extensions.get("timeout", {}).get("read")
        return response if response is not None else _json(200, _PAGE)

    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        async with You(api_key_auth="k", async_client=async_client) as you:
            yield you, captured
    finally:
        await async_client.aclose()


class TestAsync:
    @pytest.mark.asyncio
    async def test_matches_sync(self):
        async with _async_capture() as (you, captured):
            res = await you.extract_async(
                url="https://example.com", extraction_source="fetch", timeout=60
            )
        assert captured["url"] == "https://ydc-index.io/v1/extract"
        assert captured["body"] == {
            "url": "https://example.com",
            "extraction_source": "fetch",
            "timeout": 60,
        }
        assert captured["timeout"] == 70
        assert res.contents.full_page.markdown == "# Example"

    @pytest.mark.asyncio
    async def test_does_not_retry_502(self):
        retries = RetryConfig("backoff", BackoffStrategy(1, 1, 1.0, 100), False)
        async with _async_capture(_json(502, _envelope("site_blocked"))) as (you, captured):
            with pytest.raises(errors.ExtractError):
                await you.extract_async(url="https://example.com", retries=retries)
        assert captured["calls"] == 1

    @pytest.mark.asyncio
    async def test_raises_extract_error(self):
        async with _async_capture(_json(422, _envelope("invalid_url"))) as (you, _):
            with pytest.raises(errors.ExtractError) as exc:
                await you.extract_async(url="http://127.0.0.1/")
        assert exc.value.code == "invalid_url"
