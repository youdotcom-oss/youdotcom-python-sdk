# PostV1AgentsRunsEventStreamResponseBody

Inference response in application/json or text/event-stream format.


## Fields

| Field                                      | Type                                       | Required                                   | Description                                | Example                                    |
| ------------------------------------------ | ------------------------------------------ | ------------------------------------------ | ------------------------------------------ | ------------------------------------------ |
| `id`                                       | *Optional[str]*                            | :heavy_minus_sign:                         | Sequence number of the SSE event           | 0                                          |
| `event`                                    | *Optional[str]*                            | :heavy_minus_sign:                         | The type of the SSE event.                 | response.output_item.added                 |
| `data`                                     | [Optional[models.Data]](../models/data.md) | :heavy_minus_sign:                         | N/A                                        |                                            |