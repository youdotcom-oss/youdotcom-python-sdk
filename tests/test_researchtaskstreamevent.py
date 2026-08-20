"""Tests for ``ResearchTaskStreamEvent`` model-level contracts.

The SSE ``event`` discriminator must accept any string the server
emits, including names the SDK does not enumerate. The strict ``Event``
enum is preserved for backwards compatibility on the Python surface
(catchable via ``isinstance`` / equality, IDE autocomplete still
narrow), and unknown names flow through as
:class:`youdotcom.types.UnrecognizedStr` instances that compare equal
to their raw string value.

The regression scenario: the server introduces a
new SSE event name (e.g. ``retry``, ``checkpoint``) and the SDK stops
raising ``ResponseValidationError`` on the unmarshal path. This test
suite pins both halves of the contract:

- Known event names still resolve to :class:`Event` enum members.
- Unknown event names resolve to :class:`UnrecognizedStr` instances
  that compare equal to their raw string.
"""

from __future__ import annotations

import pytest

from youdotcom.models.researchtaskstreamevent import (
    Event,
    ResearchTaskStreamEvent,
)
from youdotcom.types import UnrecognizedStr


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
        """``evt.event == 'completed'`` keeps working when the input is a known Event member.

        This is the explicit backwards-compat promise: callers
        who match on the raw string identifier do not need to update.
        """
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": "completed", "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, Event)
        assert evt.event == "completed"
        assert evt.event.value == "completed"


class TestResearchTaskStreamEventUnknown:
    """Unknown event names survive unmarshal as ``UnrecognizedStr``."""

    @pytest.mark.parametrize(
        "future_event_name",
        [
            "retry",
            "checkpoint",
            "completely.new.event.we.dont.know.about",
            "0x-prefixed-thing",
        ],
    )
    def test_unknown_event_name_resolves_to_unrecognized_str(
        self, future_event_name: str
    ) -> None:
        evt = ResearchTaskStreamEvent.model_validate(
            {"id": "1", "event": future_event_name, "data": _EVENT_DATA}
        )
        assert isinstance(evt.event, UnrecognizedStr)
        assert not isinstance(evt.event, Event)

    def test_unknown_event_equality_against_raw_string(self) -> None:
        """``evt.event == 'whatever'`` returns True even when UnrecognizedStr wraps it.

        Backwards-compat: callers branching on raw string identifiers
        (the documented contract of the discriminator field) keep
        working without changes.
        """
        evt = ResearchTaskStreamEvent.model_validate(
            {
                "id": "1",
                "event": "retry",
                "data": _EVENT_DATA,
            }
        )
        assert evt.event == "retry"

    def test_unknown_event_equality_against_known_event_name(self) -> None:
        """Equality against an unrelated known name returns False."""
        evt = ResearchTaskStreamEvent.model_validate(
            {
                "id": "1",
                "event": "retry",
                "data": _EVENT_DATA,
            }
        )
        # Cross-name comparison must not return True just because both
        # back onto ``str``. If this assertion fires, UnrecognizedStr
        # has been over-engineered into something that coerces strings
        # onto enum-equivalent values.
        assert evt.event != "completed"
        assert evt.event != "connected"

    def test_unknown_event_isinstance_event_returns_false(self) -> None:
        """``isinstance(evt.event, Event)`` returns False for unknown names.

        Callers that want exhaustive enumeration can still fall back to
        the strict mode and detect unknown names by the absence of
        ``Event`` membership. This is exactly the ``isinstance`` check
        the design recommends.
        """
        evt = ResearchTaskStreamEvent.model_validate(
            {
                "id": "1",
                "event": "checkpoint",
                "data": _EVENT_DATA,
            }
        )
        assert isinstance(evt.event, UnrecognizedStr)
        assert not isinstance(evt.event, Event)

    def test_unknown_event_membership_check_in_set(self) -> None:
        """``evt.event in {'a', 'b', 'retry'}`` works for UnrecognizedStr.

        ``__contains__`` on a string set delegates to ``__eq__`` on the
        string subclass; this confirms the discriminator can be
        filtered through ``in`` membership tests without losing
        coverage on unknown values.
        """
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
