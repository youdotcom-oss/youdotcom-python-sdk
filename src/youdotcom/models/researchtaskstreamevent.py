
from __future__ import annotations
from enum import Enum
from pydantic import model_serializer
from typing import Any, Dict, Optional, Union
from typing_extensions import NotRequired, TypedDict
from youdotcom.types import (
    BaseModel,
    Nullable,
    OptionalNullable,
    UNSET,
    UNSET_SENTINEL,
)
from youdotcom.utils.enums import OpenEnumMeta


class Event(str, Enum, metaclass=OpenEnumMeta):
    r"""The type of the SSE event. Terminal events that close the stream are: `response.done`, `complete`, `error`, and `cancelled`. The stream may also emit `completed`, `failed`, or `cancelled` as event names corresponding to the task's terminal status.

    Note: this enum is **not** an exhaustive list. Unknown event names
    are accepted as plain strings so that a future server-side event
    addition does not break unmarshal. Equality checks against a known
    name (``evt.event == "connected"``) keep working because ``Event``
    members are ``str`` subclasses. Use ``isinstance(evt.event, Event)``
    to distinguish known from unknown values.
    """

    CONNECTED = "connected"
    RESPONSE_DONE = "response.done"
    COMPLETE = "complete"
    COMPLETED = "completed"
    ERROR = "error"
    FAILED = "failed"
    CANCELLED = "cancelled"


# Public alias so callers reading IDE/help see that any string is
# accepted on the wire, not just the enum members.
EventName = Union[Event, str]


class ResearchTaskStreamEventDataTypedDict(TypedDict):
    r"""The event payload. Structure varies by event type. Common fields include type, task_id, status, data (event-specific), error, and sequence."""

    type: NotRequired[str]
    r"""The event type identifier."""
    task_id: NotRequired[str]
    r"""The task UUID."""
    status: NotRequired[str]
    r"""Current task status when the event was emitted."""
    data: NotRequired[Dict[str, Any]]
    r"""Event-specific payload data."""
    error: NotRequired[Nullable[str]]
    r"""Error message if the event represents an error."""
    sequence: NotRequired[int]
    r"""Event sequence number."""


class ResearchTaskStreamEventData(BaseModel):
    r"""The event payload. Structure varies by event type. Common fields include type, task_id, status, data (event-specific), error, and sequence."""

    type: Optional[str] = None
    r"""The event type identifier."""

    task_id: Optional[str] = None
    r"""The task UUID."""

    status: Optional[str] = None
    r"""Current task status when the event was emitted."""

    data: Optional[Dict[str, Any]] = None
    r"""Event-specific payload data."""

    error: OptionalNullable[str] = UNSET
    r"""Error message if the event represents an error."""

    sequence: Optional[int] = None
    r"""Event sequence number."""

    @model_serializer(mode="wrap")
    def serialize_model(self, handler):
        optional_fields = set(
            ["type", "task_id", "status", "data", "error", "sequence"]
        )
        nullable_fields = set(["error"])
        serialized = handler(self)
        m = {}

        for n, f in type(self).model_fields.items():
            k = f.alias or n
            val = serialized.get(k, serialized.get(n))
            is_nullable_and_explicitly_set = (
                k in nullable_fields
                and (self.__pydantic_fields_set__.intersection({n}))  # pylint: disable=no-member
            )

            if val != UNSET_SENTINEL:
                if (
                    val is not None
                    or k not in optional_fields
                    or is_nullable_and_explicitly_set
                ):
                    m[k] = val

        return m


class ResearchTaskStreamEventTypedDict(TypedDict):
    r"""A server-sent event for a background research task stream."""

    id: str
    r"""Sequence number of the SSE event."""
    event: EventName
    r"""The type of the SSE event. Terminal events that close the stream are: `response.done`, `complete`, `error`, and `cancelled`. The stream may also emit `completed`, `failed`, or `cancelled` as event names corresponding to the task's terminal status. Unknown event names are accepted as plain strings so future server-side additions unmarshal cleanly.
    """
    data: ResearchTaskStreamEventDataTypedDict
    r"""The event payload. Structure varies by event type. Common fields include type, task_id, status, data (event-specific), error, and sequence."""


class ResearchTaskStreamEvent(BaseModel):
    r"""A server-sent event for a background research task stream."""

    id: str
    r"""Sequence number of the SSE event."""

    event: EventName
    r"""The type of the SSE event. Terminal events that close the stream are: `response.done`, `complete`, `error`, and `cancelled`. The stream may also emit `completed`, `failed`, or `cancelled` as event names corresponding to the task's terminal status.

    Declared as ``EventName`` (``Union[Event, str]``) because that is what
    the field actually holds at runtime: a known name resolves to the
    ``Event`` member, and an unknown name stays a plain ``str`` so that a
    future server-side event addition does not raise
    ``ResponseValidationError`` on the unmarshal path. Callers that branch
    on a known name (``evt.event == "completed"``) keep working unchanged
    because ``Event`` members are ``str`` subclasses. Callers that want the
    enum API (``evt.event.value``) must guard with
    ``isinstance(evt.event, Event)`` first — that check returns ``False``
    for unknown names, and the declared union is what makes the guard
    meaningful to a type checker.
    """

    data: ResearchTaskStreamEventData
    r"""The event payload. Structure varies by event type. Common fields include type, task_id, status, data (event-specific), error, and sequence."""
