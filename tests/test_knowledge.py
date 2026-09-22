"""Tests for the ``knowledge`` parameter and knowledge results on ``you.search``.

Locks the contract for the Knowledge launch (``POST /v1/search``):

- ``knowledge`` is a new enum-typed request parameter. ``"core"`` is the only
  value the API accepts; anything else is rejected server-side with ``422``.
- The parameter is normalized to lowercase like the other enum-typed search
  parameters, and is omitted from the request body when not supplied.
- ``results.knowledge`` is a list of ``KnowledgeResult``. ``type``, ``title``,
  and ``attribution`` are always present; ``description`` and ``as_of`` are
  optional. ``source_description`` inside an attribution entry is optional.
- The ``results.knowledge`` key is omitted entirely when no knowledge results
  are relevant, so the parsed attribute is ``None`` rather than ``[]``.
- ``KnowledgeResult.type`` is modeled as a plain string: an unrecognized value
  parses instead of raising, since a new kind may arrive later.
"""

import json
from contextlib import contextmanager

import httpx
import pytest
from pydantic import ValidationError

from youdotcom import You, models
from youdotcom.models import Knowledge, KnowledgeAttribution, KnowledgeResult


@contextmanager
def _capture(response_body: dict):
    """Yield ``(You, captured)`` over a mock transport returning ``response_body``."""
    captured: dict = {}

    def handler(request):
        captured["body"] = json.loads(request.content)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=json.dumps(response_body),
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    try:
        with You(api_key_auth="k", server_url="http://mock.local", client=client) as you:
            yield you, captured
    finally:
        client.close()


_EMPTY = {"results": {"web": []}, "metadata": {"query": "q"}}


def _search_body(**kwargs) -> dict:
    """Run one synchronous search; return the JSON body that went over the wire."""
    with _capture(_EMPTY) as (you, captured):
        you.search(query="q", **kwargs)
    return captured["body"]


def _parse(results: dict) -> models.SearchResponse:
    """Parse a ``results`` mapping through the response model."""
    return models.SearchResponse.model_validate(
        {"results": results, "metadata": {"query": "q"}}
    )


# A knowledge result shaped like what prod returns today.
_ANSWER = {
    "type": "answer",
    "title": "Paris is the capital of France",
    "description": "Paris has been the capital of France since the 10th century.",
    "as_of": "2026-09-01",
    "attribution": [
        {
            "name": "Encyclopedia Britannica",
            "source_description": "General knowledge",
        }
    ],
}


# ---------------------------------------------------------------------------
# Enum contract
# ---------------------------------------------------------------------------


class TestKnowledgeEnum:
    def test_core_member(self):
        assert Knowledge.CORE.value == "core"

    def test_core_is_the_only_member(self):
        """``core`` is the only value the published spec defines. Adding a member
        the API does not accept would let callers send a value that fails with
        ``422``, so this pins the enum to exactly what is public."""
        assert [m.value for m in Knowledge] == ["core"]


# ---------------------------------------------------------------------------
# Request wiring
# ---------------------------------------------------------------------------


class TestKnowledgeRequest:
    def test_knowledge_lands_on_wire(self):
        assert _search_body(knowledge="core")["knowledge"] == "core"

    def test_knowledge_lowercased(self):
        assert _search_body(knowledge="CORE")["knowledge"] == "core"

    def test_knowledge_accepts_enum_instance(self):
        assert _search_body(knowledge=Knowledge.CORE)["knowledge"] == "core"

    def test_knowledge_omitted_by_default(self):
        assert "knowledge" not in _search_body()

    def test_knowledge_does_not_disturb_neighbours(self):
        body = _search_body(knowledge="core", count=5, safesearch="off")
        assert body["knowledge"] == "core"
        assert body["count"] == 5
        assert body["safesearch"] == "off"

    def test_request_body_model_serializes_enum(self):
        body = models.SearchRequestBody(query="q", knowledge=Knowledge.CORE)
        assert body.model_dump(mode="json")["knowledge"] == "core"

    def test_invalid_value_raises_locally(self):
        """``knowledge`` is enum-typed on the request body, so a value the API
        would reject with ``422`` raises ``ValidationError`` before any
        request is sent -- the same local-mirrors-server pattern as
        ``extraction``."""
        with pytest.raises(ValidationError):
            _search_body(knowledge="not-a-real-value")


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------


