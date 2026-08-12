# Extraction

The `extraction` parameter on `POST /v1/search` controls how page content is attached to each result. It replaces the deprecated `livecrawl` / `livecrawl_formats` parameter pair. `extraction_mode` is required and selects between two modes:

- `"highlights"` — query-relevant excerpts land in `results.web[].contents.highlights`.
- `"full_page"` — full HTML and/or Markdown land in `results.web[].contents.html` / `.markdown`.

`extraction` cannot be combined with `livecrawl` or `livecrawl_formats`.

## Example Usage

```python
import os
from youdotcom import You
from youdotcom.models import Extraction, ExtractionFormat, ExtractionMode

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    # Query-relevant excerpts in contents.highlights
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(extraction_mode=ExtractionMode.HIGHLIGHTS),
    )

    # Full Markdown in contents.markdown
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(
            extraction_mode=ExtractionMode.FULL_PAGE,
            full_page={"extraction_formats": [ExtractionFormat.MARKDOWN]},
        ),
    )
```

You can also pass a dict matching `ExtractionTypedDict`; the SDK
normalizes at the method layer.

## Fields

| Field             | Type                                              | Required                       | Description |
| ----------------- | ------------------------------------------------- | ------------------------------ | ----------- |
| `extraction_mode` | `"highlights"` \| `"full_page"`                   | :heavy_check_mark:             | Selects between excerpts and full page content. |
| `highlights`      | `{}`                                              | :heavy_minus_sign:             | Optional container for `extraction_mode == "highlights"`. Reserved for future sub-fields; unknown keys here raise `ValidationError`. |
| `full_page`       | `{ extraction_formats?: ["html" \| "markdown"] }` | :heavy_minus_sign:             | Valid only when `extraction_mode == "full_page"`. |
