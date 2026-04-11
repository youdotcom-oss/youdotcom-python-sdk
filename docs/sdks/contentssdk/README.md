# Contents

## Overview

### Available Operations

* [generate](#generate) - Returns the content of the web pages

## generate

Returns the HTML or Markdown of a target webpage.

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="authFailure" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: authorizationFailure

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="authorizationFailure" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: invalidOrExpired

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="invalidOrExpired" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingApiKey

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="missingApiKey" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingScopes

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="missingScopes" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: otherAuthParsing

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="otherAuthParsing" -->
```python
from youdotcom import You, models


with You() as you:

    res = you.contents.generate(x_api_key="<value>", urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormatsItems.HTML,
        models.ContentsFormatsItems.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                         | Type                                                                                                                                                              | Required                                                                                                                                                          | Description                                                                                                                                                       |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `x_api_key`                                                                                                                                                       | *str*                                                                                                                                                             | :heavy_check_mark:                                                                                                                                                | A unique API Key is required to authorize API access. [Get your API Key with free credits](https://you.com/platform).                                             |
| `urls`                                                                                                                                                            | List[*str*]                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                | Array of URLs to fetch the contents from.                                                                                                                         |
| `formats`                                                                                                                                                         | List[[models.ContentsFormatsItems](../../models/contentsformatsitems.md)]                                                                                         | :heavy_minus_sign:                                                                                                                                                | Array of content formats to return. All included formats are returned in the response. Include "metadata" to get JSON-LD and OpenGraph information, if available. |
| `crawl_timeout`                                                                                                                                                   | *Optional[int]*                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                | Maximum time in seconds to wait for page content. Must be between 1 and 60 seconds. Default is 10 seconds.                                                        |
| `retries`                                                                                                                                                         | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                  | :heavy_minus_sign:                                                                                                                                                | Configuration to override the default retry behavior of the client.                                                                                               |
| `server_url`                                                                                                                                                      | *Optional[str]*                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                | An optional server URL to use.                                                                                                                                    |

### Response

**[List[models.V1ContentsPostResponsesContentApplicationJSONSchemaItems]](../../models/.md)**

### Errors

| Error Type                                | Status Code                               | Content Type                              |
| ----------------------------------------- | ----------------------------------------- | ----------------------------------------- |
| errors.ContentsRequestUnauthorizedError   | 401                                       | application/json                          |
| errors.ContentsRequestForbiddenError      | 403                                       | application/json                          |
| errors.ContentsRequestInternalServerError | 500                                       | application/json                          |
| errors.YouDefaultError                    | 4XX, 5XX                                  | \*/\*                                     |