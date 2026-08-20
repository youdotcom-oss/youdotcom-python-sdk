# Changelog

All notable changes to the You.com Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.2] - 2026-08-20

Sister release track to the extraction-parameter rollout
(3.1.0 + 3.1.1). Every documented surface is backward-compatible; see
"Root namespace narrowing" below for the one exception, which affects
only names that were never part of the public API.

The top-level root surface now resolves lazily via PEP 562
``__getattr__``. `You`, `SDKConfiguration`, `BaseSDK`, `RetryConfig`,
`BackoffStrategy`, the `HttpClient` protocols, the logger and hook
helpers, and the `models` / `errors` / `utils` / `types` sub-packages
all still resolve from the package root, and all still bind under
`from youdotcom import *` — but each is imported on first access, so
``import youdotcom`` no longer pulls transport-layer modules into
``sys.modules``.

### Root namespace narrowing

Replacing the eager `from .sdk import *` / `from .sdkconfiguration
import *` also stops those statements from leaking their own imports
onto `youdotcom`. On 3.1.1 the package root carried 48 public names;
24 of them were import machinery rather than API, and are gone:

- stdlib and third-party modules the SDK imports internally: `httpx`,
  `asyncio`, `warnings`, `weakref`
- typing and dataclass helpers: `Any`, `Callable`, `Dict`, `Iterable`,
  `List`, `Mapping`, `Optional`, `Tuple`, `Union`, `cast`,
  `dataclass`, `field`
- internal plumbing: `eventstreaming`, `get_security_from_env`,
  `unmarshal_json_response`, `remove_suffix`
- private submodule aliases: `youdotcom.sdk`, `youdotcom.basesdk`,
  `youdotcom.httpclient`, `youdotcom.sdkconfiguration` (still
  importable directly, e.g. `import youdotcom.sdk`)

None were documented, exported deliberately, or referenced by any
example. The narrowing is intentional: re-exporting them is what
dragged `httpx` and `urllib.request` into every `import youdotcom`.
If you were relying on one, import it from its own module —
`from youdotcom.utils import eventstreaming`. See
`MIGRATION.md` ("3.1.1 → 3.1.2") for the before/after.

Going the other way, `BackoffStrategy` now resolves from the root
(`from youdotcom import BackoffStrategy`) alongside `RetryConfig`,
which it configures; on 3.1.1 only `RetryConfig` did.

`__version__`, `__title__`, `__user_agent__`, and
`__openapi_doc_version__` remain reachable as attributes
(`youdotcom.__version__`) and, as on 3.1.1, are deliberately **not**
bound by `from youdotcom import *`, so a star import cannot overwrite
a consumer package's own `__version__`.

### Fixed

- **Models are usable inside a Temporal Workflow.**
  `youdotcom/__init__.py` no longer eagerly pulls transport-layer
  modules (including `httpx` and `urllib.request`) into
  ``sys.modules``, so a Workflow module that does
  `from youdotcom.models import SearchResponse` (no
  `workflow.unsafe.imports_passed_through()` work-around) prepares
  cleanly under the default `SandboxedWorkflowRunner`. PEP 562 module
  `__getattr__` mirrors the public-import surface without dragging
  transport; the `models/__init__.py` lazy pattern shipped in 3.0.0 was
  lifted to the package root. Regression coverage lives in
  `tests/test_root_init.py` (subprocess assertion: `import youdotcom`
  does not load `httpx` / `urllib.request`).
