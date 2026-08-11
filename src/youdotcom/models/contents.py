

from __future__ import annotations
from typing import List, Optional
from typing_extensions import NotRequired, TypedDict
from pydantic import Field, model_serializer
from youdotcom.types import BaseModel, UNSET_SENTINEL


class ContentsTypedDict(TypedDict):
    r"""Contents of the page if ``extraction`` was enabled (formerly ``livecrawl``)."""

    html: NotRequired[str]
    r"""The HTML content of the page."""
    markdown: NotRequired[str]
    r"""The Markdown content of the page."""
    highlights: NotRequired[List[str]]
    r"""Query-relevant excerpts extracted by the highlights mode."""


class Contents(BaseModel):
    r"""Contents of the page if ``extraction`` was enabled (formerly ``livecrawl``)."""

    html: Optional[str] = None
    r"""The HTML content of the page."""

    markdown: Optional[str] = None
    r"""The Markdown content of the page."""

    highlights: Optional[List[str]] = Field(default=None, description="Query-relevant excerpts extracted by the highlights mode.")

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["html", "markdown", "highlights"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m
