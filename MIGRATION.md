# Migration Guide: 1.x to 2.0

This guide helps you upgrade your code from You.com Python SDK 1.x to 2.0.

## Quick Reference

| Change | Find | Replace With |
|--------|------|--------------|
| Import path | `from youdotcom.types.typesafe_models import` | `from youdotcom.models import` |
| Express agent | `agent=AgentType.EXPRESS` | `request=ExpressAgentRunsRequest(...)` |
| Advanced agent | `agent=AgentType.ADVANCED` | `request=AdvancedAgentRunsRequest(...)` |
| Custom agent | `agent="uuid-string"` | `request=CustomAgentRunsRequest(agent="uuid-string", ...)` |
| Verbosity enum | `Verbosity` | `ReportVerbosity` |
| Format enum | `Format` | `ContentsFormat` |

## Step-by-Step Migration

### Step 1: Update Imports

**Before:**
```python
from youdotcom import You
from youdotcom.types.typesafe_models import (
    AgentType,
    SearchEffort,
    Verbosity,
    Country,
    Freshness,
    LiveCrawl,
    Format,
    get_text_tokens,
    stream_text_tokens,
)
```

**After:**
```python
from youdotcom import You
from youdotcom.models import (
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    CustomAgentRunsRequest,
    SearchEffort,
    ReportVerbosity,
    Country,
    Freshness,
    LiveCrawl,
    ContentsFormat,
    AgentRunsBatchResponse,
    # For streaming:
    ResponseCreated,
    ResponseStarting,
    ResponseOutputTextDelta,
    ResponseOutputContentFull,
    ResponseDone,
)
```

### Step 2: Update Agent Calls

#### Express Agent

**Before:**
```python
res = you.agents.runs.create(
    agent=AgentType.EXPRESS,
    input="What is the capital of France?",
    stream=False,
)
```

**After:**
```python
res = you.agents.runs.create(
    request=ExpressAgentRunsRequest(
        input="What is the capital of France?",
        stream=False,
    )
)
```

#### Advanced Agent

**Before:**
```python
res = you.agents.runs.create(
    agent=AgentType.ADVANCED,
    input="Research quantum computing",
    stream=False,
    tools=[
        ResearchTool(
            search_effort=SearchEffort.AUTO,
            report_verbosity=Verbosity.HIGH
        )
    ]
)
```

**After:**
```python
res = you.agents.runs.create(
    request=AdvancedAgentRunsRequest(
        input="Research quantum computing",
        stream=False,
        tools=[
            ResearchTool(
                search_effort=SearchEffort.AUTO,
                report_verbosity=ReportVerbosity.HIGH  # Note: Verbosity → ReportVerbosity
            )
        ]
    )
)
```

#### Custom Agent

**Before:**
```python
res = you.agents.runs.create(
    agent="your-custom-agent-uuid",
    input="Custom query",
    stream=False,
)
```

**After:**
```python
res = you.agents.runs.create(
    request=CustomAgentRunsRequest(
        agent="your-custom-agent-uuid",
        input="Custom query",
        stream=False,
    )
)
```

### Step 3: Update Response Handling

#### Batch (Non-Streaming) Responses

**Before:**
```python
res = you.agents.runs.create(agent=AgentType.EXPRESS, input="...", stream=False)
get_text_tokens(res)
```

**After:**
```python
res = you.agents.runs.create(
    request=ExpressAgentRunsRequest(input="...", stream=False)
)

if isinstance(res, AgentRunsBatchResponse):
    if res.output:
        for output in res.output:
            if output.text:
                print(output.text)
```

#### Streaming Responses

**Before:**
```python
res = you.agents.runs.create(agent=AgentType.EXPRESS, input="...", stream=True)
stream_text_tokens(res)
```

**After:**
```python
res = you.agents.runs.create(
    request=ExpressAgentRunsRequest(input="...", stream=True)
)

with res as stream:
    for chunk in stream:
        event = chunk.data
        
        if isinstance(event, ResponseOutputTextDelta):
            print(event.response.delta, end="", flush=True)
        
        elif isinstance(event, ResponseDone):
            print(f"\nDone in {event.response.run_time_ms}ms")
```

### Step 4: Update Contents API

**Before:**
```python
from youdotcom.types.typesafe_models import Format, print_contents

res = you.contents.generate(
    urls=["https://example.com"],
    format_=Format.MARKDOWN,
)
print_contents(res)
```

**After:**
```python
from youdotcom.models import ContentsFormat

res = you.contents.generate(
    urls=["https://example.com"],
    format_=ContentsFormat.MARKDOWN,
)
print(res)
```

### Step 5: Update Error Handling

**Before:**
```python
from youdotcom.errors import (
    PostV1AgentsRunsUnauthorizedError,
    GetV1SearchUnauthorizedError,
)
```

**After:**
```python
from youdotcom.errors import (
    AgentRuns401ResponseError,
    SearchUnauthorizedError,
)
```

## Search and Contents APIs

The Search and Contents APIs remain largely unchanged. The main differences are:

1. **Import path**: Use `from youdotcom.models import` instead of `typesafe_models`
2. **Format enum**: Use `ContentsFormat` instead of `Format`

```python
# Search API (unchanged usage)
res = you.search.unified(
    query="AI developments",
    count=10,
    freshness=Freshness.WEEK,
    country=Country.US,
)

# Contents API (updated enum name)
res = you.contents.generate(
    urls=["https://example.com"],
    format_=ContentsFormat.MARKDOWN,  # Was: Format.MARKDOWN
)
```

## Need Help?

- See the [CHANGELOG.md](CHANGELOG.md) for complete details on all changes
- Check the [examples/](examples/) folder for working code samples
- Open an issue on [GitHub](https://github.com/youdotcom-oss/youdotcom-python-sdk) if you encounter problems
