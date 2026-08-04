from __future__ import annotations
from dataclasses import dataclass, field
import httpx
from typing import Optional
from youdotcom.errors import YouError
from youdotcom.types import BaseModel


class PaymentRequiredResponseErrorData(BaseModel):
    r"""Body of a 402 ``UpgradeRequiredResponse`` — returned when the account
    cannot make paid API requests (free-tier limit exceeded, insufficient credits).
    """
    error: Optional[str] = None
    r"""The error code (e.g. ``"payment_required"``)."""
    message: Optional[str] = None
    r"""A human-readable description of the error."""
    upgrade_url: Optional[str] = None
    r"""URL for adding credits or upgrading the account."""
    limit: Optional[int] = None
    r"""The usage limit, when available."""
    used: Optional[int] = None
    r"""The usage consumed, when available."""
    period: Optional[str] = None
    r"""The usage period, when available."""
    reset_at: Optional[str] = None
    r"""The reset timestamp, when available."""


@dataclass(unsafe_hash=True)
class PaymentRequiredResponseError(YouError):
    r"""Payment Required (402). The account cannot make paid API requests."""

    data: PaymentRequiredResponseErrorData = field(hash=False)

    def __init__(
        self,
        data: PaymentRequiredResponseErrorData,
        raw_response: httpx.Response,
        body: Optional[str] = None,
    ):
        message = body or raw_response.text
        super().__init__(message, raw_response, body)
        object.__setattr__(self, "data", data)
