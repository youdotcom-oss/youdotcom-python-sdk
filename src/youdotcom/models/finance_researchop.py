

from __future__ import annotations
from .financeresearcheffort import FinanceResearchEffort
from enum import Enum
from pydantic import model_serializer
from typing import Any, Dict, List, Optional, Union
from typing_extensions import NotRequired, TypeAliasType, TypedDict
from youdotcom.types import BaseModel, UNSET_SENTINEL


class FinanceResearchRequestTypedDict(TypedDict):
    input: str
    r"""The financial research question or complex query requiring in-depth investigation and multi-step reasoning.

    Note: The maximum length of the input is 40,000 characters.
    """
    research_effort: NotRequired[FinanceResearchEffort]
    r"""Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

    Available levels:
    - `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.
    - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result.
    """
    output_schema: NotRequired[Dict[str, Any]]
    r"""Beta. Requests structured JSON output in `output.content` using a supported JSON Schema subset. Supported with every `research_effort` value. The rules and limits match the Research API, so the same schema works on both endpoints.

    Limits are enforced before model execution. The request fails with `422` if any limit is exceeded:
    - Max nesting depth: 5. - Max total properties: 100. - Max total enum values: 500. - Max large-enum string budget (enums over 250 values): 7,500. - Max total schema string budget: 25,000. The schema string budget counts property names, `$defs` names, enum values, and `const` values.

    Schema rules:
    - Root must be a JSON object. Top-level `anyOf` is not allowed. - Every object must define `properties` and set `additionalProperties: false`. - Every property must be listed in `required`. To make a field optional, keep it in `required` and add `"null"` to its type, for example `["number", "null"]`. - Recursive schemas are not supported. - A property's type may not be a bare `{"type": "null"}`. Use a nullable array form such as `["number", "null"]`, or a `null` branch inside an `anyOf`.

    See [Structured Output](https://you.com/docs/guides/finance-research/structured-output) for full rules, supported patterns, the optional-via-nullable pattern, conditional structure, and examples.
    """


