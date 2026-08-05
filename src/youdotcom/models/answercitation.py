from __future__ import annotations
from typing import List, Optional
from youdotcom.types import BaseModel


class AnswerCitation(BaseModel):
    r"""A source cited in the answer, with supporting excerpts."""

    source: str
    r"""The URL of the cited source."""

    excerpts: Optional[List[str]] = None
    r"""Verbatim excerpts from the cited source that support the answer."""
