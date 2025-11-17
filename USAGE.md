
> Tip: Additional examples can be found in the [examples](examples/) folder

### Example with Express agent

```python
# Synchronous Example with Express agent
from youdotcom import You
from youdotcom.types.typesafe_models import (
    AgentType,
    stream_text_tokens
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.agents.runs.create(
        agent=AgentType.EXPRESS,
        input="Teach me how to make an omelet",
        stream=True,
    )
    stream_text_tokens(res)

```

The same SDK client can also be used to make asynchronous requests by importing asyncio.

```python
# Asynchronous Example
import asyncio
from youdotcom import You
from youdotcom.types.typesafe_models import AgentType

async def main():
    async with You(
        api_key_auth="Your You.com API Key",
    ) as you:
        res = await you.agents.runs.create_async(
            agent=AgentType.EXPRESS,
            input="What is a Rain Frog?",
            stream=False,
        )

        async for event in res:
            # handle event
            print(event, flush=True)

asyncio.run(main())

```

### Example with Advanced agent and tools

```python
# Synchronous Example with Express agent
from youdotcom import You
from youdotcom.models import ComputeTool, ResearchTool
from youdotcom.types.typesafe_models import (
    AgentType,
    SearchEffort,
    Verbosity,
    get_text_tokens,
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.agents.runs.create(
            agent=AgentType.ADVANCED,
            input="Research and calculate the latest trends and the square root of 169. Show your work.",
            stream=False,
            tools=[
                ComputeTool(),
                ResearchTool(
                    search_effort=SearchEffort.AUTO,
                    report_verbosity=Verbosity.HIGH,
                ),
            ]
    ) 
    get_text_tokens(res)

```

### Example with Contents

```python
# Synchronous Example with the Contents API
from youdotcom import You
from youdotcom.types.typesafe_models import (
    Format,
    print_contents
)

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.contents.generate(
        urls=[
            "https://www.python.org",
            "https://www.example.com",
        ],
        format_=Format.HTML,
    )
    print_contents(res)

```

### Example with Search V1

```python
# Synchronous Example with the Search V1 API
from youdotcom import You
from youdotcom.types.typesafe_models import print_search

with You(
    api_key_auth="Your You.com API Key",
) as you:
    res = you.search.unified(
        query="latest AI developments",
    )
    print_search(res)
```
