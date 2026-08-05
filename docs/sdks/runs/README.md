# Agents.Runs

> **DEPRECATED** — The `Agents.Runs` sub-SDK pattern still works but emits `DeprecationWarning`. The sub-SDK layer was Speakeasy-generated indirection (`Agents` → `Runs` → `create()`); `you.agents()` is now a direct method on `You` with the same request types. Use the direct method instead:
>
> - `you.agents(request=...)` (was `you.agents.runs.create(request=...)`)
> - `you.agents_async(request=...)` (was `you.agents.runs.create_async(request=...)`)
>
> See [docs/sdks/you/README.md](../you/README.md#agents) for the current API. The content below is kept for reference only.

## Overview

### Available Operations

* [create](#create) - Run an Agent

## create

Execute queries using You.com's AI agents. This endpoint supports three agent types:

- **Express Agent**: Fast responses with optional web search (max 1 search)
- **Advanced Agent**: Complex queries with multi-turn reasoning, planning, and tool usage
- **Custom Agent**: User-configured assistants created in the You.com UI

The response format depends on the `stream` parameter - either a complete JSON payload or Server-Sent Events (SSE).


### Example Usage: advanced_batch

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="advanced_batch" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "advanced",
        "input": "You are a biologist studying the impacts of microplastics. Explain what microplastics are to a group of engineers, explain the impacts of microplastics on the body, and what the common sources and dosages of microplastics are. Highlight what a safe dosage might be and how to achieve it",
        "stream": False,
        "tools": [
            {
                "type": "research",
                "search_effort": models.SearchEffort.AUTO,
                "report_verbosity": models.ReportVerbosity.MEDIUM,
            },
        ],
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
### Example Usage: advanced_stream

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="advanced_stream" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "express",
        "input": "Analyze the economic impact of renewable energy adoption",
        "stream": True,
        "tools": [
            {
                "type": "web_search",
            },
        ],
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
### Example Usage: custom_batch

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="custom_batch" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "63773261-b4de-4d8f-9dfd-cff206a5cb51",
        "input": "What is the capital of France?",
        "stream": False,
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
### Example Usage: custom_stream

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="custom_stream" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "63773261-b4de-4d8f-9dfd-cff206a5cb51",
        "input": "Tell me about the history of Paris",
        "stream": True,
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```
### Example Usage: express_batch

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="express_batch" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
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
### Example Usage: express_stream

<!-- UsageSnippet language="python" operationID="AgentsRuns" method="post" path="/v1/agents/runs" example="express_stream" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "express",
        "input": "What are some great recipes I can make in under half an hour",
        "stream": True,
        "tools": [
            {
                "type": "web_search",
            },
        ],
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