- **`ResearchTaskStreamEvent.event` accepts future SSE event names.**
  `Event` now uses `OpenEnumMeta` so a server-side event-name addition
  (a new terminal status, a retry signal, anything the SDK does not
  yet enumerate) does not raise `ResponseValidationError` on the
  unmarshal path. Known event names still resolve to the `Event` enum
  member; unknown names unmarshal as plain `str` values that compare
  equal to their raw value, so callers branching on raw strings
  (`evt.event == "completed"`) keep working unchanged.
  Exhaustive-enumeration callers (`isinstance(evt.event, Event)`) get
  the right negative answer. Serialization produces no warnings.
  Coverage in `tests/test_researchtaskstreamevent.py`, including a
  regression test that drives the real `stream_research_task` SSE
  decode path with unknown event names.

  The field is declared `EventName` (a new public alias for
  `Union[Event, str]`, exported from `youdotcom.models`) because that
  is what it holds at runtime. **Typed callers may see a new type
  error:** `evt.event.value` no longer type-checks, since the value is
  a plain `str` for any event name this SDK version does not
  enumerate. That error is the bug surfacing rather than a new
  restriction — the same code raises `AttributeError` at runtime the
  first time the server emits a new name. Guard with
  `isinstance(evt.event, Event)` before using the enum API, or compare
  against raw strings, which needs no guard.

### Added

- **Attribution header `X-Client-Info` on every outbound request.**
  New optional `You(app_name=..., app_version=..., app_title=...,
  app_url=...)` constructor args identify the calling application. They are
  keyword-only, so later attribution args can be added without a breaking
  change; the existing positional parameters are untouched. Wire format:

      sdk[; client=<name>[/<version>]][; title=<title>][; url=<url>]; ua=python/<V> httpx/<V>

  so the analytics layer can distinguish SDK traffic from other
  sources. The leading `sdk` token names the channel, matching the `mcp` and
  `skill` tokens emitted elsewhere; the calling language stays recoverable
  from `ua=`, and the SDK's own version from the `User-Agent`. `client=`
  identifies the *caller* and is dropped entirely when `app_name` is unset,
  so an undeclared caller emits `sdk; ua=python/… httpx/…`. All four values
  must be printable ASCII excluding `;`, with `app_name` / `app_version` also
  excluding `/`; invalid values raise `ValueError` at construction time.
- **`safesearch` parameter on `You.answer()`.**
  The Answer API now supports the same explicit-content filtering
  as the Web Search API. New optional `safesearch` kwarg on
  `answer()` and `answer_async()` accepts ``off``, ``moderate``
  (default), or ``strict``. Case-insensitive, like the search
  counterpart. Existing call sites are unaffected.

## [3.1.1] - 2026-08-12

### Fixed

- **Stricter `extraction.highlights` contract.** The sub-object rejects
  unknown keys with `pydantic.ValidationError` before the request goes out,
  so callers cannot accidentally route an unsupported parameter to the
  server's strict `extraction` schema (`extra="forbid"` was already in
  place; the prior version allowed a small set of knobs that the server
  does not currently accept). Both the `Extraction` model instance form and
  the dict form are validated.

## [3.1.0] - 2026-08-10

Adds `extraction` on `POST /v1/search` and deprecates `livecrawl` /
`livecrawl_formats`. Sister track to the matching `extraction`-on-search
work in the API. No breaking changes.

### Added

- **`extraction` parameter** on `you.search()` / `you.search_async()` and the
  `SearchShim` forwarders. Accepts an `Extraction` model instance or a dict
  matching `ExtractionTypedDict`. Mirrors the locked schema from the docs
  preview at `youdotcom-docs` (`origin/add-extraction-parameter-to-search-api`):

  - `extraction_mode` (required): `"highlights"` (excerpts in
    `results.web[].contents.highlights`) or `"full_page"` (full HTML /
    Markdown in `results.web[].contents.html` / `.markdown`).
  - `extraction.full_page.extraction_formats` (optional; default
    `["markdown"]`).
  - Top-level `crawl_timeout` (1-60, default 10) remains on the request body,
    sibling to `extraction`.

- **`Extraction`, `ExtractionMode`, `ExtractionFormat`, `ExtractionHighlights`,
  `ExtractionFullPage`, `ExtractionTypedDict`, `ExtractionHighlightsTypedDict`,
  `ExtractionFullPageTypedDict`** exported from `youdotcom.models` for typed
  construction and IDE completion.

### Changed

