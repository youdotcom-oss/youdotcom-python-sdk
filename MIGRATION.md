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
| Format enum | `Format` | `ContentsFormats` |
| Contents format param | `format_=Format.X` | `formats=[ContentsFormats.X]` |

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
    ContentsFormats,  # Note: Now plural (formats array)
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

The Contents API has significant changes in 2.0.0:
- **`format_`** parameter is replaced by **`formats`** (an array)
- New **`metadata`** format option returns json+ld and OpenGraph information
- New **`crawl_timeout`** parameter (1-60 seconds) for controlling crawl duration

**Before (1.x):**
```python
from youdotcom.types.typesafe_models import Format, print_contents

res = you.contents.generate(
    urls=["https://example.com"],
    format_=Format.MARKDOWN,
)
print_contents(res)
```

**After (2.0):**
```python
from youdotcom.models import ContentsFormats

# Single format
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.MARKDOWN],
)

# Multiple formats at once (new in 2.0.0)
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN, ContentsFormats.METADATA],
    crawl_timeout=30,  # Optional: 1-60 seconds
)

# Access metadata (json+ld, OpenGraph info)
for item in res:
    print(f"URL: {item.url}")
    print(f"Title: {item.title}")
    if item.metadata:
        print(f"Site Name: {item.metadata.site_name}")
        print(f"Favicon: {item.metadata.favicon_url}")
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

The Search API remains largely unchanged. The Contents API has significant changes:

1. **Import path**: Use `from youdotcom.models import` instead of `typesafe_models`
2. **Format parameter**: Changed from `format_` (single value) to `formats` (array)
3. **Format enum**: Use `ContentsFormats` instead of `Format` (note the 's')
4. **New metadata format**: Request `ContentsFormats.METADATA` to get json+ld and OpenGraph info
5. **New crawl_timeout**: Optional parameter (1-60 seconds) to control crawl duration

```python
# Search API (unchanged usage)
res = you.search.unified(
    query="AI developments",
    count=10,
    freshness=Freshness.WEEK,
    country=Country.US,
)

# Contents API (updated to use formats array)
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.MARKDOWN],  # Was: format_=Format.MARKDOWN
)

# Contents API with multiple formats and metadata (new in 2.0.0)
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.HTML, ContentsFormats.METADATA],
    crawl_timeout=30,  # Optional: 1-60 seconds
)
# Access metadata
if res[0].metadata:
    print(res[0].metadata.site_name)
    print(res[0].metadata.favicon_url)
```

## Need Help?

- See the [CHANGELOG.md](CHANGELOG.md) for complete details on all changes
- Check the [examples/](examples/) folder for working code samples
- Open an issue on [GitHub](https://github.com/youdotcom-oss/youdotcom-python-sdk) if you encounter problems
