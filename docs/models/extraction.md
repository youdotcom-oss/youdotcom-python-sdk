# Extraction

The `extraction` parameter on `POST /v1/search` controls how page content is attached to each result. It replaces the deprecated `livecrawl` / `livecrawl_formats` parameter pair. `extraction_mode` is required and selects between two modes:

- `"highlights"` — query-relevant excerpts land in `results.web[].contents.highlights`.
- `"full_page"` — full HTML and/or Markdown land in `results.web[].contents.html` / `.markdown`.

`extraction` cannot be combined with `livecrawl` or `livecrawl_formats`.

With `extraction_mode="highlights"`, the optional `highlights` object carries
two token caps: `max_tokens_per_url` bounds each result's highlights (512–8192)
and `total_max_tokens` bounds the whole response (1024–8192). Both are optional
— omit them for the provider's defaults — and out-of-range values raise
`ValidationError` locally, mirroring the server's 422.

With `extraction_mode="full_page"`, the optional `extraction_source` field
selects where the content comes from:

- `"blend"` (the default when unset) — serves cached content when it is
  available and crawls the page live when it is not.
- `"cache"` — returns cached content only; `contents` is omitted for results
  that have no cached content.
- `"fetch"` — always crawls the page live, returning the freshest content at
  the cost of higher latency.

Setting `extraction_source` alongside `extraction_mode="highlights"` raises
`ValidationError` locally, mirroring the server's 422.

## Example Usage

```python
import os
from youdotcom import You
from youdotcom.models import Extraction, ExtractionFormat, ExtractionMode, ExtractionSource

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    # Query-relevant excerpts in contents.highlights
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(extraction_mode=ExtractionMode.HIGHLIGHTS),
    )

    # Per-URL and whole-response highlight caps
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction={
            "extraction_mode": "highlights",
            "highlights": {"max_tokens_per_url": 1024, "total_max_tokens": 4096},
        },
    )

    # Full Markdown in contents.markdown, always crawled live
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(
            extraction_mode=ExtractionMode.FULL_PAGE,
            extraction_source=ExtractionSource.FETCH,
            full_page={"extraction_formats": [ExtractionFormat.MARKDOWN]},
        ),
    )
```

You can also pass a dict matching `ExtractionTypedDict`; the SDK
normalizes at the method layer.

## Fields

| Field               | Type                                              | Required                       | Description |
| ------------------- | ------------------------------------------------- | ------------------------------ | ----------- |
| `extraction_mode`   | `"highlights"` \| `"full_page"`                   | :heavy_check_mark:             | Selects between excerpts and full page content. |
| `extraction_source` | `"blend"` \| `"cache"` \| `"fetch"`               | :heavy_minus_sign:             | Where `full_page` content comes from. Defaults to `"blend"`. Valid only with `extraction_mode="full_page"`. |
| `highlights`        | `{ max_tokens_per_url?: *int* (512–8192), total_max_tokens?: *int* (1024–8192) }` | :heavy_minus_sign:             | Optional container for `extraction_mode == "highlights"`. Both caps are optional; out-of-range values and unknown keys here raise `ValidationError`. |
| `full_page`         | `{ extraction_formats?: ["html" \| "markdown"] }` | :heavy_minus_sign:             | Valid only when `extraction_mode == "full_page"`. |