- **`Extraction` model is strict** (`extra="forbid"`). Unknown keys anywhere
  inside `extraction` raise pydantic `ValidationError` locally, matching
  the server's 422 contract so callers fail-fast. The top-level
  `SearchRequestBody` keeps its existing `extra="ignore"` semantics.
- **Conflict check**: passing `extraction` together with `livecrawl` or
  `livecrawl_formats` raises `ValueError` locally, mirroring the server's
  conflict check.
- **Plus-value rule**: top-level `crawl_timeout` is stripped from the request body when
  `extraction.extraction_mode == "highlights"` (the server rejects the combination).
  Default callers are silent; setting a non-default `crawl_timeout` there emits
  `UserWarning` so the strip is not surprising.

### Deprecated

- **`livecrawl` and `livecrawl_formats`** on `you.search()` /
  `you.search_async()` and the `SearchShim` forwarders. Use `extraction`
  instead. They continue to work (the server still accepts them as
  undocumented internal params) but emit `DeprecationWarning`. Removal is
  targeted for 4.0.0, coordinated with the API+docs release that sunsets
  the internal params.

### Internal

- `SearchRequestBody.serialize_model` allowlist now includes `extraction`
  alongside `livecrawl`, `livecrawl_formats`, and `crawl_timeout` so the
  strict-extraction stream of changes flow through the existing serializer
  unchanged. The new `Extraction` model has its own `model_serializer`
  (`mode="wrap"`) drops `None` sub-objects so absent fields stay off the
  wire (`extraction_mode="full_page"` without `full_page=None`, etc.).

## [3.0.0] - 2026-08-06

This release removes the Agents API and the sub-SDK classes, which is a
breaking change and therefore a major version bump. Pin `youdotcom<3` if you
still depend on the Agents API.

### Removed

- **Agents API**: The `you.agents()` / `you.agents_async()` direct methods and the `you.agents.runs` sub-SDK shim have been removed. All Agents API model classes (`ExpressAgentRunsRequest`, `AdvancedAgentRunsRequest`, `CustomAgentRunsRequest`, `AgentRunsBatchResponse`, `AgentRunsResponseOutput`, `AgentRunsStreamingResponse`, `AgentRunsResponseWebSearchResult`, `ComputeTool`, `WebSearchTool`, `ResearchTool`, `ReportVerbosity`, `SearchEffort`, `Verbosity`, and streaming event models) and error classes (`AgentRuns400ResponseError`, `AgentRuns401ResponseError`, `AgentRuns422ResponseError`) have been deleted from `youdotcom.models` and `youdotcom.errors`.
- **`search_helpers` module**: The standalone `search_helpers.search()` function has been merged into `you.search()`. Import `from youdotcom import You` and call `you.search(query=...)` directly.
- **`you.search_post()`**: Use `you.search()`.
- **`__gen_version__` / `SPEAKEASY_GENERATOR_VERSION`**: These exports are gone from `youdotcom` and `youdotcom._version`. `__version__`, `__title__`, `__openapi_doc_version__`, and `__user_agent__` are unaffected.
- **`YDCUserAgentOverrideHook` and `_hooks/registration.py`**: The hook existed to rewrite Speakeasy's default UA (`speakeasy-sdk/python ...`) to `youdotcom-python-sdk/{version}`. Now that `__user_agent__` is already `youdotcom-python-sdk/{version}`, `BaseSDK._build_request` sets it directly, so the hook was a no-op. Integrations that need a custom UA still just set `client.sdk_configuration.user_agent`.
- **Dead code**: Unused `importlib` and `TYPE_CHECKING` imports from `sdk.py`, all remaining agent model/error classes and their doc files, and `overlays/python_overlay.yaml` (Speakeasy overlay, no longer used).

### Deprecations

- **Sub-SDK access patterns deprecated**: The sub-SDK layer added unnecessary indirection: `you.search.unified()` went through extra layers before reaching the HTTP client. The new direct methods (`you.search()`, `you.contents()`) collapse this chain into a single call on `You`, with simpler signatures that accept plain strings instead of enum imports. The old patterns still work but emit `DeprecationWarning` and delegate to the new methods. Migrate at your convenience:

