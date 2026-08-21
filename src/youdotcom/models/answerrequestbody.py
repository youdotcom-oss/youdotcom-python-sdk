from __future__ import annotations
from .country import Country
from .freshnessvalue import FreshnessValue
from .language import Language
from .safesearch import SafeSearch
from pydantic import model_serializer
from typing import List, Optional
from youdotcom.types import BaseModel, UNSET_SENTINEL


class AnswerRequestBody(BaseModel):
    r"""Request body for ``POST /v1/answer``."""

    query: str
    r"""The search query used to retrieve relevant web results. Max 400 characters. Search operators (``site:``, ``OR``, etc.) are not supported."""

    freshness: Optional[FreshnessValue] = None
    r"""Specifies the freshness of the results. One of ``day``, ``week``, ``month``, ``year``, or ``YYYY-MM-DDtoYYYY-MM-DD``."""

    country: Optional[Country] = None
    r"""A supported country code that determines the geographical focus of the web results."""

    language: Optional[Language] = None
    r"""A supported BCP 47 language tag that determines the language of the web results."""

    safesearch: Optional[SafeSearch] = None
    r"""Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not."""

    include_domains: Optional[List[str]] = None
    r"""Domains to exclusively include. Cannot combine with ``exclude_domains`` or ``boost_domains``. Max 500."""

    exclude_domains: Optional[List[str]] = None
    r"""Domains to exclude. Cannot combine with ``include_domains``. Can combine with ``boost_domains``. Max 500."""

    boost_domains: Optional[List[str]] = None
    r"""Domains to prefer in ranking. Cannot combine with ``include_domains``. Can combine with ``exclude_domains``. Max 500."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(
            ["freshness", "country", "language", "safesearch", "include_domains", "exclude_domains", "boost_domains"]
        )
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m
