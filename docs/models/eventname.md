# EventName

The declared type of `ResearchTaskStreamEvent.event`:

```python
EventName = Union[Event, str]
```

A known SSE event name resolves to the corresponding
[`Event`](../models/event.md) member. An unknown name — one the installed SDK
version does not enumerate — stays a plain `str`, so a server-side event
addition unmarshals cleanly instead of raising `ResponseValidationError`.

## Example Usage

```python
from youdotcom.models import Event

for evt in stream:
    if isinstance(evt.event, Event):
        # Known name: full enum API available.
        print(evt.event.value)
    else:
        # Unknown name: forward-compatible passthrough.
        print(f"unrecognized event: {evt.event}")
```

Callers that only compare against raw strings need no guard, because `Event`
members are `str` subclasses:

```python
if evt.event == "completed":
    ...
```