| Old (deprecated) | New |
|---------------|-----|
| `you.search.unified(query=...)` | `you.search(query=...)` |
| `you.search.unified_async(query=...)` | `you.search_async(query=...)` |
| `you.contents.generate(urls=...)` | `you.contents(urls=...)` |
| `you.contents.generate_async(urls=...)` | `you.contents_async(urls=...)` |

### Added

- **Answer API**: New direct method `you.answer()` / `you.answer_async()` for `POST /v1/answer`. Returns a synthesized markdown answer with inline citations (`[[1, 2]]`), a citations array (source URLs + supporting excerpts), and web results. Accepts `query` (required), `freshness`, `country`, `language`, `include_domains`, `exclude_domains`, `boost_domains`. Requires an API key.
- **`PaymentRequiredResponseError`**: New first-class error class for HTTP 402 responses, with data model `PaymentRequiredResponseErrorData` (`error`, `message`, `upgrade_url`, `limit`, `used`, `period`, `reset_at`). Used by the answer 402 handler.
- **Case-insensitive enum parameters**: `country`, `language`, `safesearch`, `livecrawl`, `livecrawl_formats`, and `freshness` accept plain strings in any case and are normalized to the casing the API expects (`"us"` → `"US"`, `"STRICT"` → `"strict"`). Callers no longer need to import enum classes. Enum members still work.
- **SDK drift check** (`scripts/check_drift.py`): Compares the You.com OpenAPI specs against the SDK surface (endpoints, server URLs, enum values, request params, response fields). Runs non-blocking on every PR and weekly on a schedule, opening an issue when drift is found.

### Security

- **Debug-log redaction**: `Authorization`, `X-API-Key`, `Cookie`, and `Set-Cookie` are replaced with `[REDACTED]` before request/response headers are written to the debug logger, on both the sync and async paths.

  Debug logging is off by default (`get_default_logger()` returns a `NoOpLogger` unless `YOU_DEBUG` is set), so a default configuration was never affected. Callers who enabled debug output, via `YOU_DEBUG` or by passing their own `debug_logger`, previously had the API key written in plaintext to that logger's sink. If that applies to you and those logs left the host, rotate the key.

### Changed

- **An empty API key raises instead of falling back to the environment**: `You(api_key_auth="")`, a blank string, or a callable returning an empty string now raises `ValueError`. Every endpoint requires a key, so an empty string is never a valid argument; it means a key was expected and none arrived. Previously the SDK fell through to `YDC_API_KEY` / `YOU_API_KEY_AUTH`, which could run the request under a different identity than the code appeared to request. Passing `None` (or omitting the argument) remains the supported way to read the key from the environment.

  In practice this surfaces as `os.getenv("YDC_API_KEY", "")` with the variable unset; use `os.getenv("YDC_API_KEY")`. All documentation examples have been updated accordingly.
- **Both context managers now close both transports**: `__exit__` disposes of the SDK-owned async client in addition to the sync one, and `__aexit__` does the reverse. Previously whichever transport the block didn't use was leaked. As a consequence, an instance is no longer usable after leaving either block, including for calls of the other flavor: `with You(...) as you: ...` followed by `await you.search_async(...)` will fail. Create a separate client, or use `async with`, if you need both. Caller-supplied transports are still never closed by the SDK.
- **`search(language=None)` sends no language**: Omitting the argument uses the API default (`"EN"`) as before; passing `None` explicitly now omits the field entirely rather than falling back to the default.
- **422 error data model**: `UnprocessableEntityResponseErrorData` now includes optional `detail` (FastAPI validation array) and `errors` (JSON:API array) fields in addition to the existing `error` field. All three 422 response shapes deserialize without crashing. Backward compatible: existing code accessing `.error` still works.
- **500 error data model**: `InternalServerErrorResponseData` now includes an optional `errors` field for JSON:API format 500 responses. Backward compatible.
- **No longer generated by Speakeasy**: Removed all "Code generated by Speakeasy, DO NOT EDIT" disclaimers and the Speakeasy badge from the README. The SDK is now hand-maintained.
- **`__user_agent__` derived from resolved `__version__`**: The user-agent string is now built from the package's resolved version at runtime rather than a hardcoded value.
- **Dev dependencies updated**: mypy `1.15.0` → `>=2.3.0,<3`, pylint `3.2.3` → `>=4.0.0,<5`, pytest floor `>=8.0.0` → `>=9.0.0,<10`, pytest-asyncio floor `>=0.24.0` → `>=1.0.0,<2`. Runtime dependencies (httpx, httpcore, pydantic) unchanged, already at latest stable.
- **Added a `LICENSE` file**: the MIT license the README has always declared is now committed to the repository and bundled into the sdist and wheel.

