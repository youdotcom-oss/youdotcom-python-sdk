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
from youdotcom import You
from youdotcom.models import Extraction, ExtractionFormat, ExtractionMode


with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    timeout_ms=60_000,
) as you:

    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(
            extraction_mode=ExtractionMode.FULL_PAGE,
            full_page={"extraction_formats": [ExtractionFormat.MARKDOWN]},
        ),
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

With `extraction_mode="full_page"`, the optional `extraction_source` field
selects where the content comes from: `"blend"` (the default) serves cached
content when available and crawls the page live otherwise, `"cache"` returns
cached content only (`contents` is omitted for results with none), and
`"fetch"` always crawls the page live. Setting `extraction_source` alongside
`extraction_mode="highlights"` raises `ValidationError` locally.

Unknown keys inside `extraction` raise `ValidationError` locally, and passing
`extraction` together with `livecrawl` / `livecrawl_formats` raises
`ValueError` — both mirror the server's 422 contract so callers fail-fast.
<!-- End SDK Example Usage [extraction] -->

<!-- Start SDK Example Usage [knowledge] -->
```python
# Add knowledge cards backed by licensed data providers.
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    timeout_ms=60_000,
) as you:

    res = you.search(
        query="what is the capital of France",
        knowledge="core",
    )

    for card in res.results.knowledge or []:
        print(card.title, card.description)
        print([credit.name for credit in card.attribution])
```

`knowledge="core"` requests knowledge results — cards backed by licensed data
providers such as encyclopedias, market-data firms, and reference publishers.
`"core"` is the only value the API accepts; anything else raises
`ValidationError` locally, mirroring the server's 422.

Results are limited to those relevant to the query, up to 25. When none are
relevant the API omits the section, so `results.knowledge` is `None` rather
than an empty list — iterate with `or []`. `count` caps the web and news
sections, not knowledge.

Each card carries `type`, `title`, and `attribution`; for `type: answer` — the
only kind returned today — `description` is present and `as_of` is an optional
`YYYY-MM-DD` date covering the card's underlying data. `type` is a plain
string so an unrecognized kind parses rather than raises; ignore a value you
do not recognize. Attribution entries are credits rather than citations: each
names a provider and carries no URL.
<!-- End SDK Example Usage [knowledge] -->

<!-- Start SDK Example Usage [attribution] -->
```python
# Tag every outbound request with a caller-identity header so the
# analytics layer can split SDK traffic from MCP traffic.
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    app_name="acme-bot",
    app_version="2.4.0",
    app_title="Acme Bot",
    app_url="https://acme.example",
    timeout_ms=60_000,
) as you:

    res = you.search(query="What did OpenAI announce this week?")

    # Handle response
    print(res)
```

`X-Client-Info` sent on the wire:

```
sdk; client=acme-bot/2.4.0; title=Acme Bot; url=https://acme.example; ua=python/<V> httpx/<V>
```

`app_name`, `app_version`, `app_title` and `app_url` are all optional and
keyword-only. When omitted, those segments are dropped entirely, so an
undeclared caller sends just `sdk; ua=python/<V> httpx/<V>`. Values must be printable ASCII excluding `;`, and `app_name` / `app_version`
additionally exclude `/` since they are joined as `<name>/<version>`. Passing
`app_version` without `app_name` is also an error. Invalid
values raise `ValueError` at construction time.
<!-- End SDK Example Usage [attribution] -->