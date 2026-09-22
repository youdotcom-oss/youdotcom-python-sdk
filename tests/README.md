# Tests

This directory contains the test suite for the You.com Python SDK. The tests are a mixture of auto-generated scaffolding and custom test implementations designed to comprehensively validate SDK functionality.

## Running Tests

### Automated Script (Recommended)

Use the automated test script from the project root:

```bash
./scripts/run_tests.sh
```

This script handles all setup and teardown automatically:
- Starts the mock server (using Go or Docker)
- Creates/activates a Python virtual environment
- Installs all dependencies
- Runs the full test suite
- Cleans up the mock server

By default, the virtual environment is kept for faster subsequent runs. To remove it after tests complete:
```bash
./scripts/run_tests.sh --cleanup
# or
./scripts/run_tests.sh -c
```

### Manual Testing

If you prefer to run tests manually:

1. Start the mock server:
```bash
cd tests/mockserver
go run .
```

2. In a separate terminal, run pytest:
```bash
# Install dependencies first
uv sync --dev
# or with pip:
pip install -e . mypy pylint pyright pytest pytest-asyncio

# Run tests
pytest tests/ -v
```

## Test Structure

### Test Files

- `test_client.py` - Helper utilities for creating test HTTP clients
- `test_search.py` - Tests for the Search API (`/v1/search`)
- `test_extraction.py` - Tests for the `extraction` parameter on `you.search` (model contract, strict validation, wire contract, conflicts, plus-value rule, async)
- `test_knowledge.py` - Tests for the `knowledge` parameter and the knowledge result models on `you.search`
- `test_page_age.py` - Tolerance of non-ISO `page_age` values on search and news results
- `test_contents.py` - Tests for the Contents API (`/v1/contents`)
- `test_answer.py` - Tests for the Answer API (`/v1/answer`)
- `test_direct_methods.py` - Tests for direct methods on `You` (search, contents)
- `test_shims.py` - Tests for backward-compat sub-SDK shims with DeprecationWarning
- `test_param_normalization.py` - Tests for plain-string parameter normalization (case folding, `language`, deprecated shims)
- `test_research.py` - Tests for the Research API (`/v1/research`) including background mode, output_schema, and source_control
- `test_research_helpers.py` - Tests for the hand-maintained `research_helpers` module (background submission, polling, streaming, research_and_wait)
- `test_researchtaskstreamevent.py` - Tests for `ResearchTaskStreamEvent` model contracts and the real SSE decode path
- `test_security_env.py` - Tests for environment variable precedence (`YDC_API_KEY` / `YOU_API_KEY_AUTH`)
- `test_attribution.py` - Tests for the `X-Client-Info` attribution header (grammar, edge cases, construction-time validation, wire round-trip, version resolution)
- `test_redaction.py` - Tests for debug-log header redaction
- `test_client_lifecycle.py` - Tests for client teardown in `You.__exit__` / `You.__aexit__`
- `test_root_init.py` - Tests for the `youdotcom` package root module
- `test_check_drift.py` - Regression tests for `scripts/check_drift.py` (response-schema recursion, cycle safety, suppression-table staleness)
- `test_performance.py` - Performance/instrumentation tests measuring SDK overhead
- `test_live.py` - Live API tests that run against the real You.com API (requires API key)

### Test Organization

Tests are organized into logical classes using pytest:

Counts below are collected tests (`pytest --collect-only`), so a parametrized case
counts once per parameter set. The groups sum to the 447 tests in the CI gate;
`test_performance.py` and `test_live.py` are excluded from that gate.

**Search API** (10 tests):
- Basic search functionality
- Search with filters (freshness, country, safesearch)
- Pagination and livecrawl
- News livecrawl with contents
- Error handling (unauthorized, forbidden, unprocessable, internal server error)

**Extraction** (38 tests):
- Model contract and strict validation
- Wire contract and mutual exclusion with the deprecated `livecrawl`
- Plus-value rule and async parity

**Knowledge** (21 tests):
- `Knowledge` enum and plain-string normalization
- Request wire contract on `search` / `search_async`
- Response parsing into `KnowledgeResult` / `KnowledgeAttribution`
- End-to-end round-trip and sub-SDK shim parity

**Page age tolerance** (15 tests):
- ISO values still parse to `datetime`
- Non-ISO values returned verbatim instead of failing the whole response
- Wrong JSON types still raise

**Contents API** (13 tests):
- HTML and Markdown format generation
- Single and multiple URL processing
- Optional format parameter
- Error handling (unauthorized, forbidden, empty URLs)

