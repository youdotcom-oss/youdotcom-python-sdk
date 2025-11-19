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
- `test_search.py` - Tests for the Search API (`/v1/search`)
- `test_contents.py` - Tests for the Contents API (`/v1/contents`)
- `test_runs.py` - Tests for the Agents/Runs API (`/v1/agents/runs`)

### Test Organization

Tests are organized into logical classes using pytest:

**Search API** (7 tests):
- Basic search functionality
- Search with filters (freshness, country, safesearch)
- Pagination and livecrawl
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

## Test Coverage

All tests cover the functionality demonstrated in the `examples/` directory:
- ✓ All search examples (`examples/search.py`)
- ✓ All contents examples (`examples/contents.py`)
- ✓ All agents examples (`examples/agents.py`)

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
- Error responses (401 Unauthorized, 403 Forbidden)
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

