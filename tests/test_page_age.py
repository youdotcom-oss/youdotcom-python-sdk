"""Tolerance of non-ISO ``page_age`` values on search and news results (DX-815).

The spec types ``page_age`` as ``format: date-time``, but a US-locale
timestamp (``7/29/2024 10:38:56 AM``) was observed in production. Pydantic rejected it,
failing the *entire* response over one best-effort metadata field.

``page_age`` is now ``Union[datetime, str, None]``: ISO parses to a
``datetime``, anything else is handed back verbatim. Nothing is parsed
speculatively, so no value is dropped and no ambiguous date is guessed at.

Both models use the same ``LenientDateTime`` annotation, so the input space is
covered once against ``WebResult``; ``test_news_results_are_covered`` proves
the second model carries it too.
"""

import json
import warnings
from datetime import datetime, timezone

import httpx
import pytest
from pydantic import ValidationError

from youdotcom import You
from youdotcom.models import Extraction, ExtractionMode, SearchResponse
from youdotcom.models.webresult import WebResult


class TestISOValuesStillParse:
    """Pydantic's default smart union matches an ISO string as ``str``.

    ``union_mode="left_to_right"`` is what makes the ``datetime`` branch win.
    Reversing the union members would silently turn every timestamp into a
    string, so this is the guard on that ordering.
    """

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2025-06-25T11:41:00", datetime(2025, 6, 25, 11, 41)),
            ("2024-07-29", datetime(2024, 7, 29, 0, 0)),
        ],
        ids=["iso-datetime", "iso-date-only"],
    )
    def test_iso_values_become_datetimes(self, raw, expected):
        assert WebResult(page_age=raw).page_age == expected


class TestNonISOValuesAreReturnedVerbatim:
    """The fix: hand back exactly what the API sent, whatever shape it is."""

    @pytest.mark.parametrize(
        "raw",
        [
            # The value from the original report.
            "7/29/2024 10:38:56 AM",
            # A shape a parser tuned to the reported one would have dropped.
            "Mon, 29 Jul 2024 10:38:56 GMT",
            # Not a timestamp at all, but still what the API sent.
            "",
        ],
    )
    def test_unparseable_values_survive_as_strings(self, raw):
        assert WebResult(page_age=raw).page_age == raw


class TestWrongJSONTypesStillRaise:
    """A change to the field's shape must stay loud, not silently pass through."""

    @pytest.mark.parametrize("raw", [{"age": 1}, [], True], ids=["dict", "list", "bool"])
    def test_structural_type_raises(self, raw):
        with pytest.raises(ValidationError):
            WebResult(page_age=raw)

    @pytest.mark.parametrize("raw", [1721000000, "1721000000"], ids=["int", "numeric-str"])
    def test_numbers_are_read_as_epochs_not_returned_verbatim(self, raw):
        # Documented so the "any other string is returned verbatim" wording is
        # not read as covering numeric strings: pydantic coerces these to a
        # datetime, and did so before this field widened.
        assert WebResult(page_age=raw).page_age == datetime(
            2024, 7, 14, 23, 33, 20, tzinfo=timezone.utc
        )


class TestSerialization:
    """Regression guard on the union serializer, which fails soft.

    Pydantic serializes a union member it cannot match by falling back to
    ``str(value)`` with a ``UserWarning`` rather than raising — verified. So a
    future change to union-member selection could start emitting
    ``"datetime.datetime(2025, 6, 25, 11, 41)"`` in place of an ISO string with
    every other test still green. This is the only thing that would catch it.
    """

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2025-06-25T11:41:00", "2025-06-25T11:41:00"),
            ("7/29/2024 10:38:56 AM", "7/29/2024 10:38:56 AM"),
        ],
        ids=["datetime-branch", "str-branch"],
    )
    def test_both_branches_round_trip(self, raw, expected):
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # a soft serializer failure must fail the test
            dumped = json.loads(WebResult(page_age=raw).model_dump_json())
        assert dumped["page_age"] == expected


