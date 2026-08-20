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
from youdotcom.models import Event

if isinstance(evt.event, Event):
    print(evt.event.value)   # known name
else:
    print(evt.event)         # unknown name, plain str
```

Equality against a raw string works either way, because `Event` members are
`str` subclasses:

```python
if evt.event == "completed":
    ...
```
