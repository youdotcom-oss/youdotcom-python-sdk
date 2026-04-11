<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
from youdotcom import You, models


with You() as you:

    res = you.unified(query="Your query", x_api_key="<value>", count=10, language=models.Language.EN, crawl_timeout=10)

    # Handle response
    print(res)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from youdotcom import You, models

async def main():

    async with You() as you:

        res = await you.unified_async(query="Your query", x_api_key="<value>", count=10, language=models.Language.EN, crawl_timeout=10)

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->