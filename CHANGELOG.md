# Changelog

All notable changes to the You.com Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
| `Format` | `ContentsFormat` | Avoids collision with Python's built-in `format()` |
| `AgentType` | *Removed* | Replaced by typed request classes |

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
| `PostV1AgentsRunsForbiddenError` | `AgentRuns422ResponseError` |
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
- **`ContentsFormat`**: Enum for contents API format selection

### Removed

- **`youdotcom.types.typesafe_models`** module - all models now in `youdotcom.models`
- **`AgentType`** enum - replaced by typed request classes
- **`Verbosity`** - renamed to `ReportVerbosity`
- **`Format`** - renamed to `ContentsFormat`
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
