# Migration Guide

## 3.1.1 → 3.1.2

> **Additive release.** No parameter is renamed, removed, or changed in
> meaning. Two changes can require an edit, and only in narrow cases.

### Action required

| Change | Who is affected | What to do |
|--------|-----------------|------------|
| Import machinery no longer re-exported from the package root | Anyone importing a stdlib/typing name or internal helper *from* `youdotcom` | Import it from its real home. See [Root namespace narrowing](#root-namespace-narrowing) |
| `ResearchTaskStreamEvent.event` is typed `Union[Event, str]` | Type-checked code calling `evt.event.value` | Guard with `isinstance(evt.event, Event)`. See [SSE event names](#sse-event-names) |

### Root namespace narrowing

`youdotcom/__init__.py` no longer does `from .sdk import *`, so the names
those statements pulled in transitively are no longer attributes of
`youdotcom`. This is what makes `import youdotcom` transport-free inside a
Temporal Workflow sandbox.

```python
# Before (3.1.1): worked by accident.
from youdotcom import httpx, Optional, eventstreaming

# After (3.1.2): ImportError. Import from the real module.
import httpx
from typing import Optional
from youdotcom.utils import eventstreaming
```

Everything documented still resolves from the root, including under
`from youdotcom import *`:

```python
from youdotcom import You, SDKConfiguration, RetryConfig, BackoffStrategy
from youdotcom import models, errors, utils, types
import youdotcom.sdk          # private submodules still import directly
```

### SSE event names

The `event` field on `ResearchTaskStreamEvent` accepts event names this SDK
version does not enumerate, so an added server-side event no longer raises
`ResponseValidationError`. Known names still resolve to `Event` members;
unknown names arrive as plain `str`. The declared type now says so, which
means an unguarded `.value` becomes a type error:

```python
# Type error on 3.1.2 -- and an AttributeError at runtime, on 3.1.1 too,
# the first time the server emits a name this SDK doesn't know.
print(evt.event.value)

# Guarded: correct on both versions.
if isinstance(evt.event, Event):
    print(evt.event.value)
else:
    print(evt.event)

# Comparing against raw strings needs no guard -- Event members are `str`.
if evt.event == "completed":
    ...
```

## 2.5.0 → 3.0.0

> **This release adds the Answer API, removes the Agents API, and makes `search()` a direct method on `You`.** The old sub-SDK patterns still work but emit `DeprecationWarning`. Migrate at your convenience.

### Action required

Most of this release is additive, but four changes can alter the behavior of
code that upgrades without edits:

| Change | Who is affected | What to do |
|--------|-----------------|------------|
| Agents API removed | Anyone calling `you.agents...` | Pin `youdotcom<3`, or call the REST endpoint directly |
| An empty API key now raises | Anyone using `os.getenv("YDC_API_KEY", "")` | Drop the `""` default. See [API key resolution](#api-key-resolution) |
| Context managers close both transports | Anyone mixing sync and async calls on one instance | Use one instance per flavor. See [Client lifecycle](#client-lifecycle) |
| `search(language=None)` no longer defaults to `EN` | Anyone passing `language=None` explicitly | Omit the argument to keep the `EN` default |

### API key resolution

`You(api_key_auth="")` now raises `ValueError` instead of quietly reading the
environment. Every You.com endpoint requires a key, so an empty string is never
a valid argument. It means a key was expected and none arrived:

```python
# Before (2.5.x): fell through to the YDC_API_KEY / YOU_API_KEY_AUTH lookup,
#                 so the request ran under whatever the environment held.
# After  (3.0.0): ValueError, naming the likely cause.
You(api_key_auth=os.getenv("YDC_API_KEY", ""))

# Correct in 3.0.0. None is how you ask for the environment lookup:
You(api_key_auth=os.getenv("YDC_API_KEY"))
```

The old fallback was worth removing because it could run a request under a
*different* identity than the code appeared to request, most visibly when
`YDC_API_KEY` is unset but the legacy `YOU_API_KEY_AUTH` is still set, or on
shared CI runners. This is a fail-fast change, not a new unauthenticated mode:
there is no way to call these endpoints without a key.

| `api_key_auth` value | Behavior |
| -------------------- | -------- |
| omitted, or `None` | Reads `YDC_API_KEY`, then the legacy `YOU_API_KEY_AUTH` |
| a non-empty string, or a callable returning one | That key is used; no environment lookup |
| `""` (or blank), or a callable returning an empty string | Raises `ValueError` |

A callable is resolved lazily, so a callable that returns an empty key raises
on first use rather than at construction.

### Client lifecycle

`You` creates both a sync and an async transport. Previously each context
manager closed only its own, leaking the other. Both now close both:

```python
with You(api_key_auth=key) as you:
    you.search(query="...")
# Both transports are now closed and dropped.
```

If you were relying on a single instance for both flavors, note that an
instance is unusable after either block exits, including for calls of the
other flavor:

```python
# Broken in 3.0.0:
with You(api_key_auth=key) as you:
    you.search(query="...")
await you.search_async(query="...")   # transports already closed

# Use `async with` for async work, or create a separate instance.
async with You(api_key_auth=key) as you:
    await you.search_async(query="...")
```

Transports you supply yourself (`You(client=...)`, `You(async_client=...)`)
are still never closed by the SDK. You remain responsible for them.

### Debug logging redacts credentials

If you attach a `debug_logger`, `Authorization`, `X-API-Key`, `Cookie`, and
`Set-Cookie` are now logged as `[REDACTED]`. Previously the API key appeared
in plaintext in those logs. No code change is needed; if you were parsing
debug output for header values, those four are no longer recoverable.

### `search(language=...)`

Omitting `language` still sends the API default (`EN`). Passing `None`
explicitly now means "send no language at all" instead of falling back to that
default:

```python
you.search(query="...")                  # language=EN (unchanged)
you.search(query="...", language="fr")   # language=FR (unchanged)
you.search(query="...", language=None)   # 2.5.x: EN  →  3.0.0: field omitted
```

### Answer API

New direct method `you.answer()` for `POST /v1/answer`:

```python
import os
from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY")) as you:
    res = you.answer(query="What causes the 2008 financial crisis?")
    print(res.answer)           # markdown with [[1, 2]] citations
    if res.citations:
        print(res.citations[0].source)  # source URL
    if res.results and res.results.web:
        print(res.results.web[0].title) # web result title
```

Requires an API key. `country` and `language` accept plain strings (e.g. `"us"`, `"en"`) and are normalized to uppercase.

### Search Moved to Direct Method

`you.search()` / `you.search_async()` target `POST /v1/search` on `ydc-index.io`. Search requires an API key.

The standalone `search_helpers` module has been removed. Its `search()` / `search_async()` functions are now direct methods on `You`:

```python
# Before (2.5.x): from youdotcom.search_helpers import search
# search(you, query="...")

# After (3.0.0):
you.search(query="...")
```

### Server URLs

`SEARCH_OP_SERVERS` and `CONTENTS_OP_SERVERS` point to `https://ydc-index.io` (used by `you.search()` and `you.contents()`). The default server URL (used by `you.answer()`, `you.research()`, `you.finance_research()`, etc.) is `https://api.you.com`. No code changes required. The SDK resolves the correct server per endpoint automatically. This behavior was already the case in 2.5.0; it is documented here for reference.

### Agents API Removed

The `you.agents()` / `you.agents_async()` direct methods and the `you.agents.runs` sub-SDK shim have been removed. The Agents API model classes (`ExpressAgentRunsRequest`, `AdvancedAgentRunsRequest`, `CustomAgentRunsRequest`, `AgentRunsBatchResponse`, etc.) have also been removed from `youdotcom.models`. If you need the Agents API, use the REST endpoint directly or a previous SDK version.

### PaymentRequiredResponseError

The `PaymentRequiredResponseError` exception (extends `YouError`) is raised by the answer API on HTTP 402. It provides structured data:

```python
import os
from youdotcom import You
from youdotcom.errors import PaymentRequiredResponseError

with You(api_key_auth=os.getenv("YDC_API_KEY")) as you:
    try:
        res = you.answer(query="test")  # may raise 402 if out of credits
    except PaymentRequiredResponseError as e:
        print(e.data.message)       # "Insufficient credits"
        print(e.data.upgrade_url)   # "https://you.com/platform"
        print(e.data.limit)         # 100
        print(e.data.reset_at)      # "2026-08-05T00:00:00Z"
```

### 422/500 Error Models Expanded

`UnprocessableEntityResponseErrorData` now includes optional `detail` (FastAPI validation array) and `errors` (JSON:API array) fields in addition to the existing `error` field. `InternalServerErrorResponseData` now includes an optional `errors` field. These are additive. Existing code accessing `.error` or `.detail` still works.

### No Longer Generated by Speakeasy

The SDK is now hand-maintained. All "Code generated by Speakeasy, DO NOT EDIT" disclaimers have been removed. The `__gen_version__` / `SPEAKEASY_GENERATOR_VERSION` exports have been removed.

### Sub-SDK Deprecation

The sub-SDK layer was an abstraction that added unnecessary indirection: `you.search.unified()` routed through extra layers before reaching the HTTP client. In 3.0.0 these chains are collapsed into direct methods on `You`. The new methods also have simpler signatures: `country`, `language`, `safesearch`, `livecrawl`, `livecrawl_formats`, and `freshness` accept plain strings in any case and are normalized to the casing the API expects, so callers no longer need to import enum classes:

| Parameter | Normalized to | Example |
|-----------|---------------|---------|
| `country`, `language` | uppercase | `"us"` → `"US"`, `"zh-hans"` → `"ZH-HANS"` |
| `safesearch`, `livecrawl`, `livecrawl_formats`, `freshness` | lowercase | `"STRICT"` → `"strict"`, `"2026-01-01TO2026-02-01"` → `"2026-01-01to2026-02-01"` |

Enum members (`Country.US`, `SafeSearch.STRICT`, …) continue to work unchanged.

The old patterns still work but emit `DeprecationWarning` and delegate to the new methods. Migrate at your convenience:

| Old (deprecated) | New |
|---------------|-----|
| `you.search.unified(query=...)` | `you.search(query=...)` |
| `you.search.unified_async(query=...)` | `you.search_async(query=...)` |
| `you.contents.generate(urls=...)` | `you.contents(urls=...)` |
| `you.contents.generate_async(urls=...)` | `you.contents_async(urls=...)` |

The `search_helpers` module has been removed; use `you.search(query=...)` directly. The `you.search_post()` alias has been removed; use `you.search()`.

To see deprecation warnings in your code:
```bash
python -W default::DeprecationWarning your_script.py
```

## 3.0.0 → 3.1.0

> **Recommended migration only — no code change required.** `livecrawl` and `livecrawl_formats` still work on `POST /v1/search` and now emit `DeprecationWarning`. Adopt `extraction` when convenient; removal is targeted for 4.0.0.

### Why migrate

`extraction` is a typed object with strict validation (`extra="forbid"`), so the SDK fails fast on unknown keys and wrong-mode couplings. `livecrawl` is stringly typed and only validates on the server. The new `extraction_mode="highlights"` also returns query-relevant excerpts in `contents.highlights` — closer to what most callers actually want — at a fraction of the tokens of `full_page`.

### Migration mapping

| Old | New |
|-----|-----|
| `livecrawl="web"` + `livecrawl_formats=["markdown"]` | `extraction={"extraction_mode": "full_page", "full_page": {"extraction_formats": ["markdown"]}}` |
| `livecrawl="all"` + `livecrawl_formats=["html", "markdown"]` | `extraction={"extraction_mode": "full_page", "full_page": {"extraction_formats": ["html", "markdown"]}}` |
| `livecrawl="news"` + `livecrawl_formats=["markdown"]` | `extraction={"extraction_mode": "full_page", "full_page": {"extraction_formats": ["markdown"]}}` (now covers both web and news) |
| Omitting `livecrawl` (snippets only) | Omit `extraction` (default behavior unchanged), or `extraction={"extraction_mode": "highlights"}` to swap snippets for query-relevant excerpts at the same latency |

Notes:

- `livecrawl` supported `"web"`, `"news"`, `"all"` modes. `extraction_mode` does not have a per-section switch — `"highlights"` and `"full_page"` apply to all sections in the response.

### Before / after

```python
import os

from youdotcom import You
from youdotcom.models import (
    Extraction,
    ExtractionFormat,
    ExtractionMode,
    LiveCrawl,
    LiveCrawlFormats,
)

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    # Before (3.0.x): livecrawl + formats
    you.search(
        query="quantum computing tutorials",
        count=5,
        livecrawl=LiveCrawl.WEB,
        livecrawl_formats=[LiveCrawlFormats.MARKDOWN],
    )

    # After (3.1.0): extraction
    you.search(
        query="quantum computing tutorials",
        count=5,
        extraction=Extraction(
            extraction_mode=ExtractionMode.FULL_PAGE,
            full_page={"extraction_formats": [ExtractionFormat.MARKDOWN]},
        ),
    )

    # Or as a plain dict (the SDK normalizes at the method layer)
    you.search(
        query="quantum computing tutorials",
        count=5,
        extraction={
            "extraction_mode": "full_page",
            "full_page": {"extraction_formats": ["markdown"]},
        },
    )
```

### Highlights mode (new option that didn't exist with livecrawl)

```python
import os

from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    res = you.search(
        query="how does X relate to Y",
        extraction={"extraction_mode": "highlights"},
    )
# Returns res.results.web[i].contents.highlights (List[str]) -- excerpts
# that match the query, not whole pages. Snippets are omitted in this mode.
```

### Conflict and plus-value rule

`extraction` cannot be combined with `livecrawl` or `livecrawl_formats` (raises `ValueError` locally before round-tripping). And top-level `crawl_timeout` is invalid alongside `extraction_mode="highlights"` — the SDK strips `crawl_timeout` from the request body in that case (default silently, with `UserWarning` if you set a non-default value).

### No upgrade-time action required

Calls using `livecrawl` / `livecrawl_formats` continue to work, just with a `DeprecationWarning`:

```python
import os
import warnings

from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        you.search(
            query="...",
            livecrawl="web",
            livecrawl_formats=["markdown"],
        )
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        # str(deprecations[0].message) == "livecrawl is deprecated; use extraction instead"
```


## 2.4.0 → 2.5.0

### New `frontier` Research Effort Tier

A new `ResearchEffort.FRONTIER` enum value has been added for the highest-quality, longest-running research tasks. Frontier runs over longer durations (up to 4 hours) with improved quality and accuracy.

**Key constraint:** `frontier` only works with the task-based API (`background=true`). Sending `frontier` without `background=true` returns a `422`.

```python
from youdotcom import You
from youdotcom.models import ResearchEffort
from youdotcom.research_helpers import research_and_wait

you = You()

# Submit a frontier task with background mode and wait for completion
detail = research_and_wait(
    you,
    input="Evaluate the measurable global-health impact of the Gates Foundation",
    research_effort=ResearchEffort.FRONTIER,
    timeout_s=14400,  # frontier tasks can run up to 4 hours
)
print(detail.result.model_dump()["output"]["content"])
```

You can also use the lower-level helpers for manual polling or streaming:

```python
from youdotcom import You
from youdotcom.models import ResearchEffort
from youdotcom.research_helpers import research_background, poll_research_task

you = You()

task = research_background(
    you,
    input="Evaluate the measurable global-health impact of the Gates Foundation",
    research_effort=ResearchEffort.FRONTIER,
)
detail = poll_research_task(you, task_id=task.task_id, timeout_s=14400)
```

No migration is required for existing code. The `frontier` tier is purely additive; existing `LITE`, `STANDARD`, `DEEP`, and `EXHAUSTIVE` values are unchanged.

### New Background Mode for Research

The `you.research()` method now accepts `background=True` to queue long-running research tasks asynchronously. The return type changes from `ResearchResponse` to `Union[ResearchResponse, TaskResponse]` (exposed as the `ResearchResult` alias).

**Synchronous mode (default, unchanged):**

```python
from youdotcom import You
from youdotcom.models import ResearchEffort, ResearchResponse

you = You()
res = you.research(input="...", research_effort=ResearchEffort.DEEP)
# res is ResearchResponse, same as 2.4.0
assert isinstance(res, ResearchResponse)
```

**Background mode (new):**

```python
from youdotcom import You
from youdotcom.models import ResearchEffort, TaskResponse, TaskDetail

you = You()

# Submit and get a task handle
res = you.research(input="...", research_effort=ResearchEffort.DEEP, background=True)
assert isinstance(res, TaskResponse)
print(res.task_id, res.stream_url)

# Poll for completion
detail = you.get_research_task(task_id=res.task_id)
if detail.status.value == "completed":
    payload = detail.result.model_dump()  # extra="allow" preserves the full ResearchResponse
    print(payload["output"]["content"])

# Or stream events with the tolerant helper (recommended)
from youdotcom.research_helpers import stream_research
for event in stream_research(you, task_id=res.task_id):
    print(event.event, event.data)
    if event.event in ("response.done", "complete", "completed", "error", "failed", "cancelled"):
        break
```

**Or use the convenience helpers:**

```python
from youdotcom import You
from youdotcom.models import ResearchEffort
from youdotcom.research_helpers import (
    research_background, poll_research_task, research_and_wait,
    stream_research,
)

you = You()

# Option 1: Submit and wait in one call (simplest)
# Streams SSE events until the task completes, then fetches the result.
# If the stream times out or closes without a terminal event, a final
# get_research_task call resolves the status (returns the detail if
# completed, raises RuntimeError for terminal non-completed, or
# TimeoutError if still running).
detail = research_and_wait(
    you, input="...", research_effort=ResearchEffort.DEEP,
)

# Option 2: Submit, then poll manually
task = research_background(you, input="...", research_effort=ResearchEffort.DEEP)
detail = poll_research_task(you, task_id=task.task_id)

# Option 3: Stream SSE events with a tolerant decoder
# (see the note below on choosing between this and
# you.stream_research_task)
for event in stream_research(you, task_id=task.task_id):
    print(event.event, event.data)
    if event.event in ("response.done", "complete", "completed"):
        break
    if event.event in ("error", "failed", "cancelled"):
        break
```

> **Note on streaming (as written for 2.5.0):** The generated
> `you.stream_research_task()` method uses a strict pydantic decoder that
> validates event names against a fixed `Event` enum. The server emits
> intermediate workflow events (e.g. `response.created`, `response.starting`,
> `response.output_item.added`) that are not in this enum, which causes
> `ResponseValidationError` on the first intermediate event. The
> `stream_research()` helper uses a tolerant decoder that surfaces unknown
> event names instead of crashing. For real research tasks, prefer
> `stream_research()`. (It yields `RawStreamEvent` objects, not raw dicts as
> originally written here; `.event` is a `str` and `.data` is the parsed JSON
> payload.)
>
> **Updated in 3.1.2 — the `ResponseValidationError` half of this no longer
> applies.** `Event` is now an open enum and the field is typed
> `EventName` (`Union[Event, str]`), so `you.stream_research_task()` decodes
> unenumerated event names as plain `str` instead of raising. The three event
> names above are covered by a regression test. See "3.1.1 → 3.1.2" above.
>
> `stream_research()` still differs in which frames it surfaces:
> `stream_research_task()` drops data-less frames (a bare `event: ping`
> heartbeat, or one carrying only `id:`/`retry:`) and requires every frame to
> carry an `id` and a JSON-object `data`, whereas `stream_research()` yields
> them and tolerates a `data` payload that is not valid JSON. If you only
> needed unknown-event tolerance, either method now works.

### Polling and Timeout Guidance

The `poll_research_task` helper polls `GET /v1/research/{task_id}` at a configurable interval until the task reaches a terminal state. The `research_and_wait` helper streams SSE events and enforces a total wall-clock timeout. Both default sensibly for most effort tiers, but `frontier` tasks can run much longer.

**`research_and_wait` auto-adjusts `timeout_s` based on `research_effort`** when you don't pass an explicit value:

| `research_effort` | Auto `timeout_s` | Typical latency |
|-------------------|-------------------|-----------------|
| `lite`            | 600s (10 min)     | seconds         |
| `standard`        | 600s (10 min)     | 30-120s         |
| `deep`            | 600s (10 min)     | 120-300s        |
| `exhaustive`      | 600s (10 min)     | 300-600s        |
| `frontier`        | 14400s (4 hours)  | 300s - 4 hours  |

**`poll_research_task` does not auto-adjust** (it receives a `task_id`, not the effort level). You must set `timeout_s` explicitly for frontier:

```python
from youdotcom import You
from youdotcom.models import ResearchEffort
from youdotcom.research_helpers import research_background, poll_research_task

you = You()

task = research_background(
    you, input="...", research_effort=ResearchEffort.FRONTIER,
)
# poll_research_task defaults: interval_s=2.0, timeout_s=600.0
# Override for frontier:
detail = poll_research_task(
    you, task_id=task.task_id,
    interval_s=5.0,    # less aggressive for long-running tasks
    timeout_s=14400,   # 4 hours
)
```

### No Breaking Changes for Existing Code

If you do not use `background=True`, your existing `you.research()` calls are unchanged at runtime. The return is still `ResearchResponse` when `background` is omitted or `False`.

> **Type-level note for statically-typed callers:** The return type of `you.research()` widened from `ResearchResponse` to `Union[ResearchResponse, TaskResponse]`. If your code accesses `res.output` directly (or passes the result where a `ResearchResponse` is expected), `mypy`/`pyright` will flag it because `TaskResponse` has no `output` field. Add an `isinstance(res, ResearchResponse)` narrow or use `cast(ResearchResponse, res)` to satisfy type checkers. This only affects type checking, not runtime behavior.

## 2.3.0 → 2.4.0

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

`ResearchEffort` keeps the name `ResearchEffort` and values `LITE`, `STANDARD`, `DEEP`, `EXHAUSTIVE`. No migration is required. The OpenAPI spec was promoted to a named schema so the SDK preserves the clean name.

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
# Content is now Union[str, Dict[str, Any]]. When content_type is
# "object" the structured payload round-trips as a plain dict.
print(res.output.content)
# {'same_entity': True, 'confidence': 0.95, 'evidence': [...]}
print(res.output.content["same_entity"])  # True
```

Code that does `res.output.content.lower()` or similar string-only operations will still work for typical text responses (the value remains a `str`), but if you opt into `output_schema` you must branch on `content_type` before calling string methods.

#### Environment variable renamed to `YDC_API_KEY`

The SDK now reads `YDC_API_KEY` (canonical per `you.com/docs`) instead of `YOU_API_KEY_AUTH` for API key authentication. `YOU_API_KEY_AUTH` is still accepted as a fallback, so existing 2.3.x users do not need to change anything immediately. Update your environment to use the canonical name when convenient:

```bash
# Before (2.3.x)
export YOU_API_KEY_AUTH="your-api-key"

# After (2.4.0), preferred
export YDC_API_KEY="your-api-key"
# YOU_API_KEY_AUTH still works as a fallback
```

#### `WebResult.authors` field removed

The `authors` field has been removed from `WebResult` (it was always optional and never documented). Code that accesses `result.authors` will now raise `AttributeError`.

### Optional Migrations Worth Adopting

#### Adopt new typed error names

The catch surface for Research has shifted from bare-class names to per-endpoint classes:

```python
# Before (2.3.x)
from youdotcom.errors import UnprocessableEntityError

# After (2.4.0): prefer per-endpoint
from youdotcom.errors import (
    ResearchUnprocessableEntityError,  # research-specific
    FinanceResearchUnprocessableEntityError,  # new
    YouError,  # safety net, catches every SDK-raised error
)

try:
    you.research(input="")
except ResearchUnprocessableEntityError as e:
    ...
except YouError as e:
    ...
```

The bare `UnprocessableEntityError` / `SearchUnauthorizedError` / `SearchForbiddenError` names are gone.

**Note on the catch-all base class.** Use `errors.YouError`, not `errors.YouDefaultError`, as your catch-all. The typed `*UnauthorizedError`, `*ForbiddenError`, `*UnprocessableEntityError`, and every per-endpoint typed error class extend `YouError` directly rather than `YouDefaultError`. A bare `except YouDefaultError` block will silently miss these. (Catching on `(TypedError, YouDefaultError)` tuples still works as long as the typed class is also listed.) Code that catches on `YouError` or on `(SomeError, YouError)` tuples is unaffected.

### New APIs to Try

- `you.finance_research(input=..., research_effort=FinanceResearchEffort.DEEP)`: finance-optimized index.

- `you.research(..., source_control={...})`: restrict / boost / exclude domains or filter by recency or country.
- `you.research(..., output_schema={...})`: structured JSON output.
- `you.search(..., boost_domains=[...])` (POST takes a list) or `you.search.unified(..., boost_domains="nytimes.com,wired.com")` (deprecated shim, takes a single comma-separated string): boost (but don't restrict) matching domains in ranking.
- `you.contents.generate(..., max_age=86400)`: require cached content younger than 24 hours.

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

> **Note:** If you are upgrading to 3.0.0+, the Agents API (`you.agents.runs.create()`) and all agent model classes (`ExpressAgentRunsRequest`, `AdvancedAgentRunsRequest`, `CustomAgentRunsRequest`, `AgentRunsBatchResponse`, `ResponseCreated`, `ResponseStarting`, `ResponseOutputTextDelta`, `ResponseOutputContentFull`, `ResponseDone`, `ReportVerbosity`, `SearchEffort`, `AgentRuns401ResponseError`, etc.) have been removed entirely. The migration steps below that reference agent imports and calls are no longer valid. See the [2.5.0 to 3.0.0](#250--300) section above. The Search and Contents API changes below still apply.

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
