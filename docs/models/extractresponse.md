# ExtractResponse

The page `you.extract()` returns. When nothing could be extracted, the API returns an empty object and every field here is `None`.

Unknown fields are ignored, so fields the API adds later never break parsing.

## Example Usage

```python
import os
from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    res = you.extract(url="https://example.com")

    if res.contents and res.contents.full_page:
        print(res.title)
        print(res.contents.full_page.markdown)
    else:
        print("Nothing was extracted")
```

## Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `url` | *Optional[str]* | :heavy_minus_sign: | The URL whose content was extracted. |
| `extraction_source` | *Optional[str]* | :heavy_minus_sign: | Where the request allowed content to come from: `"blend"`, `"cache"`, or `"fetch"`. |
| `title` | *Optional[str]* | :heavy_minus_sign: | The title of the web page. |
| `contents` | [Optional[models.ExtractContents]](#extractcontents) | :heavy_minus_sign: | The extracted content from the URL. |
| `metadata` | [Optional[models.ExtractMetadata]](#extractmetadata) | :heavy_minus_sign: | Metadata about the web page. |

## ExtractContents

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_page` | [Optional[models.ExtractFullPageContents]](#extractfullpagecontents) | :heavy_minus_sign: | The page content in each format requested in `full_page.extraction_formats`. |

## ExtractFullPageContents

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `markdown` | *Optional[str]* | :heavy_minus_sign: | The Markdown content of the page. |
| `html` | *Optional[str]* | :heavy_minus_sign: | The HTML content of the page. |

## ExtractMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `site_name` | *Optional[str]* | :heavy_minus_sign: | The OpenGraph site name of the web page. |
| `favicon_url` | *Optional[str]* | :heavy_minus_sign: | The URL of the favicon of the web page's domain. |