### Fixed

- **`SDKConfiguration.retry_config` default**: The field used `pydantic.Field(default_factory=...)` on a stdlib `@dataclass`, which does not interpret a `FieldInfo` and left the raw object as the default. Now uses `dataclasses.field`.
- **`Security` serializer dropped the wrong key**: `serialize_model` listed `"ApiKeyAuth"` in `optional_fields`, but the field is named `api_key_auth`, so the name never matched and a `None` key was serialized instead of omitted.
- **`_populate_from_globals` name comparison**: Used `is not` to compare strings, which depends on interning and could silently fail to match. Now uses `!=`.
- **Async methods are fully typed**: `search_async()` and `contents_async()` were thin `**kwargs: Any` wrappers, which erased their signatures for type checkers and IDEs. They are now the real implementations with explicit parameters.

## [2.5.0] - 2026-07-20

### Added

- **`frontier` research effort tier**: New `ResearchEffort.FRONTIER` enum value for the highest-quality, longest-running research tasks. Frontier runs over longer durations with improved quality and accuracy. It only works with the task-based API (`background=true`); sending `frontier` without `background=true` returns a `422`. Use it with the background-mode helpers:

```python
from youdotcom import You
from youdotcom.models import ResearchEffort
from youdotcom.research_helpers import research_and_wait

you = You()
detail = research_and_wait(
    you,
    input="Evaluate the measurable global-health impact of the Gates Foundation",
    research_effort=ResearchEffort.FRONTIER,
    # timeout_s auto-adjusts to 14400 (4 hours) for frontier when omitted
)
print(detail.result.model_dump()["output"]["content"])
```

- **Research Background Mode**: The `you.research()` method now accepts an optional `background=True` parameter. When enabled, the API queues the research task and returns a `TaskResponse` (with `task_id`, `type`, `status`, `stream_url`, `created_at`) immediately instead of waiting for the inline `ResearchResponse`. Use the new methods to poll or stream the task to completion.

- **`you.get_research_task(task_id=...)`**: Poll the status of a background research task via `GET /v1/research/{task_id}`. Returns a `TaskDetail` with `status`, `result` (populated when completed), `error` (populated when failed), and timing fields.

- **`you.stream_research_task(task_id=..., from_id=0)`**: Stream real-time updates for a background research task via `GET /v1/research/{task_id}/stream` (Server-Sent Events). Returns an `EventStream` of `ResearchTaskStreamEvent` objects. The connection closes automatically when the task reaches a terminal state. Terminal event names: `response.done`, `complete`, `completed` (success); `error`, `failed`, `cancelled` (failure).

