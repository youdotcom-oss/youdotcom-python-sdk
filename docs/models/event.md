# Event

The type of the SSE event. Most streams start with a `connected` event and then deliver terminal events `response.done`, `complete`, `error`, or `cancelled` from the worker.
If the SSE stream has aged out (after ~15 minutes) without any events flowing and the task is already in a terminal state, the server emits a synthetic event whose name is the task's status: one of `completed`, `failed`, or `cancelled`. Treat these synthetic event names the same as the corresponding worker-emitted names (`complete` ↔ `completed`, `error` ↔ `failed`, `cancelled` == `cancelled`).

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