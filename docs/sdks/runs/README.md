# Runs
(*agents.runs*)

## Overview

### Available Operations

* [create](#create)

## create

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v1/agents/runs" method="post" path="/v1/agents/runs" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(agent="express", input="What is the capital of France?", stream=False, tools=[
        {
            "type": "compute",
        },
    ])

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `agent`                                                             | [models.Agent](../../models/agent.md)                               | :heavy_check_mark:                                                  | Agent type (express, advanced) or custom agent UUID                 |
| `input`                                                             | *str*                                                               | :heavy_check_mark:                                                  | User input prompt.                                                  |
| `stream`                                                            | *Optional[bool]*                                                    | :heavy_minus_sign:                                                  | N/A                                                                 |
| `tools`                                                             | List[[models.Tool](../../models/tool.md)]                           | :heavy_minus_sign:                                                  | Array of tool configurations                                        |
| `verbosity`                                                         | [Optional[models.Verbosity]](../../models/verbosity.md)             | :heavy_minus_sign:                                                  | Response verbosity level                                            |
| `workflow_config`                                                   | [Optional[models.WorkflowConfig]](../../models/workflowconfig.md)   | :heavy_minus_sign:                                                  | N/A                                                                 |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |
| `server_url`                                                        | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | An optional server URL to use.                                      |

### Response

**[models.PostV1AgentsRunsResponse](../../models/postv1agentsrunsresponse.md)**

### Errors

| Error Type                               | Status Code                              | Content Type                             |
| ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| errors.BadRequestError                   | 400                                      | application/json                         |
| errors.PostV1AgentsRunsUnauthorizedError | 401                                      | application/json                         |
| errors.PostV1AgentsRunsForbiddenError    | 403                                      | application/json                         |
| errors.YouDefaultError                   | 4XX, 5XX                                 | \*/\*                                    |