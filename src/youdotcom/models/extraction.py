"""The ``extraction`` parameter on ``POST /v1/search``.

``livecrawl`` is being replaced by an ``extraction`` object on Search:

    {
      "extraction_mode": "highlights" | "full_page",   # required
      "highlights":     {},                            # reserved for future fields
      "full_page":      { "extraction_formats": [...] }
    }

Top-level ``crawl_timeout`` (1-60, default 10) is sibling to ``extraction``
and is invalid alongside ``extraction_mode == "highlights"`` (the same
constraint is handled at the SDK layer by stripping ``crawl_timeout`` from
the request body, avoiding a round-trip 422).

``extraction.highlights`` is forward-compat: the dict shape stays stable
even when sub-fields are added. Today it carries no public configuration
knobs; unknown keys at this depth raise
:class:`pydantic.ValidationError` locally (see
:class:`_StrictExtractionBase`, ``extra="forbid"``).

Mirrors the locked ``extraction`` schema in the docs preview at
``youdotcom-docs/fern/apis/search/openapi_search_v1_overrides.yaml``.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import ConfigDict, Field, model_serializer, model_validator
from typing_extensions import NotRequired, TypedDict

from youdotcom.types import BaseModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExtractionMode(str, Enum):
    r"""The ``extraction_mode`` discriminator on the ``extraction`` object."""

    HIGHLIGHTS = "highlights"
    FULL_PAGE = "full_page"


class ExtractionFormat(str, Enum):
    r"""A format accepted by ``extraction.full_page.extraction_formats``."""

    HTML = "html"
    MARKDOWN = "markdown"


# ---------------------------------------------------------------------------
# TypedDicts (user-facing API surface)
# ---------------------------------------------------------------------------

# The SDK accepts plain strings anywhere enum-typed values are expected
# (normalized at the SDK layer), so the TypedDicts type the enums OR their
# string spellings rather than the enum alone.
ExtractionModeValue = Union[ExtractionMode, Literal["highlights", "full_page"]]
r"""``extraction_mode`` as typed for callers: the enum or its plain string."""

ExtractionFormatValue = Union[ExtractionFormat, Literal["html", "markdown"]]
r"""``extraction_format`` as typed for callers: the enum or its plain string."""


class ExtractionHighlightsTypedDict(TypedDict):
    r"""Type hint for the optional ``highlights`` sub-object.

    Reserved for future sub-fields. The dict shape is stable so callers
    can write ``extraction={"extraction_mode": "highlights"}`` without
    depending on a future sub-field appearing.
    """


class ExtractionFullPageTypedDict(TypedDict):
    r"""Type hint for the optional ``full_page`` sub-object."""

    extraction_formats: NotRequired[List[ExtractionFormatValue]]
    r"""Format(s) returned for each result. ``["markdown"]`` by default."""


class ExtractionTypedDict(TypedDict):
    r"""Type hint for the ``extraction`` object on ``POST /v1/search``."""

    extraction_mode: ExtractionModeValue
    r"""Required. ``"highlights"`` or ``"full_page"``."""

    highlights: NotRequired[ExtractionHighlightsTypedDict]
    r"""Optional. Valid only when ``extraction_mode == "highlights"``."""

    full_page: NotRequired[ExtractionFullPageTypedDict]
    r"""Optional. Valid only when ``extraction_mode == "full_page"``."""


# ---------------------------------------------------------------------------
# Base model with strict extra="forbid"
# ---------------------------------------------------------------------------


class _StrictExtractionBase(BaseModel):
    """Base for all ``extraction`` sub-models.

    ``extra="forbid"`` mirrors the server's strict ``extraction`` contract.
    Unknown keys anywhere inside ``extraction`` raise
    :class:`pydantic.ValidationError` locally so callers fail-fast instead
    of routing to a 422.

    The top-level ``SearchRequestBody`` keeps Pydantic's default
    ``extra="ignore"`` semantics; only ``extraction`` is strict.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        protected_namespaces=(),
        extra="forbid",
    )


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ExtractionHighlights(_StrictExtractionBase):
    r"""Configuration for ``extraction_mode == "highlights"``.

    Reserved for future sub-fields. Today the container has no public
    fields; ``extra="forbid"`` from :class:`_StrictExtractionBase` causes
    unknown keys (e.g. typos or unsupported knobs) to raise
    :class:`pydantic.ValidationError` locally rather than round-tripping
    to a 422.
    """


class ExtractionFullPage(_StrictExtractionBase):
    r"""Configuration for ``extraction_mode == "full_page"``."""

    extraction_formats: Optional[List[ExtractionFormat]] = None
    r"""Format(s) returned for each result. ``["markdown"]`` if unset.

    An empty list is preserved on the wire so callers that explicitly pass
    ``[]`` see that value round-trip; the API may reject that combination
    or apply its own default.
    """

    @model_serializer(mode="wrap")
    def _serialize(self, handler):  # type: ignore[no-untyped-def]
        serialized = handler(self)
        return {k: v for k, v in serialized.items() if v is not None}


class Extraction(_StrictExtractionBase):
    r"""The ``extraction`` object on ``POST /v1/search``.

    ``extraction_mode`` selects between returning query-relevant excerpts
    (``"highlights"`` -> ``results.web[].contents.highlights``) and full
    page content (``"full_page"`` -> ``results.web[].contents.html`` /
    ``contents.markdown``).

    Wrong-mode couplings and unknown keys raise
    :class:`pydantic.ValidationError` locally; the API would 422 for the
    same inputs. The forward-compat container (``ExtractionHighlights``)
    mirrors the locked server schema and has no public sub-fields today.
    """

    extraction_mode: ExtractionMode
    r"""Required. ``"highlights"`` or ``"full_page"``."""

    highlights: Optional[ExtractionHighlights] = None
    r"""Valid only when ``extraction_mode == "highlights"``."""

    full_page: Optional[ExtractionFullPage] = None
    r"""Valid only when ``extraction_mode == "full_page"``."""

    @model_validator(mode="after")
    def _check_mode_consistency(self) -> "Extraction":
        if self.extraction_mode is ExtractionMode.HIGHLIGHTS and self.full_page is not None:
            raise ValueError(
                "extraction.full_page must not be set when extraction_mode == 'highlights'"
            )
        if self.extraction_mode is ExtractionMode.FULL_PAGE and self.highlights is not None:
            raise ValueError(
                "extraction.highlights must not be set when extraction_mode == 'full_page'"
            )
        return self

    @model_serializer(mode="wrap")
    def _serialize(self, handler):  # type: ignore[no-untyped-def]
        """Drop ``None`` sub-objects so absent fields stay off the wire.

        Without this, calling ``Extraction(extraction_mode="full_page")``
        would emit ``{"extraction_mode": "full_page", "highlights": null,
        "full_page": null}`` on the wire.
        """
        serialized = handler(self)
        return {k: v for k, v in serialized.items() if v is not None}
