"""The ``POST /v1/extract`` request and response.

Extract returns one web page or PDF, by URL, as clean Markdown and/or HTML:

    {
      "url":               "https://...",                # required
      "full_page":         { "extraction_formats": [...] },  # ExtractionFullPage
      "extraction_source": "blend" | "cache" | "fetch",
      "timeout":           2-100,                         # seconds, end to end
      "parse_effort":      "lite" | "standard"            # PDFs only
    }

The response is a single object, ``{}`` when nothing was extracted.

The request side is strict: unknown keys raise
:class:`pydantic.ValidationError` locally, as the API rejects them with a 422.
The response side ignores unknown keys, so fields the API adds later never
break parsing.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional, Union

from pydantic import Field
from typing_extensions import NotRequired, TypedDict

from youdotcom.models.extraction import (
    _StrictExtractionBase,
    ExtractionFullPage,
    ExtractionFullPageTypedDict,
    ExtractionSource,
    ExtractionSourceValue,
)
from youdotcom.types import BaseModel


EXTRACT_OP_SERVERS = [
    "https://ydc-index.io",
]


class ParseEffort(str, Enum):
    r"""How much effort to spend parsing PDF pages."""

    LITE = "lite"
    STANDARD = "standard"


ParseEffortValue = Union[ParseEffort, Literal["lite", "standard"]]
r"""``parse_effort`` as typed for callers: the enum or its plain string."""


# ---------------------------------------------------------------------------
# Request
# ---------------------------------------------------------------------------


class ExtractRequestTypedDict(TypedDict):
    r"""The ``POST /v1/extract`` request body."""

    url: str
    r"""The URL to extract content from."""
    full_page: NotRequired[ExtractionFullPageTypedDict]
    r"""Options for the returned page content. Omit to return the page as Markdown."""
    extraction_source: NotRequired[ExtractionSourceValue]
    r"""Where content comes from: ``"blend"`` (the default) serves cached content when it is available and crawls the page live when it is not, ``"cache"`` returns cached content only, and ``"fetch"`` always crawls the page live."""
    timeout: NotRequired[int]
    r"""Seconds the request may take end to end, including the cache lookup and the crawl. Must be between 2 and 100. Default is 30. Past it the request fails with a ``timeout`` error."""
    parse_effort: NotRequired[ParseEffortValue]
    r"""How much effort to spend parsing PDF pages; no effect on web pages. ``"lite"`` extracts the content embedded in each page and suits digitally created PDFs. ``"standard"`` (the default) also sends complex pages, such as charts and images, through an advanced model, and is billed per PDF page."""


class ExtractRequest(_StrictExtractionBase):
    r"""The ``POST /v1/extract`` request body.

    Unknown keys raise locally, as the API 422s. Unset fields stay off the wire
    (the request serializer drops ``None``), so the API applies its own defaults.
    """

    url: str
    r"""The URL to extract content from."""

    full_page: Optional[ExtractionFullPage] = None
    r"""Options for the returned page content. Omit to return the page as Markdown."""

    extraction_source: Optional[ExtractionSource] = None
    r"""Where content comes from: ``"blend"`` (the default) serves cached content when it is available and crawls the page live when it is not, ``"cache"`` returns cached content only, and ``"fetch"`` always crawls the page live."""

    timeout: Optional[int] = Field(default=None, ge=2, le=100)
    r"""Seconds the request may take end to end, including the cache lookup and the crawl. Must be between 2 and 100. Default is 30. Past it the request fails with a ``timeout`` error."""

    parse_effort: Optional[ParseEffort] = None
    r"""How much effort to spend parsing PDF pages; no effect on web pages. ``"lite"`` extracts the content embedded in each page and suits digitally created PDFs. ``"standard"`` (the default) also sends complex pages, such as charts and images, through an advanced model, and is billed per PDF page."""


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class ExtractFullPageContentsTypedDict(TypedDict):
    r"""The page content in each format requested in ``full_page.extraction_formats``."""

    markdown: NotRequired[str]
    r"""The Markdown content of the page."""
    html: NotRequired[str]
    r"""The HTML content of the page."""


class ExtractFullPageContents(BaseModel):
    r"""The page content in each format requested in ``full_page.extraction_formats``."""

    markdown: Optional[str] = None
    r"""The Markdown content of the page."""

    html: Optional[str] = None
    r"""The HTML content of the page."""


class ExtractContentsTypedDict(TypedDict):
    r"""The extracted content from the URL."""

    full_page: NotRequired[ExtractFullPageContentsTypedDict]
    r"""The page content in each format requested in ``full_page.extraction_formats``."""


class ExtractContents(BaseModel):
    r"""The extracted content from the URL."""

    full_page: Optional[ExtractFullPageContents] = None
    r"""The page content in each format requested in ``full_page.extraction_formats``."""


class ExtractMetadataTypedDict(TypedDict):
    r"""Metadata about the web page."""

    site_name: NotRequired[Optional[str]]
    r"""The OpenGraph site name of the web page."""
    favicon_url: NotRequired[str]
    r"""The URL of the favicon of the web page's domain."""


class ExtractMetadata(BaseModel):
    r"""Metadata about the web page."""

    site_name: Optional[str] = None
    r"""The OpenGraph site name of the web page."""

    favicon_url: Optional[str] = None
    r"""The URL of the favicon of the web page's domain."""


class ExtractResponseTypedDict(TypedDict):
    r"""The extracted page. Every field is absent when nothing was extracted."""

    url: NotRequired[str]
    r"""The URL whose content was extracted."""
    extraction_source: NotRequired[str]
    r"""Where the request allowed content to come from: ``"blend"``, ``"cache"``, or ``"fetch"``."""
    title: NotRequired[str]
    r"""The title of the web page."""
    contents: NotRequired[ExtractContentsTypedDict]
    r"""The extracted content from the URL."""
    metadata: NotRequired[ExtractMetadataTypedDict]
    r"""Metadata about the web page."""


class ExtractResponse(BaseModel):
    r"""The extracted page. Every field is ``None`` when nothing was extracted."""

    url: Optional[str] = None
    r"""The URL whose content was extracted."""

    extraction_source: Optional[str] = None
    r"""Where the request allowed content to come from: ``"blend"``, ``"cache"``, or ``"fetch"``."""

    title: Optional[str] = None
    r"""The title of the web page."""

    contents: Optional[ExtractContents] = None
    r"""The extracted content from the URL."""

    metadata: Optional[ExtractMetadata] = None
    r"""Metadata about the web page."""
