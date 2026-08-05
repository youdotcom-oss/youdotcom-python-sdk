"""Error model for HTTP 422 responses.

Handles three possible 422 body shapes returned across You.com endpoints:
  - ``{"error": "..."}`` — search spec format
  - ``{"detail": [{"type": "...", "loc": [...], "msg": "...", ...}]}`` — FastAPI
    request validation errors (returned before handler runs)
  - ``{"errors": [{"status": "422", "code": "...", "title": "...", ...}]}`` —
    JSON:API format (returned by controller-level error handlers)

All fields are optional so any shape deserializes without crashing. The raw
response is always preserved on the error object for callers that need the
full body.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import httpx
from typing import Any, List, Optional
from youdotcom.errors import YouError
from youdotcom.types import BaseModel


class UnprocessableEntityResponseErrorData(BaseModel):
    error: Optional[str] = None
    r"""Error code from the search spec 422 format."""

    detail: Optional[List[dict[str, Any]]] = None
    r"""Validation error array from FastAPI's RequestValidationError."""

    errors: Optional[List[dict[str, Any]]] = None
    r"""JSON:API error array from controller-level error handlers."""


@dataclass(unsafe_hash=True)
class UnprocessableEntityResponseError(YouError):
    r"""Unprocessable Entity. Invalid request parameter combination."""

    data: UnprocessableEntityResponseErrorData = field(hash=False)

    def __init__(
        self,
        data: UnprocessableEntityResponseErrorData,
        raw_response: httpx.Response,
        body: Optional[str] = None,
    ):
        message = body or raw_response.text
        super().__init__(message, raw_response, body)
        object.__setattr__(self, "data", data)
