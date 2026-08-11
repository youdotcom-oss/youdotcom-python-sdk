# Extraction

The `extraction` parameter on `POST /v1/search` controls how page content is attached to each result. It replaces the deprecated `livecrawl` / `livecrawl_formats` parameter pair. `extraction_mode` is required and selects between two modes:

- `"highlights"` — query-relevant excerpts land in `results.web[].contents.highlights`.
- `"full_page"` — full HTML and/or Markdown land in `results.web[].contents.html` / `.markdown`.

`extraction` cannot be combined with `livecrawl` or `livecrawl_formats`.

## Example Usage

```python
from youdotcom.models import Extraction, ExtractionMode

# Query-relevant excerpts in contents.highlights
res = you.search(
    query="latest quantum computing breakthroughs",
    extraction=Extraction(extraction_mode=ExtractionMode.HIGHLIGHTS),
)

# Full Markdown in contents.markdown
res = you.search(
    query="latest quantum computing breakthroughs",
    extraction={
        "extraction_mode": "full_page",
        "full_page": {"extraction_formats": ["markdown"]},
    },
)
```

## Fields

| Field             | Type                                              | Required                       | Description |
| ----------------- | ------------------------------------------------- | ------------------------------ | ----------- |
| `extraction_mode` | `"highlights"` \| `"full_page"`                   | :heavy_check_mark:             | Selects between excerpts and full page content. |
| `highlights`      | `{ max_tokens?: int (512-8192) }`                 | :heavy_minus_sign:             | Valid only when `extraction_mode == "highlights"`. |
| `full_page`       | `{ extraction_formats?: ["html" \| "markdown"] }` | :heavy_minus_sign:             | Valid only when `extraction_mode == "full_page"`. |
