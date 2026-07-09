# Changelog

All notable changes to the You.com Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-07-09

### Added

- **Finance Research API**: New `you.finance_research()` method on the main `You` client. The Finance Research API searches a finance-optimized index — SEC filings, earnings transcripts, analyst coverage, market data, and financial news — instead of the open web. Use it for earnings analysis, due diligence, and market research.

```python
from youdotcom import You
from youdotcom.models import FinanceResearchEffort

you = You()
res = you.finance_research(
    input="What were the key drivers of NVIDIA's revenue growth in fiscal year 2025?",
    research_effort=FinanceResearchEffort.DEEP,
)
print(res.output.content)
for source in res.output.sources:
    print(f"  - {source.title or 'Untitled'}: {source.url}")
```

- **Research background mode**: New optional `background` parameter on `you.research()` and `you.research_async()`. When `True`, the request is queued as a task and a `TaskResponse` is returned immediately instead of blocking for the inline result. Use this for longer-running efforts (`deep`, `exhaustive`) that risk timeouts.

```python
res = you.research(
    input="Compare NVIDIA, AMD, and Intel profitability over 5 years",
    research_effort=ResearchEffort.DEEP,
    background=True,
)

assert isinstance(res, TaskResponse)
# poll or stream
status = you.get_research_task(task_id=res.task_id)
```

- **Research task polling**: New `you.get_research_task(task_id)` and `get_research_task_async(task_id)` for polling background research tasks. Returns a `TaskDetail` with the current `status` and, when `completed`, the full `result` matching the synchronous `ResearchResponse` shape.

- **Research SSE streaming**: New `you.stream_research_task(task_id)` and `stream_research_task_async(task_id)` for receiving real-time Server-Sent Events for a background task. Supports reconnection via `from_id=<seq>`. Event types: `connected`, `response.done` (terminal), `complete`, `error`, `cancelled`.

```python
with you.stream_research_task(task_id=task_id) as stream:
    for event in stream:
        data = event.data
        # handle connected / response.done / complete / error / cancelled
        ...
```

- **Research `source_control` (beta)**: New optional `source_control` object on `you.research()` for constraining the research agent's web sources. Supports `include_domains`, `exclude_domains`, `boost_domains`, `freshness`, and `country`. `include_domains` and `exclude_domains` cannot be combined (returns `422`); `boost_domains` combines with `exclude_domains` but not `include_domains`.

- **Research `output_schema` (beta)**: New optional `output_schema` object on `you.research()` for requesting structured JSON output in `output.content`. Response `content_type` becomes `"object"` and `output.content` is a structured dict matching the schema. Supported on `standard`, `deep`, and `exhaustive` effort levels (sending it with `lite` returns `422`).

