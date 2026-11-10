# ExtractRequest

The `POST /v1/extract` request body that `you.extract()` builds from its arguments. You don't construct it yourself; pass the same fields to `you.extract()` as keyword arguments.

The request is strict: unknown keys and out-of-range values raise `ValidationError` locally, mirroring the API's `422`.

`extraction_source` accepts `"blend"`, `"cache"`, or `"fetch"` ([`models.ExtractionSource`](extraction.md)). `parse_effort` accepts `"lite"` or `"standard"` ([`models.ParseEffort`](parseeffort.md)). Both take plain strings in any case.

## Example Usage

```python
import os
from youdotcom import You
from youdotcom.models import ExtractionSource, ParseEffort

with You(api_key_auth=os.getenv("YDC_API_KEY")) as you:
    # Dict form
    res = you.extract(
        url="https://arxiv.org/pdf/2310.06825",
        extraction_source="fetch",
        parse_effort="lite",
        timeout=60,
    )

    # Enum form
    res = you.extract(
        url="https://arxiv.org/pdf/2310.06825",
        extraction_source=ExtractionSource.FETCH,
        parse_effort=ParseEffort.LITE,
        timeout=60,
    )
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | *str* | :heavy_check_mark: | The URL to extract content from. |
| `full_page` | [Optional[models.ExtractFullPage]](extractfullpage.md) | :heavy_minus_sign: | Options for the returned page content. Omit to return the page as Markdown. |
| `extraction_source` | [Optional[models.ExtractionSource]](extraction.md) | :heavy_minus_sign: | Where content comes from: `"blend"` (the default) serves cached content when it is available and crawls the page live when it is not, `"cache"` returns cached content only, and `"fetch"` always crawls the page live. |
| `timeout` | *Optional[int]* | :heavy_minus_sign: | Seconds the request may take end to end, including the cache lookup and the crawl. Must be between 2 and 100. Default is 30. Past it the request fails with a `timeout` error. |
| `parse_effort` | [Optional[models.ParseEffort]](parseeffort.md) | :heavy_minus_sign: | How much effort to spend parsing PDF pages; no effect on web pages. `"lite"` extracts the content embedded in each page and suits digitally created PDFs. `"standard"` (the default) also sends complex pages, such as charts and images, through an advanced model, and is billed per PDF page. |
