<!-- Start SDK Example Usage [usage] -->
```python
# Synchronous Example
import os
from youdotcom import You


with You(
    api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
) as you:

    res = you.agents.runs.create(request={
        "agent": "express",
        "input": "What is the capital of France?",
        "stream": False,
    })

    with res as event_stream:
        for event in event_stream:
            # handle event
            print(event, flush=True)
```

</br>

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
import os
from youdotcom import You

async def main():

    async with You(
        api_key_auth=os.getenv("YOU_API_KEY_AUTH", ""),
    ) as you:

        res = await you.agents.runs.create_async(request={
            "agent": "express",
            "input": "What is the capital of France?",
            "stream": False,
        })

        async with res as event_stream:
            async for event in event_stream:
                # handle event
                print(event, flush=True)

asyncio.run(main())
```
<!-- End SDK Example Usage [usage] -->