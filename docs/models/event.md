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