# Contents

## Overview

### Available Operations

* [generate](#generate) - Returns the content of the web pages

## generate

Returns the content of the web pages

### Example Usage

<!-- UsageSnippet language="python" operationID="contents" method="post" path="/v1/contents" -->
```python
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.contents.generate(urls=[
        "https://www.you.com",
    ], format_=models.ContentsFormat.HTML)

    # Handle response
    print(res)

```

### Parameters

| Parameter                                                           | Type                                                                | Required                                                            | Description                                                         | Example                                                             |
| ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `urls`                                                              | List[*str*]                                                         | :heavy_minus_sign:                                                  | Array of URLs to fetch the contents from.                           |                                                                     |
| `format_`                                                           | [Optional[models.ContentsFormat]](../../models/contentsformat.md)   | :heavy_minus_sign:                                                  | The format of the content to be returned.                           | html                                                                |
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