<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
import os
from youdotcom import You, models


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.research(input="Which global cities improved air quality the most over the past 10 years, and what measurable actions contributed?", research_effort=models.ResearchEffort.LITE)

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
        api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
    ) as you:

        res = await you.research_async(input="Which global cities improved air quality the most over the past 10 years, and what measurable actions contributed?", research_effort=models.ResearchEffort.LITE)

        # Handle response
        print(res)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->