"""Tests for ``ResearchTaskStreamEvent`` model-level contracts.

The SSE ``event`` discriminator must accept any string the server
emits, including names the SDK does not enumerate. ``Event`` uses
:class:`OpenEnumMeta` so unknown values unmarshal as plain strings
without serialization warnings.

The regression scenario: the server introduces a new SSE event name
(e.g. ``retry``, ``checkpoint``) and the SDK stops raising
``ResponseValidationError`` on the unmarshal path. This test suite pins
both halves of the contract:

- Known event names still resolve to :class:`Event` enum members.
- Unknown event names resolve to plain ``str`` values that compare
  equal to their raw string.
- Serialization (``model_dump``) produces no warnings for unknown
  events (the ``OpenEnumMeta`` switch fixes the prior
  ``PydanticSerializationUnexpectedValue`` warnings).
"""

from __future__ import annotations

import warnings
from typing import get_args, get_type_hints

import httpx
import pytest

from youdotcom import You
from youdotcom.models.researchtaskstreamevent import (
    Event,
    EventName,
    ResearchTaskStreamEvent,
    ResearchTaskStreamEventTypedDict,
)


_EVENT_DATA = {"type": "delta", "task_id": "t-1", "status": "running"}


class TestResearchTaskStreamEventKnown:
    """Known event names still resolve to Event enum members."""

    @pytest.mark.parametrize(
        "event_name",
        [
            "connected",
            "response.done",
            "complete",
            "completed",
            "error",
            "failed",
            "cancelled",
        ],
    )
    def test_known_event_name_resolves_to_event_enum(self, event_name: str) -> None:
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": event_name, "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, Event)
        assert evt.event.value == event_name

    def test_known_event_equality_check_preserves_compare_eq_str(self) -> None:
        """``evt.event == 'completed'`` keeps working when the input is a known Event member."""
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "completed", "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, Event)
        assert evt.event == "completed"
        assert evt.event.value == "completed"


class TestResearchTaskStreamEventUnknown:
    """Unknown event names survive unmarshal as plain strings."""

    @pytest.mark.parametrize(
        "future_event_name",
        [
            "retry",
            "checkpoint",
            "completely.new.event.we.dont.know.about",
            "0x-prefixed-thing",
        ],
    )
    def test_unknown_event_name_resolves_to_str(
        self, future_event_name: str
    ) -> None:
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": future_event_name, "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, str)
        assert not isinstance(evt.event, Event)
        assert evt.event == future_event_name

    def test_unknown_event_equality_against_raw_string(self) -> None:
        """``evt.event == 'whatever'`` returns True for unknown names."""
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "retry", "data": _EVENT_DATA}
        )
        assert evt.event == "retry"

    def test_unknown_event_equality_against_known_event_name(self) -> None:
        """Equality against an unrelated known name returns False."""
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "retry", "data": _EVENT_DATA}
        )
        assert evt.event != "completed"
        assert evt.event != "connected"

    def test_unknown_event_isinstance_event_returns_false(self) -> None:
        """``isinstance(evt.event, Event)`` returns False for unknown names."""
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "checkpoint", "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, str)
        assert not isinstance(evt.event, Event)

    def test_unknown_event_membership_check_in_set(self) -> None:
        """``evt.event in {'a', 'b', 'retry'}`` works for unknown names."""
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "retry", "data": _EVENT_DATA}
        )
        assert evt.event in {"retry", "checkpoint"}
        assert evt.event not in {"completed", "failed"}


class TestResearchTaskStreamEventRoundTrip:
    """Known and unknown events round-trip to JSON identically."""

    def test_known_event_round_trips_to_value_string(self) -> None:
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "completed", "data": _EVENT_DATA}
        )
        dumped = evt.model_dump(by_alias=True)
        assert dumped["event"] == "completed"

    def test_unknown_event_round_trips_to_value_string(self) -> None:
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "retry", "data": _EVENT_DATA}
        )
        dumped = evt.model_dump(by_alias=True)
        assert dumped["event"] == "retry"

    def test_unknown_event_round_trip_no_warnings(self) -> None:
        """``model_dump`` on an unknown event must not emit warnings.

        The ``OpenEnumMeta`` switch fixes the prior
        ``PydanticSerializationUnexpectedValue`` warnings that
        ``Union[Event, UnrecognizedStr]`` produced.
        """
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "retry", "data": _EVENT_DATA}
        )
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            dumped = evt.model_dump(by_alias=True)
        assert dumped["event"] == "retry"


