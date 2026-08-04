# Answer

## Overview

The Answer API returns a synthesized natural-language answer with citations and the web results used to generate it. Send a `query` with optional freshness, locale, and domain controls.

### Available Operations

* [create](#create) - Returns a synthesized answer with citations from web search results

## create

Returns a synthesized natural-language answer with citations and the web results used to generate it. Provide a `query` and optional freshness, locale, and domain controls.

### Example Usage

```python
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.answer.create(query="What are the main causes of the 2008 financial crisis?")

    # Handle response
    print(res.answer)
    for citation in res.citations:
        print(f"  [{citation.source}] {citation.excerpts[0]}")
```

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | *str* | :heavy_check_mark: | The search query. Max 400 characters. Search operators (`site:`, `OR`, etc.) are not supported. |
| `freshness` | *Optional[str]* | :heavy_minus_sign: | `day`, `week`, `month`, `year`, or `YYYY-MM-DDtoYYYY-MM-DD` |
| `country` | *Optional[str]* | :heavy_minus_sign: | Country code (e.g. `US`, `GB`, `FR`). Normalized to uppercase. |
| `language` | *Optional[str]* | :heavy_minus_sign: | BCP 47 language tag (e.g. `EN`, `EN-GB`, `FR`). Normalized to uppercase. |
| `include_domains` | *Optional[List[str]]* | :heavy_minus_sign: | Domains to exclusively include. Cannot combine with `exclude_domains` or `boost_domains`. Max 500. |
| `exclude_domains` | *Optional[List[str]]* | :heavy_minus_sign: | Domains to exclude. Cannot combine with `include_domains`. Can combine with `boost_domains`. Max 500. |
| `boost_domains` | *Optional[List[str]]* | :heavy_minus_sign: | Domains to prefer in ranking. Cannot combine with `include_domains`. Can combine with `exclude_domains`. Max 500. |
| `retries` | [Optional[utils.RetryConfig]](../../models/utils/retryconfig.md) | :heavy_minus_sign: | Configuration to override the default retry behavior of the client. |
| `server_url` | *Optional[str]* | :heavy_minus_sign: | An optional server URL to use. |
| `timeout_ms` | *Optional[int]* | :heavy_minus_sign: | Override the default request timeout in milliseconds. |
| `http_headers` | *Optional[Mapping[str, str]]* | :heavy_minus_sign: | Additional headers to set or replace on requests. |

### Response

**[models.AnswerResponse](../../models/answerresponse.md)**

### Errors

| Error Type | Status Code | Content Type |
|------------|-------------|-------------|
| errors.UnauthorizedResponseError | 401 | application/json |
| errors.PaymentRequiredResponseError | 402 | application/json |
| errors.ForbiddenResponseError | 403 | application/json |
| errors.UnprocessableEntityResponseError | 422 | application/json |
| errors.InternalServerErrorResponse | 500 | application/json |
| errors.YouDefaultError | 4XX, 5XX | \*/\* |
