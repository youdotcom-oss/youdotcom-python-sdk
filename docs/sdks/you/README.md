# You SDK

## Overview

You.com API: Unified API for Express, Advanced, and Custom Agents from You.com
Get the best search results from web and news sources
Returns the HTML or Markdown of a target webpage
Multi-step reasoning with comprehensive research capabilities
Comprehensive API for You.com services:
- **Agents API**: Execute queries using Express, Advanced, and Custom AI agents
- **Search API**: Get search results from web and news sources
- **Contents API**: Retrieve and process web page content

### Available Operations

* [research](#research) - Returns comprehensive research-grade answers with multi-step reasoning

## research

Research goes beyond a single web search. In response to your question, it runs multiple searches, reads through the sources, and synthesizes everything into a thorough, well-cited answer. Use it when a question is too complex for a simple lookup, and when you need a response you can actually trust and verify.

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="research" method="post" path="/v1/research" example="authFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
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
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.research(input="<value>", research_effort=models.ResearchEffort.STANDARD)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | Type                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Required                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `input`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | *str*                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  | :heavy_check_mark:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | The research question or complex query requiring in-depth investigation and multi-step reasoning.<br/><br/>Note: The maximum length of the input is 40,000 characters.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `research_effort`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | [Optional[models.ResearchEffort]](../../models/researcheffort.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Controls how much time and effort the Research API spends on your question. Higher effort levels run more searches and dig deeper into sources, at the cost of a longer response time.<br/><br/>Available levels:<br/>- `lite`: Returns answers quickly. Good for straightforward questions that just need a fast, reliable answer.<br/>- `standard`: The default. Balances speed and depth, a good fit for most questions.<br/>- `deep`: Spends more time researching and cross-referencing sources. Use this when accuracy and thoroughness matter more than speed.<br/>- `exhaustive`: The most thorough option. Explores the topic as fully as possible, best suited for complex research tasks where you want the highest quality result. |
| `retries`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | Configuration to override the default retry behavior of the client.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

### Response

**[models.ResearchResponse](../../models/researchresponse.md)**

### Errors

| Error Type                         | Status Code                        | Content Type                       |
| ---------------------------------- | ---------------------------------- | ---------------------------------- |
| errors.ResearchUnauthorizedError   | 401                                | application/json                   |
| errors.ResearchForbiddenError      | 403                                | application/json                   |
| errors.UnprocessableEntityError    | 422                                | application/json                   |
| errors.ResearchInternalServerError | 500                                | application/json                   |
| errors.YouDefaultError             | 4XX, 5XX                           | \*/\*                              |