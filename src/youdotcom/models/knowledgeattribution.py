

from __future__ import annotations
from pydantic import model_serializer
from typing import Optional
from typing_extensions import NotRequired, TypedDict
from youdotcom.types import BaseModel, UNSET_SENTINEL


class KnowledgeAttributionTypedDict(TypedDict):
    name: str
    r"""Data provider for the knowledge result."""
    source_description: NotRequired[str]
    r"""Description of the provider."""


class KnowledgeAttribution(BaseModel):
    name: str
    r"""Data provider for the knowledge result."""

    source_description: Optional[str] = None
    r"""Description of the provider."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["source_description"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m