**Answer API** (25 tests):
- Basic answer functionality
- Answer with freshness, country, boost domains
- Async answer
- Error handling (unauthorized, forbidden, payment required, unprocessable, internal server error)

**Research API** (34 tests):
- Basic research functionality (standard, deep, exhaustive effort)
- Background mode (task submission, get_research_task, status polling)
- Output schema (structured JSON output, content_type object)
- Source control (include/exclude/boost domains, freshness, country)
- Error handling (unauthorized, forbidden, unprocessable entity, 422 combos)
- Stream research task (SSE success path + 404/401/403 error paths)

**Research Helpers** (57 tests):
- research_background / research_background_async (TaskResponse return)
- poll_research_task / poll_research_task_async (terminal status)
- research_and_wait / research_and_wait_async (submit + wait)
- stream_research / stream_research_async (tolerant SSE)
- RawStreamEvent decoder (_decode_raw_event)

**Research Task Stream Events** (26 tests):
- Known and unknown event names
- Round-trip and declared-type contracts
- End-to-end pin through the real SSE decode path

**Cross-cutting** (186 tests):
- `X-Client-Info` attribution header: grammar, edge cases, construction-time
  validation, wire round-trip, version resolution (91)
- Plain-string parameter normalization: case folding, `language` three-way
  contract, deprecated shims (35)
- Environment variable precedence `YDC_API_KEY` / `YOU_API_KEY_AUTH` (17)
- Debug-log header redaction (14)
- Client teardown in `You.__exit__` / `You.__aexit__` (10)
- Direct methods on `You` (8) and backward-compat sub-SDK shims (6)
- `youdotcom` package root module (5)

**Drift checker** (22 tests):
- Response-schema recursion, including drift on a sibling branch that reuses a model
- Cycle safety for self-referential and mutual (`A.b -> B.a -> A`) schemas
- `KNOWN_RESPONSE_GAPS` and `KNOWN_SHARED_MODEL_EXTRAS` staleness in all three cases
- `_resolve_schema` and `_nested_model` helpers

**Outside the CI gate**:
- `test_performance.py` (33 tests) - SDK overhead instrumentation
- `test_live.py` (46 tests) - runs against the real API, requires an API key

### Running Live Tests

The `test_live.py` file contains tests that run against the real You.com API. All tests require an API key and are skipped unless `YDC_API_KEY` or `YOU_API_KEY_AUTH` is set:

```bash
# Run live tests with your API key
YDC_API_KEY="your-api-key" pytest tests/test_live.py -v

# Run all tests except live tests
pytest tests/ --ignore=tests/test_live.py -v
```

## Test Coverage

All tests cover the functionality demonstrated in the `examples/` directory:
- ✓ All API examples (`examples/api-example-calls.py`)

Additionally, tests include:
- ✓ Error response handling for all endpoints
- ✓ Edge cases (empty inputs, various parameters)
- ✓ SDK type usage and validation

## Mock Server

The tests use a mock server located in `tests/mockserver/`. This server contains:

- **Hand-maintained Go code**: Core server framework and SDK models (`internal/sdk/`, `internal/server/`)
- **Custom handlers**: Test-specific responses for success and error scenarios

The mock server supports:
- Success responses for all endpoints
- Error responses (401 Unauthorized, 403 Forbidden, 404 Not Found)
- Background research task endpoints (GET /v1/research/{task_id}, GET /v1/research/{task_id}/stream)
- SSE streaming for research task updates
- Multiple test scenarios per endpoint

See [mockserver/README.md](mockserver/README.md) for more details.

## Best Practices

The test suite follows Python and pytest best practices:

- **Fixtures**: Reusable `server_url` and `api_key` fixtures
- **Class organization**: Logical grouping of related tests
- **Descriptive names**: Clear test names that indicate what's being tested
- **Proper assertions**: Specific checks for response structure
- **Error testing**: Using `pytest.raises()` for expected errors
- **DRY principle**: Minimal code duplication

## Continuous Integration

These tests are designed to run in CI/CD environments. The automated script ensures consistent test execution across different environments by:

- Automatically detecting and using Go or Docker for the mock server
- Supporting both `uv` and standard `pip` for dependency management
- Providing clear error messages and exit codes
- Cleaning up resources properly on completion or interruption

## Troubleshooting

**Tests not found**: Ensure you've installed dev dependencies with `uv sync --dev` or `pip install -e . mypy pylint pyright pytest pytest-asyncio`

**Mock server fails to start**: Ensure you have either Go (1.21+) or Docker installed

**Connection refused errors**: The mock server may not be running or may be on a different port. The default is `http://localhost:18080`

**Import errors**: Make sure the SDK is installed in editable mode (`pip install -e .`) or using `uv sync`

