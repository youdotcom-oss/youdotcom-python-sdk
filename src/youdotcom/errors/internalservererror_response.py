"""Error model for HTTP 500 responses.

Handles two possible 500 body shapes:
  - ``{"detail": "..."}`` — plain detail string
  - ``{"errors": [{"status": "500", "code": "...", "title": "...", ...}]}`` —
    JSON:API format (returned by controller-level error handlers)

Both fields are optional so either shape deserializes without crashing.
"""

from __future__ import annotations
from dataclasses import dataclass, field
import httpx
from typing import Any, List, Optional
from youdotcom.errors import YouError
from youdotcom.types import BaseModel


class InternalServerErrorResponseData(BaseModel):
    detail: Optional[str] = None
    r"""A description of the error."""

    errors: Optional[List[dict[str, Any]]] = None
    r"""JSON:API error array from controller-level error handlers."""


@dataclass(unsafe_hash=True)
class InternalServerErrorResponse(YouError):
    r"""Internal Server Error during authentication/authorization middleware."""

    data: InternalServerErrorResponseData = field(hash=False)

    def __init__(
        self,
        data: InternalServerErrorResponseData,
        raw_response: httpx.Response,
        body: Optional[str] = None,
    ):
        message = body or raw_response.text
        super().__init__(message, raw_response, body)
        object.__setattr__(self, "data", data)
