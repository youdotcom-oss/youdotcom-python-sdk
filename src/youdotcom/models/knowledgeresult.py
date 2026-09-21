

from __future__ import annotations
from .knowledgeattribution import KnowledgeAttribution, KnowledgeAttributionTypedDict
from pydantic import model_serializer
from typing import List, Optional
from typing_extensions import NotRequired, TypedDict
from youdotcom.types import BaseModel, UNSET_SENTINEL


class KnowledgeResultTypedDict(TypedDict):
    r"""A single knowledge result. `type` identifies the kind of result and determines which fields it populates. `type`, `title`, and `attribution` are required on every kind.

    For `type: answer`, the only kind currently returned, `description` is required and `as_of` is optional.
    """

    type: str
    r"""The kind of knowledge result retrieved. `answer` is the only value currently returned. Ignore a value you do not recognize rather than failing on it, since a new kind may populate a different set of fields."""
    title: str
    r"""The title of the knowledge result."""
    attribution: List[KnowledgeAttributionTypedDict]
    r"""Display credit for the data behind the result. These are credits rather than citations: each entry names a provider and carries no URL."""
    description: NotRequired[str]
    r"""Description of the knowledge result, drawn from proprietary licensed data. Required on `type: answer` results."""
    as_of: NotRequired[str]
    r"""The date the result's underlying data covers, as `YYYY-MM-DD`. Optional, and omitted when the provider reports no date."""


class KnowledgeResult(BaseModel):
    r"""A single knowledge result. `type` identifies the kind of result and determines which fields it populates. `type`, `title`, and `attribution` are required on every kind.

    For `type: answer`, the only kind currently returned, `description` is required and `as_of` is optional.
    """

    type: str
    r"""The kind of knowledge result retrieved. `answer` is the only value currently returned. Ignore a value you do not recognize rather than failing on it, since a new kind may populate a different set of fields."""

    title: str
    r"""The title of the knowledge result."""

    attribution: List[KnowledgeAttribution]
    r"""Display credit for the data behind the result. These are credits rather than citations: each entry names a provider and carries no URL."""

    description: Optional[str] = None
    r"""Description of the knowledge result, drawn from proprietary licensed data. Required on `type: answer` results."""

    as_of: Optional[str] = None
    r"""The date the result's underlying data covers, as `YYYY-MM-DD`. Optional, and omitted when the provider reports no date."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["description", "as_of"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m