- **Convenience helpers** in `youdotcom.research_helpers` (hand-maintained, regen-safe):
  - `research_background(you, ...)` / `research_background_async(you, ...)`: submit and return `TaskResponse` directly (no Union narrowing needed).
  - `poll_research_task(you, task_id, ...)` / `poll_research_task_async(...)`: poll until terminal status (`completed`, `failed`, `cancelled`). Defaults: `interval_s=2.0`, `timeout_s=600.0` (10 minutes). For `frontier` tasks, pass `timeout_s=14400` (4 hours) explicitly since `poll_research_task` receives a `task_id` and cannot auto-detect the effort tier.
  - `research_and_wait(you, ...)` / `research_and_wait_async(...)`: submit with `background=True`, then stream SSE events until a terminal event arrives, and fetch the final `TaskDetail`. If the stream times out or closes without a terminal event, a final `get_research_task` call resolves the status (returns the detail if completed, raises `RuntimeError` for terminal non-completed, or `TimeoutError` if still running). For polling instead of streaming, use `poll_research_task` directly. **`timeout_s` auto-adjusts** based on `research_effort` when omitted: 600s (10 min) for standard/deep/exhaustive, 14400s (4 hours) for `frontier`.
  - `stream_research(you, task_id, ...)` / `stream_research_async(...)`: tolerant SSE iterator that surfaces undocumented event types as raw dicts instead of crashing on validation. **Recommended over `you.stream_research_task()` for real research tasks**, since the server emits intermediate workflow events not in the strict `Event` enum.

- **New models**: `TaskResponse`, `TaskResponseStatus`, `TaskDetail`, `TaskDetailStatus`, `TaskDetailInput`, `Result`, `GetResearchTaskRequest`, `StreamResearchTaskRequest`, `ResearchTaskStreamEvent`, `ResearchTaskStreamEventData`, `Event`, `ResearchResult` (Union alias).

- **New error classes**: `GetResearchTaskUnauthorizedError`, `GetResearchTaskForbiddenError`, `GetResearchTaskNotFoundError`, `GetResearchTaskInternalServerError`, `StreamResearchTaskUnauthorizedError`, `StreamResearchTaskForbiddenError`, `StreamResearchTaskNotFoundError`, `StreamResearchTaskInternalServerError` (and their `*Data` variants).

### Changed

- **`you.research()` return type** is now `Union[ResearchResponse, TaskResponse]` (exposed as the `ResearchResult` alias). When `background=False` (the default), the return is `ResearchResponse` as before. When `background=True`, the return is `TaskResponse`. Use `isinstance(res, TaskResponse)` to narrow, or use the `research_helpers` convenience functions.

### Notes

- All 2.4.0 features (finance_research, source_control, output_schema, boost_domains, max_age, env-var precedence, user_agent hook) are unchanged.

## [2.4.0] - 2026-07-14

### Added

- **Finance Research API**: New `you.finance_research()` method on the main `You` client. The Finance Research API searches a finance-optimized index: SEC filings, earnings transcripts, analyst coverage, market data, and financial news, instead of the open web. Use it for earnings analysis, due diligence, and market research.

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

- **Research `source_control` (beta)**: New optional `source_control` object on `you.research()` for constraining the research agent's web sources. Supports `include_domains`, `exclude_domains`, `boost_domains`, `freshness`, and `country`. `include_domains` and `exclude_domains` cannot be combined (returns `422`); `boost_domains` combines with `exclude_domains` but not `include_domains`.

- **Research `output_schema` (beta)**: New optional `output_schema` object on `you.research()` for requesting structured JSON output in `output.content`. Response `content_type` becomes `"object"` and `output.content` is a structured dict matching the schema. Supported on `standard`, `deep`, and `exhaustive` effort levels (sending it with `lite` returns `422`).