class TestKnowledgeResponse:
    def test_parses_full_answer(self):
        resp = _parse({"knowledge": [_ANSWER]})
        assert resp.results.knowledge is not None
        kr = resp.results.knowledge[0]
        assert kr.type == "answer"
        assert kr.title == "Paris is the capital of France"
        assert kr.description.startswith("Paris has been")
        assert kr.as_of == "2026-09-01"
        assert kr.attribution[0].name == "Encyclopedia Britannica"
        assert kr.attribution[0].source_description == "General knowledge"

    def test_optional_fields_default_to_none(self):
        kr = KnowledgeResult.model_validate(
            {"type": "answer", "title": "t", "attribution": [{"name": "n"}]}
        )
        assert kr.description is None
        assert kr.as_of is None
        assert kr.attribution[0].source_description is None

    def test_optional_fields_omitted_on_round_trip(self):
        """Absent optionals stay absent rather than serializing as null."""
        kr = KnowledgeResult.model_validate(
            {"type": "answer", "title": "t", "description": "d", "attribution": [{"name": "n"}]}
        )
        dumped = kr.model_dump(mode="json")
        assert dumped == {
            "type": "answer",
            "title": "t",
            "attribution": [{"name": "n"}],
            "description": "d",
        }

    def test_attribution_omits_absent_source_description(self):
        dumped = KnowledgeAttribution(name="n").model_dump(mode="json")
        assert dumped == {"name": "n"}

    def test_unknown_type_parses(self):
        """Forward compat: the spec says to ignore an unrecognized ``type``
        rather than fail, since a new kind may populate different fields."""
        kr = KnowledgeResult.model_validate(
            {"type": "some_future_kind", "title": "t", "attribution": [{"name": "n"}]}
        )
        assert kr.type == "some_future_kind"

    def test_missing_knowledge_key_is_none(self):
        """Prod omits ``results.knowledge`` when nothing is relevant."""
        assert _parse({"web": []}).results.knowledge is None

    def test_multiple_results_preserved(self):
        resp = _parse({"knowledge": [_ANSWER, {**_ANSWER, "title": "second"}]})
        assert [r.title for r in resp.results.knowledge] == [
            "Paris is the capital of France",
            "second",
        ]

    def test_knowledge_alongside_news(self):
        resp = _parse({"knowledge": [_ANSWER], "news": []})
        assert resp.results.knowledge is not None
        assert resp.results.news == []


# ---------------------------------------------------------------------------
# End to end through the SDK
# ---------------------------------------------------------------------------


class TestKnowledgeEndToEnd:
    def test_search_returns_parsed_knowledge(self):
        with _capture({"results": {"knowledge": [_ANSWER]}}) as (you, captured):
            resp = you.search(query="what is the capital of France", knowledge="core")
        assert captured["body"]["knowledge"] == "core"
        assert resp.results.knowledge[0].title == "Paris is the capital of France"


# ---------------------------------------------------------------------------
# Async + deprecated-spelling parity
# ---------------------------------------------------------------------------


class TestKnowledgeParity:
    @pytest.mark.asyncio
    async def test_search_async_sends_knowledge(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps({"results": {"knowledge": [_ANSWER]}}),
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as ac:
            async with You(
                api_key_auth="k", server_url="http://mock.local", async_client=ac
            ) as you:
                resp = await you.search_async(query="q", knowledge="core")

        assert captured["body"]["knowledge"] == "core"
        assert resp.results.knowledge[0].type == "answer"

    def test_deprecated_unified_passes_knowledge(self):
        with _capture(_EMPTY) as (you, captured):
            with pytest.warns(DeprecationWarning):
                you.search.unified(query="q", knowledge="core")
        assert captured["body"]["knowledge"] == "core"

    @pytest.mark.asyncio
    async def test_deprecated_unified_async_passes_knowledge(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200,
                headers={"content-type": "application/json"},
                content=json.dumps(_EMPTY),
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as ac:
            async with You(
                api_key_auth="k", server_url="http://mock.local", async_client=ac
            ) as you:
                with pytest.warns(DeprecationWarning):
                    await you.search.unified_async(query="q", knowledge="core")

        assert captured["body"]["knowledge"] == "core"