- **Search API `boost_domains`**: New optional parameter on `you.search_post()` and on the underlying `you.search.unified()` (also accessible via `GET /v1/search`). Boost (but don't restrict) results from specified domains. Up to 500 domains per request. Cannot be combined with `include_domains`.

- **Contents API `max_age`**: New optional `max_age` parameter (integer seconds, ≥0, nullable) for controlling cache freshness. When set, cached content older than the threshold is ignored and the page is re-fetched. Default `null` (no age limit).

### Changed

- **`Research` API response is now `Union[ResearchResponse, TaskResponse]`**: The `POST /v1/research` 200 response is now a `oneOf` between inline `ResearchResponse` and the new `TaskResponse` returned when `background=True`. Update code that asserts on `isinstance(res, ResearchResponse)` to handle both shapes (or use type narrowing based on whether you passed `background=True`).

- **`Research.output.content` is now `Union[str, object]`**: When an `output_schema` is supplied, `output.content` is a structured JSON object (matching the schema) instead of a Markdown string. Check `output.content_type` to deserialise correctly: `text` → str, `object` → dict.

- **New `FinanceResearchEffort` enum**: The Finance Research API has its own effort enum (`DEEP`, `EXHAUSTIVE`) distinct from the Research API's `ResearchEffort`. Both have clean names — `ResearchEffort` is unchanged from 2.3.x.

- **Livecrawl formats parameter now requires a list**: The `livecrawl_formats` parameter is now strictly typed as `Optional[List[LiveCrawlFormats]]`. Passing a single enum value (which worked in prior versions) now raises a validation error. Wrap the value in a list:

```python
# Before (2.3.x)
you.search.unified(query="...", livecrawl_formats=LiveCrawlFormats.MARKDOWN)

# After (2.4.0)
you.search.unified(query="...", livecrawl_formats=[LiveCrawlFormats.MARKDOWN])
```

- **Consolidated error classes**: The shared `422`, `401`, `403` response shapes for Research and Search endpoints are now exposed as consolidated `UnprocessableEntityResponseError`, `UnauthorizedResponseError`, and `ForbiddenResponseError` instead of per-endpoint `SearchUnprocessableEntityError` / `ResearchUnprocessableEntityError` etc. Per-endpoint typed errors (`ResearchUnauthorizedError`, `FinanceResearchUnprocessableEntityError`, etc.) are still available as the primary raise target, but the bare-from-spec names like `UnprocessableEntityError` and `SearchForbiddenError` are gone. Catch on either the per-endpoint class or `YouDefaultError` for backward compatibility.

- **Environment variable renamed to `YDC_API_KEY`**: The SDK now reads the `YDC_API_KEY` environment variable for API key authentication (canonical per `you.com/docs`). The previous `YOU_API_KEY_AUTH` is still accepted as a fallback for 2.3.x users upgrading without code changes. Set `YDC_API_KEY` in your environment and the SDK will pick it up automatically:

```bash
# Before (2.3.x)
export YOU_API_KEY_AUTH="your-api-key"

# After (2.4.0) — preferred
export YDC_API_KEY="your-api-key"
# YOU_API_KEY_AUTH still works as a fallback
```

### Notes

- The `unresearched` `ulow` effort level remains internal and is intentionally NOT exposed in the SDK — it is consolidated as internal routing on the server.
- `you.finance_research()` deliberately does not support `source_control` or `output_schema`. The Finance Research API runs against a finance-optimized index and returns Markdown-formatted answers only.
- Background-mode + SSE streaming endpoints are considered ahead-of-docs and may receive minor surface changes before being documented at `docs.you.com`. The Python SDK contract matches the server implementation (`background`, `GET /v1/research/{task_id}`, `GET /v1/research/{task_id}/stream`) as of this release.

### Hand-maintained additions (not regenerated)

These live in `src/youdotcom/research_helpers.py`, `src/youdotcom/_hooks/registration.py`, and parts of `src/youdotcom/utils/security.py` and are NOT regenerated by Speakeasy — future SDK regens will overwrite them. The next release MUST re-apply the hand-edits below (or move them into the overlay / `x-speakeasy-env-var` extension before regen) so they survive regeneration:

- **`security.py` env-var precedence**: `get_security_from_env` reads `YDC_API_KEY` first and falls back to `YOU_API_KEY_AUTH` for backward compatibility with the 2.3.x env-var name. Covered by `tests/test_security_env.py`. Future regens that drop the fallback will lose `2.3.x` users — re-apply the two-line `or` chain after regen, or move the precedence into the Speakeasy overlay.

- **`research_helpers` module**: New `youdotcom.research_helpers` with the following public helpers:
  - `research_background(client, **kwargs)` / `research_background_async`: Submit research with `background=True` and return a typed `TaskResponse` directly (no need to narrow `Union[ResearchResponse, TaskResponse]`).
  - `poll_research_task(client, task_id, *, interval_s, timeout_s)` / `poll_research_task_async`: Poll `GET /v1/research/{task_id}` until status reaches a terminal state (`completed`, `failed`, `cancelled`); raises `RuntimeError`/`TimeoutError` accordingly.
  - `research_and_wait(client, *, mode, **kwargs)` / `research_and_wait_async`: Submit + wait (poll or stream) until done, returning the final `TaskDetail`. Note: today's SDK unmarshals the `Result` model with `extra=ignore`, so the inline `ResearchResponse` is not typed through this path — `detail.result.model_dump()` returns an empty dict because the typed model has no schema-declared fields and pydantic drops the `output` data. The supported workaround is to issue a synchronous `client.research(..., background=False)` call with the same input once the task reaches `completed`.
  - `stream_research_events_raw(client, task_id)` / `stream_research_events_raw_async`: SSE iterator that yields `RawStreamEvent(id, event, data, retry)` and accepts event names outside the documented enum (`connected`/`response.done`/`complete`/`error`/`cancelled`). Use this in place of `client.stream_research_task(...)` when the server may emit intermediate workflow events (`research.searching`, etc.).

- **`YDCUserAgentOverrideHook` honors custom `user_agent`**: Previously the hook unconditionally rewrote `User-Agent` to `youdotcom-python-sdk/{sdk_version}`. Now it detects when `sdk_configuration.user_agent` has been overridden away from the speakeasy default (`speakeasy-sdk/python ...`) and passes the custom value through. Integrations (langchain-youdotcom, youdotcom-temporal, n8n-nodes-youdotcom) can now simply set `client.sdk_configuration.user_agent = "<integration>/<version>"` after construction instead of swapping hooks.

---

## [2.3.0] - 2026-02-27

### Added

- **Research API**: New `research()` and `research_async()` methods on the main `You` client for comprehensive, multi-step research answers with citations. The Research API goes beyond a single web search by running multiple searches, reading sources, and synthesizing thorough, well-cited answers.

```python
from youdotcom import You
from youdotcom.models import ResearchEffort

you = You()
res = you.research(
    input="What are the latest advances in quantum computing?",
    research_effort=ResearchEffort.DEEP,
)
print(res.output.content)
for source in res.output.sources:
    print(f"  - {source.title or 'Untitled'}: {source.url}")
```

- **`ResearchEffort` enum**: Controls depth of research (`lite`, `standard`, `deep`, `exhaustive`)
- **Research models**: `ResearchRequest`, `ResearchResponse`, `Output`, `Source`, `ContentType`
- **Research errors**: `ResearchUnauthorizedError`, `ResearchForbiddenError`, `ResearchInternalServerError`, `UnprocessableEntityError`
- **`AgentRuns400ResponseError`**: New error class for 400 Bad Request responses from the Agents API

### Changed

- **Default server URL**: Changed from `https://ydc-index.io` to `https://api.you.com`. If you were relying on the default, no action needed as both resolve to the same API.
- **Python version requirement**: Now requires Python >=3.10 (previously >=3.9.2)
- **Search API `count` parameter**: Now defaults to `10` instead of `None`
- **Contents API `crawl_timeout`**: Type changed from `float` to `int`, default is now `10` seconds
- **Speakeasy generator**: Updated from v2.801.2 to v2.845.12

---

## [2.2.0] - 2026-01-29

### Changed

- **Renamed `SearchContents` to `Contents`**: The `SearchContents` model has been renamed to `Contents` and moved to its own module (`youdotcom.models.contents`). The interface remains the same with `html` and `markdown` fields.

### Added

- **News results now support `contents` field**: When using `livecrawl=NEWS` or `livecrawl=ALL`, news results can now include crawled page contents (HTML and/or Markdown), just like web results. This enables richer news content retrieval.

```python
from youdotcom.models import LiveCrawl, LiveCrawlFormats

# Get news with crawled contents
res = you.search.unified(
    query="technology news",
    livecrawl=LiveCrawl.NEWS,
    livecrawl_formats=LiveCrawlFormats.MARKDOWN,
)

for news_item in res.results.news:
    if news_item.contents:
        print(news_item.contents.markdown)
```

### Removed

- **`SearchContents`**: Replaced by `Contents`. If you were importing `SearchContents` directly, update your imports to use `Contents`.

---

## [2.0.0] - 2026-01-09

### Breaking Changes

#### Agents API: New Typed Request Pattern

The Agents API now uses typed request classes instead of the `AgentType` enum, providing better type safety, IDE autocompletion, and clearer intent.

**Before (1.x):**
```python
from youdotcom.types.typesafe_models import AgentType, SearchEffort, Verbosity

you.agents.runs.create(
    agent=AgentType.EXPRESS,
    input="What is the capital of France?",
    stream=False,
)

you.agents.runs.create(
    agent=AgentType.ADVANCED,
    input="Research quantum computing",
    stream=False,
    tools=[ResearchTool(search_effort=SearchEffort.AUTO, report_verbosity=Verbosity.HIGH)]
)

you.agents.runs.create(
    agent="your-custom-agent-uuid",
    input="Custom query",
    stream=False,
)
```

**After (2.0):**
```python
from youdotcom.models import (
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    CustomAgentRunsRequest,
    ResearchTool,
    SearchEffort,
    ReportVerbosity,
)

you.agents.runs.create(
    request=ExpressAgentRunsRequest(
        input="What is the capital of France?",
        stream=False,
    )
)

you.agents.runs.create(
    request=AdvancedAgentRunsRequest(
        input="Research quantum computing",
        stream=False,
        tools=[ResearchTool(search_effort=SearchEffort.AUTO, report_verbosity=ReportVerbosity.HIGH)]
    )
)

you.agents.runs.create(
    request=CustomAgentRunsRequest(
        agent="your-custom-agent-uuid",
        input="Custom query",
        stream=False,
    )
)
```

**Why this is better:**
- **Type safety**: Each agent type has its own request class with the appropriate fields
- **IDE support**: Better autocompletion since each request type only shows relevant options
- **Validation**: Invalid combinations are caught at development time, not runtime
- **Clarity**: The request type makes the intent explicit in the code

---

#### Model Imports Consolidated

All models are now imported from `youdotcom.models` instead of the separate `typesafe_models` module.

**Before (1.x):**
```python
from youdotcom.types.typesafe_models import (
    AgentType,
    SearchEffort,
    Verbosity,
    Country,
    Freshness,
    LiveCrawl,
    Format,
)
```

**After (2.0):**
```python
from youdotcom.models import (
    ExpressAgentRunsRequest,
    AdvancedAgentRunsRequest,
    SearchEffort,
    ReportVerbosity,
    Country,
    Freshness,
    LiveCrawl,
    ContentsFormat,
)
```

**Why this is better:**
- **Single import location**: All models in one place
- **Cleaner namespace**: No nested module paths
- **Better discoverability**: Easier to find available models

---

#### Renamed Models

| Old Name (1.x) | New Name (2.0) | Reason |
|----------------|----------------|--------|
| `Verbosity` | `ReportVerbosity` | More specific—clarifies it controls research report verbosity |
| `Format` | `ContentsFormats` | Avoids collision with Python's built-in `format()`, plural indicates array usage |
| `AgentType` | *Removed* | Replaced by typed request classes |

---

#### Contents API: New Formats Array Pattern

The Contents API now uses a `formats` array instead of a single `format_` parameter, allowing you to request multiple content types in a single call.

**Before (1.x):**
```python
res = you.contents.generate(
    urls=["https://example.com"],
    format_=Format.MARKDOWN,
)
```

**After (2.0):**
```python
from youdotcom.models import ContentsFormats

# Request single format
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.MARKDOWN],
)

# Request multiple formats at once
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.HTML, ContentsFormats.MARKDOWN, ContentsFormats.METADATA],
)
```

**Why this is better:**
- **Multiple formats**: Request HTML, Markdown, and Metadata in a single API call
- **Metadata support**: New `METADATA` format returns json+ld and OpenGraph information
- **Flexibility**: Get exactly the content types you need

---

#### Contents API: New Metadata Format

The new `METADATA` format returns structured metadata about web pages including json+ld and OpenGraph information.

```python
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.METADATA],
)

for item in res:
    if item.metadata:
        print(f"Site Name: {item.metadata.site_name}")
        print(f"Favicon: {item.metadata.favicon_url}")
```

---

#### Contents API: New crawl_timeout Parameter

A new optional `crawl_timeout` parameter allows you to control the maximum time (1-60 seconds) spent crawling each URL.

```python
res = you.contents.generate(
    urls=["https://example.com"],
    formats=[ContentsFormats.HTML],
    crawl_timeout=30,  # Wait up to 30 seconds per URL
)
```

---

#### Removed Helper Functions

The following helper functions have been removed in favor of working directly with typed response objects:

| Removed Function | Replacement |
|-----------------|-------------|
| `get_text_tokens(response)` | Access `response.output[0].text` directly |
| `stream_text_tokens(response)` | Iterate over streaming events (see example below) |
| `print_search(response)` | Access `response.results` and `response.metadata` directly |
| `print_contents(response)` | Access response contents directly |

**Why this is better:**
- **Full control**: Access all response fields, not just what helpers exposed
- **Type safety**: Response objects are fully typed for IDE support
- **Flexibility**: Handle responses exactly as your application needs

---

#### New Streaming Response Pattern

Streaming responses now use properly typed event classes for better handling.

**Before (1.x):**
```python
res = you.agents.runs.create(agent=AgentType.EXPRESS, input="...", stream=True)
stream_text_tokens(res)  # Helper function handled everything
```

**After (2.0):**
```python
from youdotcom.models import (
    ResponseCreated,
    ResponseStarting,
    ResponseOutputTextDelta,
    ResponseOutputContentFull,
    ResponseDone,
)

response = you.agents.runs.create(
    request=ExpressAgentRunsRequest(input="...", stream=True)
)

with response as stream:
    for chunk in stream:
        event = chunk.data
        
        if isinstance(event, ResponseCreated):
            print(f"Started: {event.seq_id}")
        
        elif isinstance(event, ResponseOutputTextDelta):
            print(event.response.delta, end="", flush=True)
        
        elif isinstance(event, ResponseOutputContentFull):
            # Handle web search results, etc.
            for result in event.response.full:
                print(f"Source: {result.url}")
        
        elif isinstance(event, ResponseDone):
            print(f"\nCompleted in {event.response.run_time_ms}ms")
```

**Why this is better:**
- **Granular control**: Handle each event type appropriately
- **Type safety**: Each event type has typed fields
- **Rich metadata**: Access timing, sequence IDs, and intermediate results

---

#### Error Class Renames

Error classes have been renamed for consistency and clarity:

| Old Name (1.x) | New Name (2.0) |
|----------------|----------------|
| `PostV1AgentsRunsUnauthorizedError` | `AgentRuns401ResponseError` |
| `PostV1AgentsRunsForbiddenError` | Removed (403 now handled by `YouDefaultError`) |
| `GetV1SearchUnauthorizedError` | `SearchUnauthorizedError` |
| `GetV1SearchForbiddenError` | `SearchForbiddenError` |
| `PostV1ContentsUnauthorizedError` | `ContentsUnauthorizedError` |
| `PostV1ContentsForbiddenError` | `ContentsForbiddenError` |

**Why this is better:**
- **Readable names**: No HTTP method prefixes cluttering the name
- **Consistent pattern**: `{Operation}{StatusCode}Error` or `{Operation}{Description}Error`

---

### Added

- **`ExpressAgentRunsRequest`**: Typed request for Express agent calls
- **`AdvancedAgentRunsRequest`**: Typed request for Advanced agent calls  
- **`CustomAgentRunsRequest`**: Typed request for Custom agent calls (with UUID)
- **`AgentRunsBatchResponse`**: Typed response for non-streaming agent calls
- **`AgentRunsStreamingResponse`**: Typed response wrapper for streaming
- **Streaming event types**: `ResponseCreated`, `ResponseStarting`, `ResponseOutputItemAdded`, `ResponseOutputContentFull`, `ResponseOutputTextDelta`, `ResponseOutputItemDone`, `ResponseDone`
- **`ReportVerbosity`**: Enum for research tool report detail level
- **`ContentsFormats`**: Enum for contents API format selection (html, markdown, metadata)
- **`ContentsMetadata`**: Model for metadata response (site_name, favicon_url)
- **Contents API `formats` parameter**: Array of formats to request (replaces single `format_`)
- **Contents API `crawl_timeout` parameter**: Optional timeout (1-60 seconds) for URL crawling
- **Contents API `METADATA` format**: Returns json+ld and OpenGraph information

### Removed

- **`youdotcom.types.typesafe_models`** module - all models now in `youdotcom.models`
- **`AgentType`** enum - replaced by typed request classes
- **`Verbosity`** - renamed to `ReportVerbosity`
- **`Format`** - renamed to `ContentsFormats` (note the 's')
- **`format_` parameter** in Contents API - replaced by `formats` array
- **Helper functions**: `get_text_tokens()`, `stream_text_tokens()`, `print_search()`, `print_contents()`

---

## [1.4.1] - 2025-12-10

### Changed
- Updated search results to include `contents` field when livecrawl is enabled

## [1.4.0] - 2025-12-09

### Changed
- Renamed `request_uuid` to `search_uuid` in search metadata for consistency

## [1.3.0] - 2025-11-19

### Changed
- Version update for PyPI compatibility

## [1.0.0] - 2025-11-18

### Added
- Initial stable release
- Agents API with Express, Advanced, and Custom agents
- Search API with unified search endpoint
- Contents API for web page content retrieval
- Typesafe models for all API responses
- Streaming support via Server-Sent Events (SSE)