class TestSearchResponseWithNonISOPageAge:
    """The reported failure, reproduced at the transport boundary.

    Before this change the body below raised ``ResponseValidationError`` and the
    caller got nothing — not even the results whose timestamps were fine.
    """

    _BODY = json.dumps(
        {
            "results": {
                "web": [
                    {"url": "https://example.com/a", "page_age": "7/29/2024 10:38:56 AM"},
                    {"url": "https://example.com/b", "page_age": "2025-06-25T11:41:00"},
                    {"url": "https://example.com/c", "page_age": ""},
                    {"url": "https://example.com/d"},
                ],
                "news": [
                    {
                        "url": "https://example.com/news",
                        "title": "News with US-locale timestamp",
                        "page_age": "7/29/2024 10:38:56 AM",
                    }
                ],
            },
            "metadata": {"q": "test", "latency": 0.1},
        }
    )

    @pytest.fixture
    def results(self):
        def handler(request):
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=self._BODY
            )

        sdk_client = httpx.Client(transport=httpx.MockTransport(handler))
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        try:
            res = you.search(query="test")
            assert isinstance(res, SearchResponse)
            assert res.results is not None
            yield res.results
        finally:
            sdk_client.close()

    def test_every_page_age_lands_as_expected(self, results):
        assert results.web is not None and len(results.web) == 4
        assert results.web[0].page_age == "7/29/2024 10:38:56 AM"
        assert results.web[1].page_age == datetime(2025, 6, 25, 11, 41)
        assert results.web[2].page_age == ""
        assert results.web[3].page_age is None

    def test_news_results_are_covered(self, results):
        # The only thing the second model can prove: that it is wired up.
        assert results.news is not None and len(results.news) == 1
        assert results.news[0].page_age == "7/29/2024 10:38:56 AM"

class TestHighlightsResponseShape:
    """`page_age` on a highlights response.

    A highlights response has a different shape — snippets omitted,
    `contents.highlights` present — so the field is worth pinning on it rather
    than assuming the plain-search coverage carries over.
    """

    _BODY = json.dumps(
        {
            "results": {
                "web": [
                    {
                        "url": "https://example.com/a",
                        "title": "Normalized upstream",
                        "page_age": "2025-06-25T11:41:00",
                        "contents": {"highlights": ["first excerpt", "second excerpt"]},
                    },
                    {
                        "url": "https://example.com/b",
                        "title": "Not normalized",
                        "page_age": "7/29/2024 10:38:56 AM",
                        "contents": {"highlights": ["excerpt"]},
                    },
                ]
            },
            "metadata": {"q": "test", "latency": 0.1},
        }
    )

    def test_page_age_parses_on_a_highlights_response(self):
        captured: dict = {}

        def handler(request):
            captured["body"] = json.loads(request.content)
            return httpx.Response(
                200, headers={"content-type": "application/json"}, content=self._BODY
            )

        sdk_client = httpx.Client(transport=httpx.MockTransport(handler))
        you = You(server_url="http://mock.local", client=sdk_client, api_key_auth="test")
        try:
            res = you.search(
                query="test",
                extraction=Extraction(extraction_mode=ExtractionMode.HIGHLIGHTS),
            )
        finally:
            sdk_client.close()

        # The request really did ask for highlights, so this exercises that mode.
        assert captured["body"]["extraction"]["extraction_mode"] == "highlights"

        web = res.results.web
        assert web is not None and len(web) == 2
        assert web[0].contents is not None
        assert web[0].contents.highlights == ["first excerpt", "second excerpt"]
        # Snippets are omitted in this mode; page_age still resolves both ways.
        assert web[0].snippets is None
        assert web[0].page_age == datetime(2025, 6, 25, 11, 41)
        assert web[1].page_age == "7/29/2024 10:38:56 AM"
