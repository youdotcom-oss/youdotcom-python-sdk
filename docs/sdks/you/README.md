# You SDK

## Overview

You.com Contents API: Get the best search results from web and news sources

### Available Operations

* [agents_runs](#agents_runs) - Run an Agent
* [search](#search) - Returns a list of unified search results from web and news sources
* [contents](#contents) - Returns the content of the web pages

## agents_runs

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

    res = you.agents_runs(request={
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

## search

Returns a list of unified search results from web and news sources

### Example Usage

<!-- UsageSnippet language="python" operationID="search" method="get" path="/v1/search" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.search(query="Your query", language=models.Language.EN)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                       | Type                                                                                                                                                                                            | Required                                                                                                                                                                                        | Description                                                                                                                                                                                     | Example                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`                                                                                                                                                                                         | *str*                                                                                                                                                                                           | :heavy_check_mark:                                                                                                                                                                              | The search query used to retrieve relevant results from the web. You can also include [search operators](#search-operators) to refine your search.                                              | Your query                                                                                                                                                                                      |
| `count`                                                                                                                                                                                         | *Optional[int]*                                                                                                                                                                                 | :heavy_minus_sign:                                                                                                                                                                              | Specifies the maximum number of search results to return per section (the sections are `web` and `news`. See the JSON response to visualize them).                                              |                                                                                                                                                                                                 |
| `freshness`                                                                                                                                                                                     | [Optional[models.SearchFreshness]](../../models/searchfreshness.md)                                                                                                                             | :heavy_minus_sign:                                                                                                                                                                              | Specifies the freshness of the results to return.                                                                                                                                               |                                                                                                                                                                                                 |
| `offset`                                                                                                                                                                                        | *Optional[int]*                                                                                                                                                                                 | :heavy_minus_sign:                                                                                                                                                                              | Indicates the `offset` for pagination. The `offset` is calculated in multiples of `count`. For example, if `count = 5` and `offset = 1`, results 5–10 will be returned. Range `0 ≤ offset ≤ 9`. |                                                                                                                                                                                                 |
| `country`                                                                                                                                                                                       | [Optional[models.SearchCountry]](../../models/searchcountry.md)                                                                                                                                 | :heavy_minus_sign:                                                                                                                                                                              | The country code that determines the geographical focus of the web results.                                                                                                                     |                                                                                                                                                                                                 |
| `language`                                                                                                                                                                                      | [Optional[models.Language]](../../models/language.md)                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                              | The language of the web results that will be returned (BCP 47 format).                                                                                                                          |                                                                                                                                                                                                 |
| `safesearch`                                                                                                                                                                                    | [Optional[models.SearchSafesearch]](../../models/searchsafesearch.md)                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                              | Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not.                                                                       |                                                                                                                                                                                                 |
| `livecrawl`                                                                                                                                                                                     | [Optional[models.SearchLivecrawl]](../../models/searchlivecrawl.md)                                                                                                                             | :heavy_minus_sign:                                                                                                                                                                              | Indicates which section(s) of search results to livecrawl and return full page content.                                                                                                         |                                                                                                                                                                                                 |
| `livecrawl_formats`                                                                                                                                                                             | [Optional[models.SearchLivecrawlFormats]](../../models/searchlivecrawlformats.md)                                                                                                               | :heavy_minus_sign:                                                                                                                                                                              | Indicates the format of the livecrawled content.                                                                                                                                                |                                                                                                                                                                                                 |
| `retries`                                                                                                                                                                                       | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                | :heavy_minus_sign:                                                                                                                                                                              | Configuration to override the default retry behavior of the client.                                                                                                                             |                                                                                                                                                                                                 |
| `server_url`                                                                                                                                                                                    | *Optional[str]*                                                                                                                                                                                 | :heavy_minus_sign:                                                                                                                                                                              | An optional server URL to use.                                                                                                                                                                  | http://localhost:8080                                                                                                                                                                           |

### Response

**[models.SearchResponse](../../models/searchresponse.md)**

### Errors

| Error Type                       | Status Code                      | Content Type                     |
| -------------------------------- | -------------------------------- | -------------------------------- |
| errors.SearchUnauthorizedError   | 401                              | application/json                 |
| errors.SearchForbiddenError      | 403                              | application/json                 |
| errors.SearchInternalServerError | 500                              | application/json                 |
| errors.YouDefaultError           | 4XX, 5XX                         | \*/\*                            |

## contents

Returns the content of the web pages

### Example Usage

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents(urls=[
        "https://www.you.com",
    ], format_=models.FormatEnum1.HTML)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `urls`                                                              | List[*str*]                                                         | :heavy_minus_sign:                                                  | Array of URLs to fetch the contents from.                           |                                                                     |
| `format_`                                                           | [Optional[models.Format]](../../models/format_.md)                  | :heavy_minus_sign:                                                  | The format of the content to be returned.                           | html                                                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |

### Response

**[List[models.ContentsResponse]](../../models/.md)**

### Errors

| Error Type                         | Status Code                        | Content Type                       |
| ---------------------------------- | ---------------------------------- | ---------------------------------- |
| errors.ContentsUnauthorizedError   | 401                                | application/json                   |
| errors.ContentsForbiddenError      | 403                                | application/json                   |
| errors.ContentsInternalServerError | 500                                | application/json                   |
| errors.YouDefaultError             | 4XX, 5XX                           | \*/\*                              |