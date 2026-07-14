<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YDC_API_KEY", ""),
) as you:

    res = you.search_post(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, include_domains=[
        "nytimes.com",
        "bbc.com",
    ], exclude_domains=[
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
        api_key_auth=os.getenv("YDC_API_KEY", ""),
    ) as you:

        res = await you.search_post_async(query="What are the latest geopolitical updates from India", count=10, language=models.Language.EN, include_domains=[
            "nytimes.com",
            "bbc.com",
        ], exclude_domains=[
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