# ResearchTaskStreamEventData

The event payload. Structure varies by event type. Common fields include type, task_id, status, data (event-specific), error, and sequence.


## Fields

| Field                                           | Type                                            | Required                                        | Description                                     |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| `type`                                          | *Optional[str]*                                 | :heavy_minus_sign:                              | The event type identifier.                      |
| `task_id`                                       | *Optional[str]*                                 | :heavy_minus_sign:                              | The task UUID.                                  |
| `status`                                        | *Optional[str]*                                 | :heavy_minus_sign:                              | Current task status when the event was emitted. |
| `data`                                          | Dict[str, *Any*]                                | :heavy_minus_sign:                              | Event-specific payload data.                    |
| `error`                                         | *OptionalNullable[str]*                         | :heavy_minus_sign:                              | Error message if the event represents an error. |
| `sequence`                                      | *Optional[int]*                                 | :heavy_minus_sign:                              | Event sequence number.                          |