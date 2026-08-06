from __future__ import annotations
from typing import List, Optional
from youdotcom.types import BaseModel


class AnswerSearchResult(BaseModel):
    r"""A web search result used during answer synthesis."""

    url: str
    r"""The URL of the source webpage."""

    title: str
    r"""The title of the source webpage."""

    snippets: Optional[List[str]] = None
    r"""Text snippets from the search result that preview its content."""

    page_age: Optional[str] = None
    r"""The publication date or age supplied by the search result."""
