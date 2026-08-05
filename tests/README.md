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
# or
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

## Test Structure

### Test Files

- `test_client.py` - Helper utilities for creating test HTTP clients
- `test_search.py` - Tests for the Search API (`/v1/agents/search`)
- `test_contents.py` - Tests for the Contents API (`/v1/contents`)
- `test_runs.py` - Tests for the Agents/Runs API (`/v1/agents/runs`)
- `test_research.py` - Tests for the Research API (`/v1/research`) including background mode, output_schema, and source_control
- `test_research_helpers.py` - Tests for the hand-maintained `research_helpers` module (background submission, polling, streaming, research_and_wait)
- `test_security_env.py` - Tests for environment variable precedence (`YDC_API_KEY` / `YOU_API_KEY_AUTH`)
- `test_performance.py` - Performance/instrumentation tests measuring SDK overhead
- `test_live.py` - Live API tests that run against the real You.com API (requires API key)

### Test Organization

Tests are organized into logical classes using pytest:

**Search API** (9 tests):
- Basic search functionality
- Search with filters (freshness, country, safesearch)
- Pagination and livecrawl
- News livecrawl with contents (new in 2.2.0)
- Error handling (unauthorized, forbidden)

**Contents API** (8 tests):
- HTML and Markdown format generation
- Single and multiple URL processing
- Optional format parameter
- Error handling (unauthorized, forbidden, empty URLs)

**Agents/Runs API** (12 tests):
- Express agent (basic, streaming, with tools)
- Advanced agent (with research, compute, multiple tools)
- Custom agents (UUID-based)
- Tool configurations and verbosity
- Error handling (unauthorized, forbidden, empty input)

**Research API**:
- Basic research functionality (standard, deep, exhaustive effort)
- Background mode (task submission, get_research_task, status polling)
- Output schema (structured JSON output, content_type object)
- Source control (include/exclude/boost domains, freshness, country)
- Error handling (unauthorized, forbidden, unprocessable entity, 422 combos)
- Stream research task (SSE success path + 404/401/403 error paths)

**Research Helpers**:
- research_background / research_background_async (TaskResponse return)
- poll_research_task / poll_research_task_async (terminal status)
- research_and_wait / research_and_wait_async (submit + wait)
- stream_research / stream_research_async (tolerant SSE)
- RawStreamEvent decoder (_decode_raw_event)

### Running Live Tests

The `test_live.py` file contains tests that run against the real You.com API. Keyed tests are skipped unless an API key is provided. Keyless search tests (`TestLiveSearchKeyless`) run without an API key by default, since they verify the free-tier `/v1/agents/search` proxy:

```bash
# Run live tests with your API key (enables keyed tests)
YDC_API_KEY="your-api-key" pytest tests/test_live.py -v

# Run only keyless live tests (no API key needed)
pytest tests/test_live.py::TestLiveSearchKeyless -v

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

- **Auto-generated code**: Core framework from Speakeasy (`internal/sdk/`, `internal/server/`)
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

**Tests not found**: Ensure you've installed dev dependencies with `uv sync --dev` or `pip install -e ".[dev]"`

**Mock server fails to start**: Ensure you have either Go (1.21+) or Docker installed

**Connection refused errors**: The mock server may not be running or may be on a different port. The default is `http://localhost:18080`

**Import errors**: Make sure the SDK is installed in editable mode (`pip install -e .`) or using `uv sync`

