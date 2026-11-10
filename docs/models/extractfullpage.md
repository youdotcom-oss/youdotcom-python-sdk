# ExtractFullPage

Options for the page content `you.extract()` returns. Pass a dict or an `ExtractFullPage`; unknown keys raise `ValidationError` locally, mirroring the API's `422`.

## Example Usage

```python
import os
from youdotcom import You
from youdotcom.models import ExtractFullPage, ExtractionFormat

with You(api_key_auth=os.getenv("YDC_API_KEY")) as you:
    # Dict form
    res = you.extract(
        url="https://example.com",
        full_page={"extraction_formats": ["markdown", "html"]},
    )

    # Model form
    res = you.extract(
        url="https://example.com",
        full_page=ExtractFullPage(
            extraction_formats=[ExtractionFormat.MARKDOWN, ExtractionFormat.HTML]
        ),
    )
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `extraction_formats` | Optional[List[[models.ExtractionFormat](extraction.md)]] | :heavy_minus_sign: | Content formats to return, one or both of `"markdown"` and `"html"`. `["markdown"]` by default; an empty list is treated the same. |
