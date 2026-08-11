"""The ``extraction`` parameter on ``POST /v1/search``.

Abi is replacing ``livecrawl`` with an ``extraction`` object on Search:

    {
      "extraction_mode": "highlights" | "full_page",   # required
      "highlights":     { "max_tokens": int },         # 512-8192
      "full_page":      { "extraction_formats": [...] }
    }

Top-level ``crawl_timeout`` (1-60, default 10) is sibling to ``extraction``
and is invalid alongside ``extraction_mode == "highlights"`` (verified from
the upstream ``youdotcom-index`` server code; the same constraint is
replicated at the SDK layer so callers fail-fast rather than round-tripping
a 422).

Mirrors the locked ``extraction`` schema in the docs preview at
``youdotcom-docs/fern/apis/search/openapi_search_v1_overrides.yaml``.
"""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

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


class ExtractionHighlightsTypedDict(TypedDict):
    r"""Type hint for the optional ``highlights`` sub-object."""

    max_tokens: NotRequired[int]
    r"""Maximum tokens returned per result. 512-8192. Default: API default (4096)."""


class ExtractionFullPageTypedDict(TypedDict):
    r"""Type hint for the optional ``full_page`` sub-object."""

    extraction_formats: NotRequired[List[ExtractionFormat]]
    r"""Format(s) returned for each result. ``["markdown"]`` by default."""


class ExtractionTypedDict(TypedDict):
    r"""Type hint for the ``extraction`` object on ``POST /v1/search``."""

    extraction_mode: ExtractionMode
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

    ``extra="forbid"`` matches the upstream ``youdotcom-index``
    ``SearchHighlightsConfig`` / nested ``extraction`` models (verified in
    ``youdotcom_index_api/search/schemas.py``). Unknown keys anywhere inside
    ``extraction`` raise :class:`pydantic.ValidationError` locally so
    callers fail-fast instead of routing to a 422.

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
    r"""Configuration for ``extraction_mode == "highlights"``."""

    max_tokens: Optional[int] = Field(default=None, ge=512, le=8192)
    r"""Maximum tokens returned per result. 512-8192.

    ``None`` falls back to the API default (4096). Setting a value outside
    [512, 8192] raises :class:`pydantic.ValidationError` to mirror the
    server's ``SearchHighlightsConfig.max_tokens`` constraint (verified from
    ``youdotcom_index_api/services/highlights/schemas.py``: ``ge=512``,
    ``le=8192``).
    """

    @model_serializer(mode="wrap")
    def _serialize(self, handler):  # type: ignore[no-untyped-def]
        """Drop ``None`` values so omitted fields stay off the wire.

        Mirrors :meth:`SearchRequestBody.serialize_model`. Without this,
        Pydantic's default dump would emit ``{"max_tokens": null}`` even
        when the caller did not pass the field.
        """
        serialized = handler(self)
        return {k: v for k, v in serialized.items() if v is not None}


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
    ``contents.markdown``). Wrong-mode couplings, unknown keys, and out-of
    range ``max_tokens`` raise :class:`pydantic.ValidationError` locally;
    the API would 422 for the same inputs.
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
