<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    timeout_ms=60_000,
) as you:

    res = you.search(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
        "spam-site.com",
        "other-site.com",
    ], boost_domains=[
        "nytimes.com",
        "wired.com",
    ], crawl_timeout=10)

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
import os
from youdotcom import You, models

async def main():

    async with You(
        api_key_auth=os.getenv("YDC_API_KEY"),
        timeout_ms=60_000,
    ) as you:

        res = await you.search_async(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, exclude_domains=[
            "spam-site.com",
            "other-site.com",
        ], boost_domains=[
            "nytimes.com",
            "wired.com",
        ], crawl_timeout=10)

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->

<!-- Start SDK Example Usage [extraction] -->
```python
# Attach full Markdown content to each result via the new `extraction` parameter.
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    timeout_ms=60_000,
) as you:

    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction={
            "extraction_mode": "full_page",
            "full_page": {"extraction_formats": ["markdown"]},
        },
    )

    for hit in res.results.web or []:
        print(hit.title, hit.url, hit.contents.markdown if hit.contents else None)
```

The `extraction` parameter replaces the deprecated `livecrawl` /
`livecrawl_formats` string pair. Pass an `Extraction` model, a dict matching
`ExtractionTypedDict`, or omit it for snippets-only behavior. Two modes:

- `extraction_mode="highlights"` — query-relevant excerpts land in
  `results.web[].contents.highlights`; snippets are omitted.
- `extraction_mode="full_page"` — return full HTML and/or Markdown in
  `results.web[].contents.html` / `.markdown` (default: `["markdown"]`).

Unknown keys inside `extraction` raise `ValidationError` locally, and passing
`extraction` together with `livecrawl` / `livecrawl_formats` raises
`ValueError` — both mirror the server's 422 contract so callers fail-fast.
<!-- End SDK Example Usage [extraction] -->