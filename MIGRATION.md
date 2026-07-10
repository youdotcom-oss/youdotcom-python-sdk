# Migration Guide

## 2.3.0 → 2.4.0 (Latest)

This guide covers breaking changes introduced in 2.4.0. If you are upgrading from 1.x or 2.0, also read the [1.x → 2.0](#1x-to-20) section below.

### Breaking Changes in 2.4.0

#### New `FinanceResearchEffort` enum

The Finance Research API has its own effort enum (`DEEP`, `EXHAUSTIVE`) distinct from the Research API's `ResearchEffort` enum (which is unchanged):

```python
# Research API (unchanged from 2.3.x)
from youdotcom.models import ResearchEffort
you.research(input="...", research_effort=ResearchEffort.DEEP)

# New in 2.4.0: Finance Research API
from youdotcom.models import FinanceResearchEffort
you.finance_research(input="...", research_effort=FinanceResearchEffort.DEEP)
```

`ResearchEffort` keeps the name `ResearchEffort` and values `LITE`, `STANDARD`, `DEEP`, `EXHAUSTIVE`. No migration is required — the OpenAPI spec was promoted to a named schema so the SDK preserves the clean name.

#### `livecrawl_formats` now requires a list

`livecrawl_formats` on the Search API is now strictly typed as `Optional[List[LiveCrawlFormats]]`. Passing a single enum value (silently coerced in earlier versions) raises a `ValidationError` at request time. Wrap the value in a list:

```python
# Before (2.3.x): single value was accepted
you.search.unified(
    query="...",
    livecrawl=LiveCrawl.WEB,
    livecrawl_formats=LiveCrawlFormats.MARKDOWN,
)

# After (2.4.0): must be a list
you.search.unified(
    query="...",
    livecrawl=LiveCrawl.WEB,
    livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
)
```

If you request multiple formats, the list form is the only available form:

```python
you.search.unified(
    query="...",
    livecrawl=LiveCrawl.WEB,
    livecrawl_formats=[LiveCrawlFormats.HTML, LiveCrawlFormats.MARKDOWN],
)
```

#### Research response is now `Union[ResearchResponse, TaskResponse]`

`you.research()` now returns either `ResearchResponse` (the inline answer, default) or `TaskResponse` (a task handle) depending on the `background` parameter. Code that asserts `isinstance(res, ResearchResponse)` still works for synchronous research, but be aware that:

```python
# Synchronous (unchanged behaviour)
res = you.research(input="...", research_effort=ResearchEffort.STANDARD)
assert isinstance(res, ResearchResponse)  # still True

# New: background-mode returns a TaskResponse
res = you.research(
    input="...",
    research_effort=ResearchEffort.DEEP,
    background=True,
)
assert isinstance(res, TaskResponse)
```

If you use `You` as a `TypedDict`-style client and only pass synchronous keyword arguments, this change is transparent.

#### Research `output.content` is now `Union[str, object]`

`output.content` is now `Union[str, object]` instead of always `str`. Plain research responses still return a Markdown `str` (with `content_type="text"`). Only when you supply `output_schema=...` does the SDK deserialize `output.content` as a structured JSON object matching your schema (with `content_type="object"`).

```python
res = you.research(
    input="Are Acme Logistics DE and Acme Logistics NJ the same entity?",
    output_schema={
        "type": "object",
        "properties": {
            "same_entity": {"type": "boolean"},
            "confidence": {"type": "number"},
            "evidence": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["same_entity", "confidence", "evidence"],
    },
)
assert res.output.content_type.value == "object"
# Caveat (2.4.0): the typed `Content` model declares no fields and uses
# pydantic's default `extra="ignore"`, so the JSON payload returned by the
# server is dropped at unmarshal time. `res.output.content` is an empty
# `Content()` instance rather than the structured dict. There is no
# SDK-level workaround for structured output in 2.4.0 — the fix is staged
# in `overlays/python_overlay.yaml` (`additionalProperties: true`) and will
# take effect on the next regeneration, after which `output.content` will
# round-trip the dict directly.
```

Code that does `res.output.content.lower()` or similar string-only operations will still work for typical text responses (the value remains a `str`), but if you opt into `output_schema` you must branch on `content_type` before calling string methods.

#### Environment variable renamed to `YDC_API_KEY`

The SDK now reads `YDC_API_KEY` (canonical per `you.com/docs`) instead of `YOU_API_KEY_AUTH` for API key authentication. `YOU_API_KEY_AUTH` is still accepted as a fallback, so existing 2.3.x users do not need to change anything immediately. Update your environment to use the canonical name when convenient:

```bash
# Before (2.3.x)
export YOU_API_KEY_AUTH="your-api-key"

# After (2.4.0) — preferred
export YDC_API_KEY="your-api-key"
# YOU_API_KEY_AUTH still works as a fallback
```

### Optional Migrations Worth Adopting

#### Use background mode for heavy research efforts

For `ResearchEffort.DEEP` and `EXHAUSTIVE` calls, prefer background mode + polling or streaming to avoid client-side timeouts:

```python
# Recommended for long-running research
res = you.research(
    input="deep, multi-source question...",
    research_effort=ResearchEffort.EXHAUSTIVE,
    background=True,
)

while True:
    status = you.get_research_task(task_id=res.task_id)
    if status.status.value == "completed":
        break
    time.sleep(5)
```

#### Adopt new typed error names

The catch surface for Research has shifted from bare-class names to per-endpoint classes:

```python
# Before (2.3.x)
from youdotcom.errors import UnprocessableEntityError

# After (2.4.0): prefer per-endpoint
from youdotcom.errors import (
    ResearchUnprocessableEntityError,  # research-specific
    FinanceResearchUnprocessableEntityError,  # new
    YouDefaultError,  # safety net
)

try:
    you.research(input="")
except ResearchUnprocessableEntityError as e:
    ...
except YouDefaultError as e:
    ...
```

The bare `UnprocessableEntityError` / `SearchUnauthorizedError` / `SearchForbiddenError` names are gone. Code that catches on `YouDefaultError` or on `(SomeError, YouDefaultError)` tuples is unaffected.

### New APIs to Try

- `you.finance_research(input=..., research_effort=FinanceResearchEffort.DEEP)` — finance-optimized index.
- `you.research(..., background=True)` + `you.get_research_task(task_id)` / `you.stream_research_task(task_id)` — long-running research with poll/stream.
- `you.research(..., source_control={...})` — restrict / boost / exclude domains or filter by recency or country.
- `you.research(..., output_schema={...})` — structured JSON output.
- `you.search_post(..., boost_domains=[...])` (POST takes a list) or `you.search.unified(..., boost_domains="nytimes.com,wired.com")` (GET takes a single comma-separated string) — boost (but don't restrict) matching domains in ranking.
- `you.contents.generate(..., max_age=86400)` — require cached content younger than 24 hours.

---

## 1.x → 2.3.0

This guide covers breaking changes introduced in 2.3.0. If you are upgrading from 1.x, also read the [1.x → 2.0](#1x-to-20) section below.

### Breaking Changes in 2.3.0

#### Python 3.10 now required

The minimum supported Python version has been raised from `>=3.9.2` to `>=3.10`. If you are running Python 3.9, you must upgrade before installing this version.

```bash
python --version   # must be 3.10 or later
pip install "youdotcom>=2.3.0"
```

#### Search API: `count` default changed

`you.search.unified()` now defaults `count` to `10` (previously `None`/no default). If your code omits `count` and relies on the API-server default, you will now always receive 10 results.

```python
# Before (2.x < 2.3.0): count was unset, server decided
res = you.search.unified(query="AI news")

# After (2.3.0+): equivalent explicit call
res = you.search.unified(query="AI news", count=10)
```

#### Contents API: `crawl_timeout` type changed

`crawl_timeout` has changed from `float` to `int`. Passing a float (e.g., `crawl_timeout=5.5`) will now raise a validation error.

```python
# Before: float was accepted
res = you.contents.generate(urls=["https://example.com"], crawl_timeout=5.5)

# After: use int
res = you.contents.generate(urls=["https://example.com"], crawl_timeout=5)
```

---

## 1.x to 2.0

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