class FinanceResearchRequest(BaseModel):
    input: str
    r"""The financial research question or complex query requiring in-depth investigation and multi-step reasoning.

    Note: The maximum length of the input is 40,000 characters.
    """

    research_effort: Optional[FinanceResearchEffort] = FinanceResearchEffort.DEEP
    r"""Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.

    Available levels:
    - `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.
    - `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result.
    """

    output_schema: Optional[Dict[str, Any]] = None
    r"""Beta. Requests structured JSON output in `output.content` using a supported JSON Schema subset. Supported with every `research_effort` value. The rules and limits match the Research API, so the same schema works on both endpoints.

    Limits are enforced before model execution. The request fails with `422` if any limit is exceeded:
    - Max nesting depth: 5. - Max total properties: 100. - Max total enum values: 500. - Max large-enum string budget (enums over 250 values): 7,500. - Max total schema string budget: 25,000. The schema string budget counts property names, `$defs` names, enum values, and `const` values.

    Schema rules:
    - Root must be a JSON object. Top-level `anyOf` is not allowed. - Every object must define `properties` and set `additionalProperties: false`. - Every property must be listed in `required`. To make a field optional, keep it in `required` and add `"null"` to its type, for example `["number", "null"]`. - Recursive schemas are not supported. - A property's type may not be a bare `{"type": "null"}`. Use a nullable array form such as `["number", "null"]`, or a `null` branch inside an `anyOf`.

    See [Structured Output](https://you.com/docs/guides/finance-research/structured-output) for full rules, supported patterns, the optional-via-nullable pattern, conditional structure, and examples.
    """

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["research_effort", "output_schema"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m


FinanceResearchLocTypedDict = TypeAliasType(
    "FinanceResearchLocTypedDict", Union[str, int]
)


FinanceResearchLoc = TypeAliasType("FinanceResearchLoc", Union[str, int])


class FinanceResearchInputTypedDict(TypedDict):
    pass


class FinanceResearchInput(BaseModel):
    pass


FinanceResearchInputUnionTypedDict = TypeAliasType(
    "FinanceResearchInputUnionTypedDict", Union[FinanceResearchInputTypedDict, str]
)
r"""The input value that caused the error."""


FinanceResearchInputUnion = TypeAliasType(
    "FinanceResearchInputUnion", Union[FinanceResearchInput, str]
)
r"""The input value that caused the error."""


class FinanceResearchDetailTypedDict(TypedDict):
    type: str
    r"""The validation error type."""
    loc: List[FinanceResearchLocTypedDict]
    r"""The location of the error as a path of segments (strings for field names, integers for byte offsets)."""
    msg: str
    r"""A human-readable description of the error."""
    input: FinanceResearchInputUnionTypedDict
    r"""The input value that caused the error."""
    ctx: NotRequired[Dict[str, Any]]
    r"""Additional context about the error."""


class FinanceResearchDetail(BaseModel):
    type: str
    r"""The validation error type."""

    loc: List[FinanceResearchLoc]
    r"""The location of the error as a path of segments (strings for field names, integers for byte offsets)."""

    msg: str
    r"""A human-readable description of the error."""

    input: FinanceResearchInputUnion
    r"""The input value that caused the error."""

    ctx: Optional[Dict[str, Any]] = None
    r"""Additional context about the error."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["ctx"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m


class FinanceResearchContentType(str, Enum):
    r"""The format of the content field."""

    TEXT = "text"
    OBJECT = "object"


class FinanceResearchSourceTypedDict(TypedDict):
    url: str
    r"""The URL of the source webpage."""
    title: NotRequired[str]
    r"""The title of the source webpage."""
    snippets: NotRequired[List[str]]
    r"""Relevant excerpts from the source page that were used in generating the answer."""


class FinanceResearchSource(BaseModel):
    url: str
    r"""The URL of the source webpage."""

    title: Optional[str] = None
    r"""The title of the source webpage."""

    snippets: Optional[List[str]] = None
    r"""Relevant excerpts from the source page that were used in generating the answer."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(["title", "snippets"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))

            if val != UNSET_SENTINEL:
                if val is not None or k not in optional_fields:
                    m[k] = val

        return m


class FinanceResearchOutputTypedDict(TypedDict):
    r"""The research output containing the answer and sources."""

    content: Union[str, Dict[str, Any]]
    r"""The comprehensive finance-grade response with inline citations. By default, content is a Markdown string with numbered citations that reference the items in the sources array. When `output_schema` is provided, content is a JSON object that conforms to the requested schema."""
    content_type: FinanceResearchContentType
    r"""The format of the content field."""
    sources: List[FinanceResearchSourceTypedDict]
    r"""A list of web sources used to generate the answer."""


class FinanceResearchOutput(BaseModel):
    r"""The research output containing the answer and sources."""

    content: Union[str, Dict[str, Any]]
    r"""The comprehensive finance-grade response with inline citations. By default, content is a Markdown string with numbered citations that reference the items in the sources array. When `output_schema` is provided, content is a JSON object that conforms to the requested schema."""

    content_type: FinanceResearchContentType
    r"""The format of the content field."""

    sources: List[FinanceResearchSource]
    r"""A list of web sources used to generate the answer."""


class FinanceResearchResponseTypedDict(TypedDict):
    r"""A JSON object containing a comprehensive finance-grade answer with citations and supporting search results"""

    output: FinanceResearchOutputTypedDict
    r"""The research output containing the answer and sources."""
    warnings: NotRequired[List[str]]
    r"""Non-fatal warnings generated during the request, such as a deprecation notice for an `output_schema` that will stop being accepted in a future release. `None` when the response omits the key; an empty list when the key is present but no warnings occurred."""


class FinanceResearchResponse(BaseModel):
    r"""A JSON object containing a comprehensive finance-grade answer with citations and supporting search results"""

    output: FinanceResearchOutput
    r"""The research output containing the answer and sources."""

    warnings: Optional[List[str]] = None
    r"""Non-fatal warnings generated during the request, such as a deprecation notice for an `output_schema` that will stop being accepted in a future release. `None` when the response omits the key; an empty list when the key is present but no warnings occurred."""
