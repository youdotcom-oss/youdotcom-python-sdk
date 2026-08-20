<div align="center">
  <img width="600" height="315" alt="You.com" src="https://raw.githubusercontent.com/youdotcom-oss/youdotcom-python-sdk/refs/heads/main/images/logo.png" />
</div>

<div align="center">
  <strong>The official Python SDK for the You.com API</strong>: web search, citation-backed answers, page contents, and multi-step research.
</div>

<div align="center">
  <a href="https://pypi.org/project/youdotcom/"><img src="https://img.shields.io/pypi/v/youdotcom.svg" alt="PyPI" /></a>
  <a href="https://pypi.org/project/youdotcom/"><img src="https://img.shields.io/pypi/pyversions/youdotcom.svg" alt="Python versions" /></a>
  <a href="https://you.com/docs"><img src="https://img.shields.io/badge/docs-you.com%2Fdocs-blue.svg" alt="Documentation" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License: MIT" /></a>
</div>

## Install

```bash
pip install youdotcom
```

Requires Python 3.10+. Also available via `uv add youdotcom` or `poetry add youdotcom`.

## Quickstart

Get an API key from [you.com/platform](https://you.com/platform) and set it as `YDC_API_KEY`.

```python
import os
from youdotcom import You

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    res = you.answer(query="What caused the 2008 financial crisis?")
    print(res.answer)
```

That prints a markdown answer with inline `[[1, 2]]` citations. The sources behind
them are on the response:

```python
    for citation in res.citations or []:
        print(citation.source, citation.excerpts)
```

Two things about that snippet worth knowing up front:

> **`timeout_ms` is doing real work.** Without it, requests inherit httpx's 5
> second default, and `answer` takes longer than that. See [Timeouts](#timeouts).
>
> **The key is explicit here, but it doesn't have to be.** Pass
> `api_key_auth=None`, or omit it, to read `YDC_API_KEY` from the environment.
> See [Authentication](#authentication) for the resolution order.

## The APIs

Every method is a direct call on `You`, and every one has an `_async` twin with
the same signature.

`search()` and `answer()` normalize their enum-typed parameters, so plain
strings work in any case. `country="us"` and `safesearch="STRICT"` are both
accepted. Elsewhere, pass the value as the API spells it (all lowercase) or
import the enum from `youdotcom.models`.

### Answer

A synthesized answer with citations, grounded in live web results.

```python
res = you.answer(
    query="What are the tradeoffs of vector vs. keyword search?",
    freshness="month",
    safesearch="strict",
    include_domains=["arxiv.org"],
)

res.answer                    # markdown, with inline [[n]] citations
res.citations                 # [AnswerCitation(source, excerpts)]
res.results.web               # results used during synthesis
```

### Search

Ranked web and news results.

```python
res = you.search(
    query="EU AI Act enforcement timeline",
    count=10,
    country="us",
    freshness="week",
)

for hit in res.results.web or []:
    print(hit.title, hit.url)
```

`include_domains` restricts results to an allowlist; `exclude_domains` and
`boost_domains` filter and re-rank. `include_domains` cannot be combined with
either of the others. The API returns `422` if you try. Search also supports
[search operators](https://you.com/docs/guides/search-operators).

#### Page content extraction

Pass `extraction` to attach page content to each result. Two modes:

```python
import os
from youdotcom import You
from youdotcom.models import Extraction, ExtractionFormat, ExtractionMode

with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
    # Query-relevant excerpts in `contents.highlights` (snippets are omitted).
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(
            extraction_mode=ExtractionMode.HIGHLIGHTS,
        ),
    )
    for hit in res.results.web or []:
        print(hit.title, hit.url, hit.contents.highlights if hit.contents else None)

    # Full HTML and/or Markdown in `contents.html` / `contents.markdown`.
    res = you.search(
        query="latest quantum computing breakthroughs",
        extraction=Extraction(
            extraction_mode=ExtractionMode.FULL_PAGE,
            full_page={"extraction_formats": [ExtractionFormat.MARKDOWN]},
        ),
    )
```

You can also pass a dict matching `ExtractionTypedDict` — the SDK
normalizes at the method layer. `extraction` replaces the deprecated
`livecrawl` / `livecrawl_formats` parameters. Passing both raises
`ValueError`, and top-level `crawl_timeout` is ignored (stripped from
the request body) when `extraction_mode == "highlights"`. Unknown keys
inside `extraction` raise `ValidationError` locally, matching the
server's 422.

### Contents

Clean HTML or Markdown for a list of URLs.

```python
pages = you.contents(
    urls=["https://example.com", "https://you.com"],
    formats=["markdown", "metadata"],
)

for page in pages:
    print(page.url, page.title)
    print(page.markdown)
```

`formats` accepts `html`, `markdown`, and `metadata` (JSON-LD and OpenGraph).
Use `max_age` to reject cached content older than a given number of seconds.

### Research

Multi-step research with reasoning and cited sources. Higher effort levels run
more searches and take longer.

```python
res = you.research(
    input="Compare the unit economics of the major cloud providers",
    research_effort="deep",     # lite | standard | deep | exhaustive | frontier
)

print(res.output.content)
for source in res.output.sources or []:
    print(source.url)
```

`you.finance_research()` is the finance-tuned counterpart, taking
`research_effort` of `deep` or `exhaustive`.

Deep and exhaustive runs can take minutes, and `frontier` runs far longer. For
anything beyond `standard`, use [background mode](#long-running-research).

## Async

Every method has an `_async` variant. Use `async with` so both transports are
released on exit.

```python
import asyncio
import os
from youdotcom import You

async def main():
    async with You(api_key_auth=os.getenv("YDC_API_KEY"), timeout_ms=60_000) as you:
        res = await you.answer_async(query="What is retrieval-augmented generation?")
        print(res.answer)

asyncio.run(main())
```

Concurrent calls share the one client:

```python
answer, results = await asyncio.gather(
    you.answer_async(query="What is RAG?"),
    you.search_async(query="RAG benchmarks", count=5),
)
```

## Long-running research

Rather than holding a request open for minutes, background mode submits the task
and returns immediately. The helpers in `youdotcom.research_helpers` cover the
common shapes.

**Submit and wait.** Handles submission, streaming, and the final fetch:

```python
from youdotcom.research_helpers import research_and_wait

detail = research_and_wait(
    you,
    input="Survey the state of solid-state battery commercialization",
    research_effort="exhaustive",
)
print(detail.status, detail.result)
```

The wait is bounded automatically: 10 minutes for standard, deep, and
exhaustive, 4 hours for `frontier`. Pass `timeout_s` to override. It raises
`TimeoutError` if no terminal event arrives, and `RuntimeError` if the task ends
in a non-completed state.

**Submit and poll**, if you'd rather own the loop:

```python
from youdotcom.research_helpers import research_background, poll_research_task

task = research_background(you, input="...", research_effort="deep")
detail = poll_research_task(you, task.task_id, interval_s=5.0)
```

**Stream events** as the task progresses:

```python
from youdotcom.research_helpers import stream_research

for evt in stream_research(you, task_id=task.task_id):
    print(evt.event, evt.data)
    if evt.event in ("response.done", "completed", "error", "failed", "cancelled"):
        break
```

`stream_research()` tolerates event names outside the documented set, yielding
them as raw dicts. Prefer it over `you.stream_research_task()`, which validates
strictly and will raise on an unrecognized event. Pass `from_id` to resume a
stream after a disconnect.

Each helper has an `_async` twin: `research_and_wait_async`,
`research_background_async`, `poll_research_task_async`, `stream_research_async`.

## Authentication

The API key is sent as the `X-API-Key` header. How it's resolved:

| `api_key_auth` | Behavior |
| --- | --- |
| omitted, or `None` | Reads `YDC_API_KEY`, then the legacy `YOU_API_KEY_AUTH` |
| a non-empty string, or a callable returning one | That key is used; no environment lookup |
| `""` or blank, or a callable returning an empty string | Raises `ValueError` |

Every endpoint requires a key, so an empty string is never valid. It means a key
was expected and none arrived. The SDK raises rather than reading the
environment, since falling back would run the request under whatever identity
the environment happens to hold instead of the one the code asked for.

In practice that shows up as `os.getenv("YDC_API_KEY", "")` with the variable
unset. Use `os.getenv("YDC_API_KEY")`. `None` is how you ask for the lookup.

A callable is resolved on each request, so it can return a rotating key.

## Errors

Every API error subclasses `YouError`, which carries `.message`,
`.status_code`, `.body`, `.headers`, and `.raw_response`. The typed subclasses
below add a parsed `.data`.

```python
from youdotcom.errors import (
    PaymentRequiredResponseError,
    UnauthorizedResponseError,
    YouError,
)

try:
    res = you.answer(query="...")
except UnauthorizedResponseError:
    ...                                  # 401, bad or missing key
except PaymentRequiredResponseError as e:
    print(e.data.message, e.data.upgrade_url)   # 402, out of credits
except YouError as e:
    print(e.status_code, e.body)         # anything else from the API
```

Answer and search share one set of error classes; research, finance research,
contents, and the task endpoints each raise their own, so you can catch a `422`
from research without catching one from search.

| Status | Answer / Search | Contents | Research | Finance Research | Task get / stream |
| --- | --- | --- | --- | --- | --- |
| 401 | `UnauthorizedResponseError` | `ContentsUnauthorizedError` | `ResearchUnauthorizedError` | `FinanceResearchUnauthorizedError` | `GetResearchTask…` / `StreamResearchTask…UnauthorizedError` |
| 402 | `PaymentRequiredResponseError` <sup>answer only</sup> | n/a | n/a | n/a | n/a |
| 403 | `ForbiddenResponseError` | `ContentsForbiddenError` | `ResearchForbiddenError` | `FinanceResearchForbiddenError` | `…ForbiddenError` |
| 404 | n/a | n/a | n/a | n/a | `…NotFoundError` |
| 422 | `UnprocessableEntityResponseError` | n/a | `ResearchUnprocessableEntityError` | `FinanceResearchUnprocessableEntityError` | n/a |
| 500 | `InternalServerErrorResponse` | `ContentsInternalServerError` | `ResearchInternalServerError` | `FinanceResearchInternalServerError` | `…InternalServerError` |

Two errors sit outside that table: `ResponseValidationError` when a response
doesn't match its model, and `httpx.RequestError` (and subclasses) for transport
failures such as connection resets and timeouts.

## Configuration

### Retries

The SDK does **not** retry by default. Opt in per call or for the whole client:

```python
from youdotcom.utils import BackoffStrategy, RetryConfig

retries = RetryConfig(
    "backoff",
    BackoffStrategy(initial_interval=500, max_interval=10_000, exponent=1.5, max_elapsed_time=60_000),
    retry_connection_errors=True,
)

with You(api_key_auth=key, retry_config=retries) as you:   # whole client
    res = you.search(query="...", retries=retries)         # or one call
```

Retries apply to `429`, `500`, `502`, `503`, and `504`.

### Timeouts

**Set one.** With no `timeout_ms`, requests inherit the underlying httpx client's
default of 5 seconds, which is far too short for `answer`, `research`, and
`finance_research`. Those endpoints routinely take tens of seconds, so a call
without a timeout will raise `httpx.ReadTimeout` before the API responds.

`timeout_ms` applies to the whole client or to a single call:

```python
with You(api_key_auth=key, timeout_ms=60_000) as you:
    answer = you.answer(query="...")                     # inherits 60s
    results = you.search(query="...", timeout_ms=10_000)  # this call only
```

Search and contents are fast enough for the default. Research in background mode
is the exception: the helpers under
[Long-running research](#long-running-research) manage their own deadlines, so
`timeout_s` there bounds the wait rather than `timeout_ms`.

### Attribution

Every SDK request emits an `X-Client-Info` header so the analytics layer can
split SDK traffic from MCP traffic. The wire format is:

```
python-sdk; client=youdotcom/<version>[; title=<title>][; url=<url>]; ua=python/<V> httpx/<V>
```

Optionally pass `app_title` and `app_url` to populate the `title=` and
`url=` segments:

```python
import os
from youdotcom import You

with You(
    api_key_auth=os.getenv("YDC_API_KEY"),
    app_title="MyAgent",
    app_url="https://example.com",
    timeout_ms=60_000,
) as you:
    res = you.search(query="...")
```

Both arguments are optional; existing call sites are unaffected.

### Servers

`search` and `contents` go to `https://ydc-index.io`. Everything else goes to
`https://api.you.com`: `answer`, `research`, `finance_research`, and the research
task endpoints. The SDK routes each call for you. To point one call
elsewhere, at a proxy or a test server, pass `server_url` to the method:

```python
res = you.search(query="...", server_url="http://localhost:18080")
```

The constructor's `server_url` sets the default host, which affects the
`api.you.com` endpoints. Because `search` and `contents` have their own
per-operation default, they are unaffected by it; override those per call.

### Custom HTTP client

Pass any `httpx.Client` / `httpx.AsyncClient` to control proxies, TLS, custom
headers, or connection limits:

```python
import httpx

http_client = httpx.Client(proxy="http://localhost:8030", headers={"x-team": "search"})

with You(api_key_auth=key, client=http_client) as you:
    ...

http_client.close()   # a transport you supply is yours to close
```

You can also pass anything satisfying the `HttpClient` / `AsyncHttpClient`
protocols in `youdotcom.httpclient` to wrap requests with your own logic. Note
that a transport you supply is yours to close. The SDK only closes the ones it
creates.

### Resource management

`You` holds open connections and has no public `close()`, so use it as a context
manager. Both transports are released on exit.

```python
with You(api_key_auth=key) as you:
    ...
# or: async with You(api_key_auth=key) as you:
```

An instance is not reusable after the block exits, including for calls of the
other flavor. Use one instance per sync/async flavor.

### Debug logging

Set `YOU_DEBUG=1` for request and response logging, or pass your own logger:

```python
import logging

with You(api_key_auth=key, debug_logger=logging.getLogger("youdotcom")) as you:
    ...
```

`Authorization`, `X-API-Key`, `Cookie`, and `Set-Cookie` are redacted. Request
and response bodies are not, and may carry sensitive data. Don't enable debug
logging in production, and don't commit debug logs to version control.

## Documentation

- [API reference](https://you.com/docs/api-reference): endpoints, parameters, response schemas
- [Quickstart](https://you.com/docs/quickstart)
- [Pricing and plans](https://you.com/platform)
- [`docs/`](docs/): per-method SDK reference generated from this codebase
- [`examples/`](examples/): runnable, typed examples for every endpoint
- [MIGRATION.md](MIGRATION.md): upgrading between major versions

## Development

### Testing

```bash
./scripts/run_tests.sh
```

Starts the Go mock server, sets up a virtualenv, runs the suite, and cleans up.
Pass `--cleanup` to remove the virtualenv afterwards. See
[tests/README.md](tests/README.md) for running pieces of it directly.

### Drift detection

This SDK is hand-maintained rather than generated, so `scripts/check_drift.py`
enforces what code generation used to guarantee: it diffs the published OpenAPI
specs against the SDK surface (endpoints, server URLs, enum values, request
parameters, response fields) and runs on every PR plus weekly.

```bash
python scripts/check_drift.py --verbose
```

### Versioning

This project follows [Semantic Versioning](https://semver.org/). Breaking
changes only land in major releases and are documented in
[MIGRATION.md](MIGRATION.md) and [CHANGELOG.md](CHANGELOG.md).

### Contributing

Pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and
guidelines. For bugs and feature requests, open an issue.

## License

MIT. See [LICENSE](LICENSE).
