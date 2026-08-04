from __future__ import annotations
from .answercitation import AnswerCitation
from .answersearchresult import AnswerSearchResult
from typing import List, Optional
from youdotcom.types import BaseModel


class AnswerResults(BaseModel):
    r"""Search results grouped by result type."""

    web: List[AnswerSearchResult] = []
    r"""All web search results considered during answer synthesis."""


class AnswerResponse(BaseModel):
    r"""A synthesized answer with citations and supporting search results."""

    answer: str
    r"""The synthesized response with numbered inline citations that reference items in the ``citations`` array."""

    citations: List[AnswerCitation] = []
    r"""The sources cited in the answer, in citation order."""

    results: AnswerResults = AnswerResults()
    r"""Search results grouped by result type."""
