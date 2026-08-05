# You SDK

## Overview

You.com API: Unified API for Express, Advanced, and Custom Agents from You.com
Get the best search results from web and news sources
Returns the HTML or Markdown of a target webpage
Multi-step reasoning with comprehensive research capabilities
Finance-focused multi-step research with competitive accuracy at same price points and latencies as the Research API
Comprehensive API for You.com services:
- **Agents API**: Execute queries using Express, Advanced, and Custom AI agents
- **Answer API**: Get synthesized, citation-backed answers grounded in real-time web results
- **Research API**: In-depth, multi-step research with citations and sources
- **Finance Research API**: Finance-focused multi-step research with citations and sources
- **Search API**: Get search results from web and news sources (keyless-capable via `/v1/agents/search`)
- **Contents API**: Retrieve and process web page content

### Available Operations

* [answer](#answer) - Returns a synthesized answer with citations from web search results
* [agents](#agents) - Run an Agent
* [search](#search) - Returns a list of unified search results from web and news sources
* [contents](#contents) - Returns the content of the web pages
* [research](#research) - Returns comprehensive research-grade answers with multi-step reasoning
* [get_research_task](#get_research_task) - Get the status of a background research task
* [stream_research_task](#stream_research_task) - Stream updates for a background research task
* [finance_research](#finance_research) - Returns comprehensive finance-grade research answers with multi-step reasoning

## answer

Returns a synthesized answer with citations from web search results.

### Example Usage

```python
import os
from youdotcom import You

with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:
    res = you.answer(query="What is the capital of France?")
    print(res)
```

## agents

Execute queries using You.com's AI agents (Express, Advanced, or Custom).

### Example Usage

```python
import os
from youdotcom import You, models

with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:
    res = you.agents(request=models.ExpressAgentRunsRequest(
        input="What are the latest AI developments?",
    ))
    print(res)
```

## search

Search via `POST /v1/agents/search` — the keyless-capable proxy. With no API key configured, runs in the free tier (100 queries/day, count ≤ 50, no livecrawl). With a key, the proxy forwards to the full search endpoint. Country and language accept plain strings and are normalized to uppercase.

### Example Usage: keyless

```python
from youdotcom import You

# No API key — uses the free tier
with You() as you:
    res = you.search(query="What is the capital of France?", count=5)
    if res.results and res.results.web:
        print(res.results.web[0].title)
```

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="authFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: authorizationFailure

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="authorizationFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: invalidOrExpired

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="invalidOrExpired" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: invalidParams

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="invalidParams" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingApiKey

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="missingApiKey" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingScopes

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="missingScopes" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: otherAuthParsing

<!-- UsageSnippet language="python" operationID="agentsSearch" method="post" path="/v1/agents/search" example="otherAuthParsing" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                          | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `query`                                                                                                                                                                                                                                                                                                                                                                                                                                                       | *str*                                                                                                                                                                                                                                                                                                                                                                                                                                                         | :heavy_check_mark:                                                                                                                                                                                                                                                                                                                                                                                                                                            | The search query used to retrieve relevant results from the web. You can also include [search operators](https://docs.you.com/search/search-operators) to refine your search.                                                                                                                                                                                                                                                                                 | What are the latest geopolitical updates from India                                                                                                                                                                                                                                                                                                                                                                                                           |
| `count`                                                                                                                                                                                                                                                                                                                                                                                                                                                       | *Optional[int]*                                                                                                                                                                                                                                                                                                                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Specifies the maximum number of search results to return per section (the sections are `web` and `news`. See the JSON response to visualize them).                                                                                                                                                                                                                                                                                                            |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `freshness`                                                                                                                                                                                                                                                                                                                                                                                                                                                   | [Optional[models.FreshnessValue]](../../models/freshnessvalue.md)                                                                                                                                                                                                                                                                                                                                                                                             | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Specifies the freshness of the results to return. Provide either one of `day`, `week`, `month`, `year`, or a date range string in the format `YYYY-MM-DDtoYYYY-MM-DD`.<br/><br/>When your search query includes a temporal keyword and you also set a freshness parameter, the search will use the broader (i.e., less restrictive) of the two timeframes. For example, if you use `query=news+this+week&freshness=month`, the results will use a freshness of month. |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `offset`                                                                                                                                                                                                                                                                                                                                                                                                                                                      | *Optional[int]*                                                                                                                                                                                                                                                                                                                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Indicates the `offset` for pagination. The `offset` is calculated in multiples of `count`. For example, if `count = 5` and `offset = 1`, results 5–10 will be returned. Range `0 ≤ offset ≤ 9`.                                                                                                                                                                                                                                                               |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `country`                                                                                                                                                                                                                                                                                                                                                                                                                                                     | [Optional[models.Country]](../../models/country.md)                                                                                                                                                                                                                                                                                                                                                                                                           | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | The country code that determines the geographical focus of the web results.                                                                                                                                                                                                                                                                                                                                                                                   |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `language`                                                                                                                                                                                                                                                                                                                                                                                                                                                    | [Optional[models.Language]](../../models/language.md)                                                                                                                                                                                                                                                                                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | The language of the web results that will be returned (BCP 47 format).                                                                                                                                                                                                                                                                                                                                                                                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `safesearch`                                                                                                                                                                                                                                                                                                                                                                                                                                                  | [Optional[models.SafeSearch]](../../models/safesearch.md)                                                                                                                                                                                                                                                                                                                                                                                                     | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Configures the safesearch filter for content moderation. This allows you to decide whether to return NSFW content or not.                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `livecrawl`                                                                                                                                                                                                                                                                                                                                                                                                                                                   | [Optional[models.LiveCrawl]](../../models/livecrawl.md)                                                                                                                                                                                                                                                                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Indicates which section(s) of search results to livecrawl and return full page content.                                                                                                                                                                                                                                                                                                                                                                       |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `livecrawl_formats`                                                                                                                                                                                                                                                                                                                                                                                                                                           | List[[models.LiveCrawlFormats](../../models/livecrawlformats.md)]                                                                                                                                                                                                                                                                                                                                                                                             | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Indicates the format(s) of the livecrawled content. Pass one or both values (`html`, `markdown`). In a GET request, repeat the parameter: `?livecrawl_formats=html&livecrawl_formats=markdown`. In a POST body, provide a JSON array: `["html", "markdown"]`.                                                                                                                                                                                                 |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `include_domains`                                                                                                                                                                                                                                                                                                                                                                                                                                             | List[*str*]                                                                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | A list of domains to restrict search results to. Only results from these domains will be returned. Supports up to 500 domains. This is a strict allowlist, not a boost — results are limited exclusively to the specified domains.<br/><br/>Cannot be combined with `exclude_domains`; passing both will return a `422` error.                                                                                                                                | [<br/>"nytimes.com",<br/>"bbc.com"<br/>]                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `exclude_domains`                                                                                                                                                                                                                                                                                                                                                                                                                                             | List[*str*]                                                                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | A list of domains to exclude from search results. Results from these domains will be filtered out. Supports up to 500 domains.<br/><br/>Cannot be combined with `include_domains`; passing both will return a `422` error.                                                                                                                                                                                                                                    | [<br/>"spam-site.com",<br/>"other-site.com"<br/>]                                                                                                                                                                                                                                                                                                                                                                                                             |
| `boost_domains`                                                                                                                                                                                                                                                                                                                                                                                                                                               | List[*str*]                                                                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | A list of domains to boost in search ranking. Matching results from these domains receive a relative ranking boost, but results are not limited to these domains. Supports up to 500 domains. Can be combined with `exclude_domains`, but cannot be combined with `include_domains` (returns `422`).                                                                                                                                                          | [<br/>"nytimes.com",<br/>"wired.com"<br/>]                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `crawl_timeout`                                                                                                                                                                                                                                                                                                                                                                                                                                               | *Optional[int]*                                                                                                                                                                                                                                                                                                                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Maximum time in seconds to wait for page content when `livecrawl` is enabled. Must be between 1 and 60 seconds. Default is 10 seconds.                                                                                                                                                                                                                                                                                                                        | 10                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                     | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                              | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                           |                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `server_url`                                                                                                                                                                                                                                                                                                                                                                                                                                                  | *Optional[str]*                                                                                                                                                                                                                                                                                                                                                                                                                                               | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                            | An optional server URL to use.                                                                                                                                                                                                                                                                                                                                                                                                                                | http://localhost:8080                                                                                                                                                                                                                                                                                                                                                                                                                                         |

### Response

**[models.SearchResponse](../../models/searchresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.PaymentRequiredResponseError     | 402                                     | application/json                        |
| errors.UnauthorizedResponseError        | 401                                     | application/json                        |
| errors.ForbiddenResponseError           | 403                                     | application/json                        |
| errors.UnprocessableEntityResponseError | 422                                     | application/json                        |
| errors.InternalServerErrorResponse      | 500                                     | application/json                        |
| errors.YouDefaultError                  | 4XX, 5XX                                | \*/\*                                   |

## contents

Returns the HTML or Markdown of target web pages.

### Example Usage

```python
import os
from youdotcom import You, models

with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:
    res = you.contents(urls=["https://example.com"], formats=[models.ContentsFormats.MARKDOWN])
    print(res)
```

## research

Research goes beyond a single web search. In response to your question, it runs multiple searches, reads through the sources, and synthesizes everything into a thorough, well-cited answer. Use it when a question is too complex for a simple lookup, and when you need a response you can actually trust and verify.

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="authFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: authorizationFailure

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="authorizationFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: invalidEnum

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="invalidEnum" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: invalidJson

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="invalidJson" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: invalidOrExpired

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="invalidOrExpired" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: missingApiKey

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="missingApiKey" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: missingField

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="missingField" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: missingScopes

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="missingScopes" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: otherAuthParsing

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="otherAuthParsing" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```
### Example Usage: stringTooLong

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="stringTooLong" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | *str*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | :heavy_check_mark:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | The research question or complex query requiring in-depth investigation and multi-step reasoning.<br/><br/>Note: The maximum length of the input is 40,000 characters.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `research_effort`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | [Optional[models.ResearchEffort]](../../models/researcheffort.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Controls how much time and effort the Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.<br/><br/>Available levels:<br/>- `lite`: Returns answers quickly. Good for straightforward questions that just need a fast, reliable answer.<br/>- `standard`: The default. Balances speed and depth, a good fit for most questions.<br/>- `deep`: Spends more time researching and cross-referencing sources. Use this when accuracy and thoroughness matter more than speed.<br/>- `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex research tasks where you want the highest quality result.<br/>- `frontier`: The highest-quality tier. Runs over longer durations with improved quality and accuracy. Only works with the task-based API (`background=true`); sending `frontier` without `background=true` returns a 422. |
| `source_control`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | [Optional[models.SourceControl]](../../models/sourcecontrol.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Beta. Controls which web sources the research agent searches and visits. Use this to allow specific domains, block specific domains, boost specific domains, filter by recency, or focus web results by country.<br/><br/>`include_domains` and `exclude_domains` cannot be used together. Each domain list is capped at 500 entries. `exclude_domains` also blocks the research agent from visiting pages on those domains during browsing. `boost_domains` gives matching domains a relative ranking boost without filtering out other domains. It can be combined with `exclude_domains` but cannot be combined with `include_domains`.                                                                             |
| `output_schema`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Dict[str, *Any*]                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Beta. Requests structured JSON output in output.content using a supported JSON Schema subset. Supported only with research_effort values standard, deep, and exhaustive. Sending output_schema with research_effort: "lite" returns 422.<br/><br/>Schema rules: Root must be a JSON object. Top-level anyOf is not allowed. Every object must define properties and set additionalProperties: false. Every property must be listed in required. Recursive schemas are not supported.<br/><br/>Limits: Max nesting depth 5, max total properties 100, max total enum values 500, max total schema string budget 25,000.                                                                                                 |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### Response

**[models.ResearchResponse](../../models/researchresponse.md)**

### Errors

| Error Type                              | Status Code                             | Content Type                            |
| --------------------------------------- | --------------------------------------- | --------------------------------------- |
| errors.ResearchUnauthorizedError        | 401                                     | application/json                        |
| errors.ResearchForbiddenError           | 403                                     | application/json                        |
| errors.ResearchUnprocessableEntityError | 422                                     | application/json                        |
| errors.ResearchInternalServerError      | 500                                     | application/json                        |
| errors.YouDefaultError                  | 4XX, 5XX                                | \*/\*                                   |

## get_research_task

Poll the status of a background research task created with background=true. When the task is completed, the result is included in the response.

### Example Usage

<!-- UsageSnippet language="python" operationID="getResearchTask" method="get" path="/v1/research/{task_id}" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.get_research_task(task_id="586a9bc3-2c52-499c-a61d-be3cc9170c51")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `task_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | The UUID of the research task.                                      |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[models.TaskDetail](../../models/taskdetail.md)**

### Errors

| Error Type                                | Status Code                               | Content Type                              |
| ----------------------------------------- | ----------------------------------------- | ----------------------------------------- |
| errors.GetResearchTaskUnauthorizedError   | 401                                       | application/json                          |
| errors.GetResearchTaskForbiddenError      | 403                                       | application/json                          |
| errors.GetResearchTaskNotFoundError       | 404                                       | application/json                          |
| errors.GetResearchTaskInternalServerError | 500                                       | application/json                          |
| errors.YouDefaultError                    | 4XX, 5XX                                  | \*/\*                                     |

## stream_research_task

Stream real-time updates for a background research task via Server-Sent Events (SSE). Supports reconnection via the from_id query parameter to replay missed events. The connection closes automatically when the task reaches a terminal state.

### Example Usage

<!-- UsageSnippet language="python" operationID="streamResearchTask" method="get" path="/v1/research/{task_id}/stream" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.stream_research_task(task_id="b431835b-e51d-453e-a623-25615ac31489", from_id=0)

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `task_id`                                                           | *str*                                                               | :heavy_check_mark:                                                  | The UUID of the research task.                                      |
| `from_id`                                                           | *Optional[int]*                                                     | :heavy_minus_sign:                                                  | Resume from a sequence number for reconnection.                     |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |

### Response

**[Union[eventstreaming.EventStream[models.ResearchTaskStreamEvent], eventstreaming.EventStreamAsync[models.ResearchTaskStreamEvent]]](../../models/researchtaskstreamevent.md)**

### Errors

| Error Type                                   | Status Code                                  | Content Type                                 |
| -------------------------------------------- | -------------------------------------------- | -------------------------------------------- |
| errors.StreamResearchTaskUnauthorizedError   | 401                                          | application/json                             |
| errors.StreamResearchTaskForbiddenError      | 403                                          | application/json                             |
| errors.StreamResearchTaskNotFoundError       | 404                                          | application/json                             |
| errors.StreamResearchTaskInternalServerError | 500                                          | application/json                             |
| errors.YouDefaultError                       | 4XX, 5XX                                     | \*/\*                                        |

## finance_research

The Finance Research API is purpose-built for financial questions. Like the Research API, it runs multiple searches, reads through sources, and synthesizes everything into a thorough, well-cited answer — but its retrieval index is optimized for financial data: earnings reports, SEC filings, analyst coverage, market data, and financial news.
Use it when you need credible, sourced answers to financial questions: company fundamentals, market trends, competitive analysis, earnings summaries, or macroeconomic research.

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="authFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: authorizationFailure

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="authorizationFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: invalidEnum

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="invalidEnum" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: invalidJson

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="invalidJson" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: invalidOrExpired

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="invalidOrExpired" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: missingApiKey

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="missingApiKey" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: missingField

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="missingField" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: missingScopes

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="missingScopes" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: otherAuthParsing

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="otherAuthParsing" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```
### Example Usage: stringTooLong

<!-- UsageSnippet language="python" operationID="finance_research" method="post" path="/v1/finance_research" example="stringTooLong" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.finance_research(input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?", research_effort=models.FinanceResearchEffort.DEEP)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | Example                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | *str*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | :heavy_check_mark:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | The financial research question or complex query requiring in-depth investigation and multi-step reasoning.<br/><br/>Note: The maximum length of the input is 40,000 characters.                                                                                                                                                                                                                                                                                                                                                                                                                        | What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `research_effort`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | [Optional[models.FinanceResearchEffort]](../../models/financeresearcheffort.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Controls how much time and effort the Finance Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.<br/><br/>Available levels:<br/>- `lite`: Returns answers quickly. Good for straightforward financial questions that just need a fast, reliable answer.<br/>- `deep`: The default. Spends more time researching and cross-referencing sources. Good for most financial questions, including multi-company comparisons, earnings analysis, and regulatory research.<br/>- `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex financial research tasks where you want the highest quality result. | deep                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |

### Response

**[models.FinanceResearchResponse](../../models/financeresearchresponse.md)**

### Errors

| Error Type                                     | Status Code                                    | Content Type                                   |
| ---------------------------------------------- | ---------------------------------------------- | ---------------------------------------------- |
| errors.FinanceResearchUnauthorizedError        | 401                                            | application/json                               |
| errors.FinanceResearchForbiddenError           | 403                                            | application/json                               |
| errors.FinanceResearchUnprocessableEntityError | 422                                            | application/json                               |
| errors.FinanceResearchInternalServerError      | 500                                            | application/json                               |
| errors.YouDefaultError                         | 4XX, 5XX                                       | \*/\*                                          |