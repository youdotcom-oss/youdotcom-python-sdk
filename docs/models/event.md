# Event

The type of the SSE event. Terminal events that close the stream are: `response.done`, `complete`, `error`, and `cancelled`. The stream may also emit `completed`, `failed`, or `cancelled` as event names corresponding to the task's terminal status.

## Example Usage

```python
from youdotcom.models import Event

value = Event.CONNECTED
```


## Values

| Name            | Value           |
| --------------- | --------------- |
| `CONNECTED`     | connected       |
| `RESPONSE_DONE` | response.done   |
| `COMPLETE`      | complete        |
| `COMPLETED`     | completed       |
| `ERROR`         | error           |
| `FAILED`        | failed          |
| `CANCELLED`     | cancelled       |

## Open enum

This list is **not** exhaustive. `Event` is an open enum: an event name the
SDK does not yet enumerate unmarshals as a plain `str` rather than raising
`ResponseValidationError`, so a server-side event addition does not break
existing clients. Fields typed [`EventName`](../models/eventname.md) hold
either an `Event` member (known name) or a `str` (unknown name).

Guard before reaching for the enum API:

```python
from youdotcom.models import Event, ResearchTaskStreamEvent

known = ResearchTaskStreamEvent.model_validate(
    {"id": "1", "event": "completed", "data": {}}
)
unknown = ResearchTaskStreamEvent.model_validate(
    {"id": "2", "event": "some.future.event", "data": {}}
)

for evt in (known, unknown):
    if isinstance(evt.event, Event):
        print("known:", evt.event.value)
    else:
        print("unknown:", evt.event)
# known: completed
# unknown: some.future.event
```

Equality against a raw string works either way, because `Event` members are
`str` subclasses — so this needs no guard:

```python
from youdotcom.models import ResearchTaskStreamEvent

evt = ResearchTaskStreamEvent.model_validate(
    {"id": "1", "event": "completed", "data": {}}
)
print(evt.event == "completed")
# True
```
