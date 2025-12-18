# AgentRunsStreamingResponse

A server-sent event containing stock market update content


## Fields

| Field                                           | Type                                            | Required                                        | Description                                     |
| ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| `id`                                            | *str*                                           | :heavy_check_mark:                              | Sequence number of the SSE event, starts from 0 |
| `event`                                         | *str*                                           | :heavy_check_mark:                              | The type of the SSE event                       |
| `data`                                          | [models.Data](../models/data.md)                | :heavy_check_mark:                              | N/A                                             |