# ExtractError

An error returned by the Extract API (`402`, `422`, `500`, `502`, `503`, `504`). Every one shares the same body, so branch on `code`: it is stable, new codes may be added, and existing codes are never renamed or removed. `message` is for people and may be reworded.

`code`, `retryable`, and `request_id` are shortcuts for the same fields on `data.error`.

| Code | Status | Retryable | Meaning |
|------|--------|-----------|---------|
| `invalid_request` | 422 | No | The body failed validation. `details.fields` lists each problem. |
| `invalid_url` | 422 | No | The URL can never be fetched. `details.reason` is `malformed`, `unsupported_scheme`, `private_address`, or `unresolvable`. |
| `pdf_too_large` | 422 | No | The PDF needs more time than `timeout` allows; a higher `timeout` can let it through. |
| `payment_required` | 402 | No | The prepaid credit balance is depleted. `details.upgrade_url` is where to add credits. |
| `site_blocked` | 502 | No | The site does not allow its content to be extracted. |
| `site_unreachable` | 502 | No | The site could not be reached or loaded. |
| `unsupported_content` | 502 | No | The content at this URL cannot be extracted. |
| `timeout` | 504 | Yes | The request did not finish within `timeout`. Below 100, retry with a higher `timeout`. |
| `service_unavailable` | 503 | Yes | A dependency was down or rate limited. Honor the `Retry-After` header. |
| `internal_error` | 500 | Varies | Check `retryable`. |

The API gateway answers some `401`, `402`, and `403` responses before the request reaches the Extract API. Those raise `UnauthorizedResponseError`, `PaymentRequiredResponseError`, and `ForbiddenResponseError`.

## Example Usage

```python
import os
from youdotcom import You, errors

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    try:
        res = you.extract(url="https://example.com/large-report.pdf", timeout=30)
    except errors.ExtractError as e:
        if e.code == "pdf_too_large":
            # Raise the HTTP timeout too, or the client gives up before the API does
            res = you.extract(
                url="https://example.com/large-report.pdf", timeout=100, timeout_ms=110_000
            )
        else:
            print(e.code, e.retryable, e.request_id)
            raise
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data.error.code` | *str* | :heavy_check_mark: | Stable error code to branch on. |
| `data.error.message` | *Optional[str]* | :heavy_minus_sign: | Human-readable explanation. The wording can change, so don't parse it. |
| `data.error.retryable` | *Optional[bool]* | :heavy_minus_sign: | Whether sending the same request again can succeed. |
| `data.error.request_id` | *Optional[str]* | :heavy_minus_sign: | The You.com ID for this request. Include it when you contact support. |
| `data.error.details.fields` | Optional[List[ExtractErrorField]] | :heavy_minus_sign: | `invalid_request` only. One `field` and `message` per validation problem. |
| `data.error.details.reason` | *Optional[str]* | :heavy_minus_sign: | Cause of the error, for `invalid_url`, `site_blocked`, `site_unreachable`, and `unsupported_content`. |
| `data.error.details.content_type` | *Optional[str]* | :heavy_minus_sign: | `unsupported_content` only, when known. The content type of the page. |
| `data.error.details.timeout_s` | *Optional[int]* | :heavy_minus_sign: | `timeout` and `pdf_too_large` only. The timeout, in seconds, that applied to the request. |
| `data.error.details.page_count` | *Optional[int]* | :heavy_minus_sign: | `pdf_too_large` only, when known. The number of pages in the PDF. |
| `data.error.details.upgrade_url` | *Optional[str]* | :heavy_minus_sign: | `payment_required` only. Where to add credits. |
