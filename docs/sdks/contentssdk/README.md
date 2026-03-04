# Contents

## Overview

### Available Operations

* [generate](#generate) - Returns the content of the web pages

## generate

Returns the HTML or Markdown of a target webpage.

### Example Usage: authFailure

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="authFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: authorizationFailure

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="authorizationFailure" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: invalidOrExpired

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="invalidOrExpired" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingApiKey

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="missingApiKey" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: missingScopes

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="missingScopes" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```
### Example Usage: otherAuthParsing

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" example="otherAuthParsing" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], formats=[
        models.ContentsFormats.HTML,
        models.ContentsFormats.MARKDOWN,
    ], crawl_timeout=10)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                                                                                                                         | Type                                                                                                                                                              | Required                                                                                                                                                          | Description                                                                                                                                                       | Example                                                                                                                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `urls`                                                                                                                                                            | List[*str*]                                                                                                                                                       | :heavy_minus_sign:                                                                                                                                                | Array of URLs to fetch the contents from.                                                                                                                         |                                                                                                                                                                   |
| `formats`                                                                                                                                                         | List[[models.ContentsFormats](../../models/contentsformats.md)]                                                                                                   | :heavy_minus_sign:                                                                                                                                                | Array of content formats to return. All included formats are returned in the response. Include "metadata" to get JSON-LD and OpenGraph information, if available. | [<br/>"html",<br/>"markdown"<br/>]                                                                                                                                |
| `crawl_timeout`                                                                                                                                                   | *Optional[int]*                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                | Maximum time in seconds to wait for page content. Must be between 1 and 60 seconds. Default is 10 seconds.                                                        | 10                                                                                                                                                                |
| `retries`                                                                                                                                                         | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)                                                                                                  | :heavy_minus_sign:                                                                                                                                                | Configuration to override the default retry behavior of the client.                                                                                               |                                                                                                                                                                   |
| `server_url`                                                                                                                                                      | *Optional[str]*                                                                                                                                                   | :heavy_minus_sign:                                                                                                                                                | An optional server URL to use.                                                                                                                                    | http://localhost:8080                                                                                                                                             |

### Response

**[List[models.ContentsResponse]](../../models/.md)**

### Errors

| Error Type                         | Status Code                        | Content Type                       |
| ---------------------------------- | ---------------------------------- | ---------------------------------- |
| errors.ContentsUnauthorizedError   | 401                                | application/json                   |
| errors.ContentsForbiddenError      | 403                                | application/json                   |
| errors.ContentsInternalServerError | 500                                | application/json                   |
| errors.YouDefaultError             | 4XX, 5XX                           | \*/\*                              |