class TestResearchTaskStreamEventDeclaredType:
    """The declared type of ``event`` must admit the plain-``str`` case.

    Every other test in this module passes whether the field is annotated
    ``Event`` or ``EventName``, because they assert runtime behavior and
    the runtime behavior comes from ``OpenEnumMeta``. The annotation is a
    separate contract: annotated ``Event``, a caller writing
    ``evt.event.value`` type-checks clean and then raises
    ``AttributeError`` the first time the server emits an unenumerated
    name, and the ``isinstance(evt.event, Event)`` guard the docstring
    prescribes narrows to ``Never``. Pinning it here is what keeps the
    declared type honest.
    """

    def test_event_field_annotation_admits_str(self) -> None:
        annotation = ResearchTaskStreamEvent.model_fields["event"].annotation
        assert annotation is EventName, (
            "ResearchTaskStreamEvent.event must be annotated EventName "
            f"(Union[Event, str]), got {annotation!r}. A bare Event "
            "annotation hides the unknown-event-name case from type checkers."
        )
        assert set(get_args(EventName)) == {Event, str}

    def test_typed_dict_annotation_matches_model(self) -> None:
        assert (
            get_type_hints(ResearchTaskStreamEventTypedDict)["event"]
            is ResearchTaskStreamEvent.model_fields["event"].annotation
        )


class TestStreamDecodePath:
    """End-to-end pin through the real SSE decode path (DX-778).

    The tests above validate the model directly. That is not the path a caller
    exercises: ``stream_research_task`` wraps every SSE frame in
    ``unmarshal_json_response``, which re-raises any pydantic failure as
    ``ResponseValidationError``. A regression could therefore leave the
    model-level tests green while the streaming API still blows up on a new
    server event name, so this drives the generated method over a
    ``MockTransport`` stream carrying both known and unknown event names.
    """

    _FRAMES = [
        b"id: 0\nevent: connected\ndata: "
        b'{"type":"connected","task_id":"abc","status":"running"}\n\n',
        # Not in the Event enum -- the exact case DX-778 is about.
        b"id: 1\nevent: research.searching\ndata: "
        b'{"type":"research.searching","task_id":"abc","status":"running"}\n\n',
        b"id: 2\nevent: checkpoint\ndata: "
        b'{"type":"checkpoint","task_id":"abc","status":"running"}\n\n',
        b"id: 3\nevent: response.done\ndata: "
        b'{"type":"response.done","task_id":"abc","status":"completed"}\n\n',
    ]

    def _stream_events(self):
        def handler(request):
            return httpx.Response(
                200,
                headers={"content-type": "text/event-stream"},
                content=b"".join(self._FRAMES),
            )

        client = httpx.Client(transport=httpx.MockTransport(handler))
        try:
            with You(
                api_key_auth="k", server_url="http://mock.local", client=client
            ) as you:
                with you.stream_research_task(
                    task_id="00000000-0000-0000-0000-000000000001"
                ) as stream:
                    return list(stream)
        finally:
            client.close()

    def test_unknown_event_names_do_not_raise_on_the_stream_path(self):
        """No ``ResponseValidationError`` for any frame, known or unknown."""
        events = self._stream_events()
        assert [e.event for e in events] == [
            "connected",
            "research.searching",
            "checkpoint",
            "response.done",
        ]

    def test_stream_path_types_split_known_from_unknown(self):
        events = {e.event: e.event for e in self._stream_events()}
        assert isinstance(events["connected"], Event)
        assert isinstance(events["response.done"], Event)
        assert not isinstance(events["research.searching"], Event)
        assert not isinstance(events["checkpoint"], Event)
        assert type(events["checkpoint"]) is str  # noqa: E721

    def test_stream_path_emits_no_warnings(self):
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            events = self._stream_events()
        assert len(events) == len(self._FRAMES)
