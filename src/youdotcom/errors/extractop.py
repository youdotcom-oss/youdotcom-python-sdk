"""Error model for ``POST /v1/extract``.

Every Extract error the API itself returns (402, 422, 500, 502, 503, 504)
shares one body:

    {"error": {"code", "message", "retryable", "request_id", "details"?}}

Branch on ``code``: it is stable, new values may be added, and existing ones
are never renamed or removed. ``message`` is for people and may be reworded.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import httpx
from typing import List, Optional
from youdotcom.errors import YouError
from youdotcom.types import BaseModel


class ExtractErrorField(BaseModel):
    r"""One validation problem on an ``invalid_request`` error."""

    field: Optional[str] = None
    r"""Dotted path to the invalid field, such as ``full_page.extraction_formats.0``, or ``body`` when the body itself can't be parsed."""

    message: Optional[str] = None
    r"""What is wrong with the field."""


class ExtractErrorDetails(BaseModel):
    r"""Extra context for some codes. Fields not relevant to the code are ``None``."""

    fields: Optional[List[ExtractErrorField]] = None
    r"""``invalid_request`` only. One entry per validation problem."""

    reason: Optional[str] = None
    r"""Cause of the error, for ``invalid_url``, ``site_blocked``, ``site_unreachable``, and ``unsupported_content``."""

    content_type: Optional[str] = None
    r"""``unsupported_content`` only, when known. The content type of the page."""

    timeout_s: Optional[int] = None
    r"""``timeout`` and ``pdf_too_large`` only. The timeout, in seconds, that applied to the request."""

    page_count: Optional[int] = None
    r"""``pdf_too_large`` only, when known. The number of pages in the PDF."""

    upgrade_url: Optional[str] = None
    r"""``payment_required`` only. Where to add credits."""


class ExtractErrorDetail(BaseModel):
    r"""The ``error`` object of an Extract error body."""

    code: str
    r"""Stable error code to branch on, such as ``invalid_request``, ``invalid_url``, ``pdf_too_large``, ``site_blocked``, ``timeout``, or ``service_unavailable``. New codes may be added; existing codes are never renamed or removed."""

    message: Optional[str] = None
    r"""Human-readable explanation. The wording can change, so don't parse it."""

    retryable: Optional[bool] = None
    r"""Whether sending the same request again can succeed."""

    request_id: Optional[str] = None
    r"""The You.com ID for this request. Include it when you contact support."""

    details: Optional[ExtractErrorDetails] = None
    r"""Extra context for some codes."""


class ExtractErrorData(BaseModel):
    r"""The body of an Extract error response."""

    error: ExtractErrorDetail


@dataclass(unsafe_hash=True)
class ExtractError(YouError):
    r"""An error returned by the Extract API. Branch on ``data.error.code``."""

    data: ExtractErrorData = field(hash=False)

    def __init__(
        self,
        data: ExtractErrorData,
        raw_response: httpx.Response,
        body: Optional[str] = None,
    ):
        message = body or raw_response.text
        super().__init__(message, raw_response, body)
        object.__setattr__(self, "data", data)

    @property
    def code(self) -> str:
        r"""Shortcut for ``data.error.code``."""
        return self.data.error.code

    @property
    def retryable(self) -> Optional[bool]:
        r"""Shortcut for ``data.error.retryable``."""
        return self.data.error.retryable

    @property
    def request_id(self) -> Optional[str]:
        r"""Shortcut for ``data.error.request_id``."""
        return self.data.error.request_id


def parse_extract_error(body: str) -> Optional[ExtractErrorData]:
    """``body`` parsed as an Extract error, or ``None`` when it is another shape."""
    try:
        return ExtractErrorData.model_validate_json(body)
    except ValueError:
        return None
