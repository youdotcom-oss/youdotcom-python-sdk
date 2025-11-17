# Contents
(*contents*)

## Overview

### Available Operations

* [generate](#generate) - Returns the content of the web pages

## generate

Returns the content of the web pages

### Example Usage

<!-- UsageSnippet language="python" operationID="post_/v1/contents" method="post" path="/v1/contents" -->
```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], format_="html")

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `urls`                                                              | List[*str*]                                                         | :heavy_minus_sign:                                                  | Array of URLs to fetch the contents from.                           |                                                                     |
| `format_`                                                           | [Optional[models.Format]](../../models/format_.md)                  | :heavy_minus_sign:                                                  | The format of the content to be returned.                           | html                                                                |
| `retries`                                                           | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md)    | :heavy_minus_sign:                                                  | Configuration to override the default retry behavior of the client. |                                                                     |
| `server_url`                                                        | *Optional[str]*                                                     | :heavy_minus_sign:                                                  | An optional server URL to use.                                      | http://localhost:8080                                               |

### Response

**[List[models.PostV1ContentsResponse]](../../models/.md)**

### Errors

| Error Type                               | Status Code                              | Content Type                             |
| ---------------------------------------- | ---------------------------------------- | ---------------------------------------- |
| errors.PostV1ContentsUnauthorizedError   | 401                                      | application/json                         |
| errors.PostV1ContentsForbiddenError      | 403                                      | application/json                         |
| errors.PostV1ContentsInternalServerError | 500                                      | application/json                         |
| errors.YouDefaultError                   | 4XX, 5XX                                 | \*/\*                                    |