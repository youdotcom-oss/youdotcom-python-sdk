

from __future__ import annotations
from .knowledgeresult import KnowledgeResult, KnowledgeResultTypedDict
from .newsresult import NewsResult, NewsResultTypedDict
from .searchmetadata import SearchMetadata, SearchMetadataTypedDict
from .webresult import WebResult, WebResultTypedDict
from pydantic import model_serializer
from typing import List, Optional
from typing_extensions import NotRequired, TypedDict
from youdotcom.types import BaseModel, UNSET_SENTINEL


class ResultsTypedDict(TypedDict):
    web: NotRequired[List[WebResultTypedDict]]
    news: NotRequired[List[NewsResultTypedDict]]
    knowledge: NotRequired[List[KnowledgeResultTypedDict]]
    r"""Results backed by licensed data providers. Up to 25 are returned, limited to those relevant to the query. When none are relevant the key is omitted rather than returned as an empty array."""


class Results(BaseModel):
    web: Optional[List[WebResult]] = None

    news: Optional[List[NewsResult]] = None

    knowledge: Optional[List[KnowledgeResult]] = None
    r"""Results backed by licensed data providers. Up to 25 are returned, limited to those relevant to the query. When none are relevant the key is omitted rather than returned as an empty array."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["web", "news", "knowledge"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m


class SearchResponseTypedDict(TypedDict):
    r"""A JSON object containing unified search results from web, news, and knowledge sources"""

    results: NotRequired[ResultsTypedDict]
    metadata: NotRequired[SearchMetadataTypedDict]


class SearchResponse(BaseModel):
    r"""A JSON object containing unified search results from web, news, and knowledge sources"""

    results: Optional[Results] = None

    metadata: Optional[SearchMetadata] = None

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["results", "metadata"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m
