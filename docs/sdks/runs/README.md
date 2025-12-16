# Agents.Runs

## Overview

### Available Operations

* [create](#create) - Run an Agent

## create

Execute queries using You.com's AI agents. This endpoint supports three agent types:

- **Express Agent**: Fast responses with optional web search (max 1 search)
- **Advanced Agent**: Complex queries with multi-turn reasoning, planning, and tool usage
- **Custom Agent**: User-configured assistants created in the You.com UI

The response format depends on the `stream` parameter - either a complete JSON payload or Server-Sent Events (SSE).


### Example Usage

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "express",
        "input": "What is the capital of France?",
        "stream": False,
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `request`                                                           | [models.AgentsRunsRequest](../../models/agentsrunsrequest.md)       | :heavy_check_mark:                                                  | The request object to use for the request.                          |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |
| `server_url`                                                        | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | An optional server URL to use.                                      |

### Response

**[models.AgentsRunsResponse](../../models/agentsrunsresponse.md)**

### Errors

| Error Type                       | Status Code                      | Content Type                     |
| -------------------------------- | -------------------------------- | -------------------------------- |
| errors.AgentRuns400ResponseError | 400                              | application/json                 |
| errors.AgentRuns401ResponseError | 401                              | application/json                 |
| errors.AgentRuns422ResponseError | 422                              | application/json                 |
| errors.YouDefaultError           | 4XX, 5XX                         | \*/\*                            |