- **Search API `boost_domains`**: New optional parameter on `you.search_post()` and on the underlying `you.search.unified()` (also accessible via `GET /v1/search`). Boost (but don't restrict) results from specified domains. Up to 500 domains per request. Cannot be combined with `include_domains`.

- **Contents API `max_age`**: New optional `max_age` parameter (integer seconds, ≥0, nullable) for controlling cache freshness. When set, cached content older than the threshold is ignored and the page is re-fetched. Default `null` (no age limit).

### Changed

- **`Research.output.content` is now `Union[str, object]`**: When an `output_schema` is supplied, the server returns a structured JSON object and `content_type` becomes `"object"`. The overlay injects `additionalProperties: true` so `output.content` round-trips as a plain `dict` matching the requested schema. Text responses (`content_type="text"`) return `output.content` as a `str`. Check `output.content_type` to deserialise correctly: `text` → str, `object` → dict.

- **New `FinanceResearchEffort` enum**: The Finance Research API has its own effort enum (`DEEP`, `EXHAUSTIVE`) distinct from the Research API's `ResearchEffort`. Both have clean names. `ResearchEffort` is unchanged from 2.3.x.

- **Livecrawl formats parameter now requires a list**: The `livecrawl_formats` parameter is now strictly typed as `Optional[List[LiveCrawlFormats]]`. Passing a single enum value (which worked in prior versions) now raises a validation error. Wrap the value in a list:

```python
# Before (2.3.x)
you.search.unified(query="...", livecrawl_formats=LiveCrawlFormats.MARKDOWN)

# After (2.4.0)
you.search.unified(query="...", livecrawl_formats=[LiveCrawlFormats.MARKDOWN])
```

- **Consolidated error classes for Search**: The bare-from-spec names removed in 2.4.0 (`SearchForbiddenError`, `SearchUnauthorizedError`, `UnprocessableEntityError`, etc.) are replaced for both Search endpoints (`you.search.unified()` GET and `you.search_post()` POST) by consolidated `UnprocessableEntityResponseError`, `UnauthorizedResponseError`, and `ForbiddenResponseError`. `you.research()` and `you.finance_research()` keep raising per-endpoint typed errors (`ResearchUnprocessableEntityError`, `FinanceResearchUnprocessableEntityError`, etc.). Those classes are NOT consolidated. Catch Search on the consolidated `*ResponseError` class or `YouDefaultError`; catch Research/Finance Research on the per-endpoint class.

- **`WebResult.authors` field removed**: The `authors` field has been removed from the web search result model (`WebResult` / `WebResultTypedDict`). The server no longer returns this field. The overlay includes a `remove` action so future regenerations stay aligned.

- **Environment variable renamed to `YDC_API_KEY`**: The SDK now reads the `YDC_API_KEY` environment variable for API key authentication (canonical per `you.com/docs`). The previous `YOU_API_KEY_AUTH` is still accepted as a fallback for 2.3.x users upgrading without code changes. Set `YDC_API_KEY` in your environment and the SDK will pick it up automatically:

```bash
# Before (2.3.x)
export YOU_API_KEY_AUTH="your-api-key"

# After (2.4.0), preferred
export YDC_API_KEY="your-api-key"
# YOU_API_KEY_AUTH still works as a fallback
```

### Notes

- The `unresearched` `ulow` effort level remains internal and is intentionally NOT exposed in the SDK. It is consolidated as internal routing on the server.
- `you.finance_research()` deliberately does not support `source_control` or `output_schema`. The Finance Research API runs against a finance-optimized index and returns Markdown-formatted answers only.
- **`pydantic` upper bound removed**: The SDK previously pinned `pydantic <2.13` as a defensive measure. For a published library, upper bounds on core deps create resolver conflicts for downstream consumers who need a newer pydantic for other packages (fastapi, langchain, etc.). The SDK uses only stable pydantic 2.x APIs (`model_dump`, `model_serializer`, `BaseModel`, `pydantic_core.core_schema`), and the overlay's `additionalProperties: true` → `Dict[str, Any]` mechanism is plain Python typing, not a pydantic feature. The lower bound `>=2.11.2` is retained; if a future pydantic release breaks something, CI will catch it and we'll pin reactively.

### Fixed

- **`output_schema` requests no longer send an empty `{}` body**: the Research request body declares `output_schema` as an inline `type: object` schema (no `$ref`, no `properties`). Previously the body was a docstring-only model, so pydantic's `extra="ignore"` stripped every JSON Schema field on serialize, leaving the server to receive `{}` and return 422 (`Structured output schema root must be an object`). Now `OutputSchema` round-trips as `Optional[Dict[str, Any]]` and the JSON Schema reaches the server intact. Regression caught before release by `tests/test_live.py::TestLiveResearchOutputSchema::test_research_output_schema_structured_payload` against prod.

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
| `Verbosity` | `ReportVerbosity` | More specific, clarifies it controls research report verbosity |
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
