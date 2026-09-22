from __future__ import annotations
from typing import List, Optional
from youdotcom.types import BaseModel


class AnswerSearchResult(BaseModel):
    r"""A web search result used during answer synthesis."""

    url: str
    r"""The URL of the source webpage."""

    title: str
    r"""The title of the source webpage."""

    description: Optional[str] = None
    r"""A brief description of the content of the search result."""

    snippets: Optional[List[str]] = None
    r"""Text snippets from the search result that preview its content."""

    thumbnail_url: Optional[str] = None
    r"""URL of the thumbnail."""

    page_age: Optional[str] = None
    r"""The publication date or age supplied by the search result."""
