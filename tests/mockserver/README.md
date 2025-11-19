# Mock Server

A generated HTTP mock server based on your OpenAPI Specification (OAS). This server contains a mixture of auto-generated code from Speakeasy and custom handlers for testing various scenarios including error responses.

## Running Tests

Tests should be run using the automated test script from the project root:

```shell
./scripts/run_tests.sh
```

This script handles starting the mock server, setting up the Python environment, installing dependencies, running the test suite, and cleaning up the mock server.

## Manual Usage

The server can be built and started manually via the [Go programming language toolchain](https://go.dev/) or [Docker](https://www.docker.com/).

If you have Go installed, start the server directly via:

```shell
go run .
```

Otherwise, if you have Docker installed, build and run the server via:

```shell
docker build -t mockserver .
docker run -i -p 18080:18080 -t --rm mockserver
```

By default, the server runs on port `18080`.

### Server Paths

The server contains generated paths from the OAS and the following additional built-in paths.

| Path | Description |
|---|---|
| [`/_mockserver/health`](https://localhost:18080/_mockserver/health) | verify server is running |
| [`/_mockserver/log`](https://localhost:18080/_mockserver/log) | view per-OAS-operation logs |

Any request outside the generated and built-in paths will return a `404 Not Found` response.

### Server Customization

The server supports the following flags for customization.

| Flag | Default | Description |
|---|---|---|
| `-address` | `:18080` | server listen address |
| `-log-format` | `text` | logging format (supported: `JSON`, `text`) |
| `-log-level` | `INFO` | logging level (supported: `DEBUG`, `INFO`, `WARN`, `ERROR`) |

For example, enabling server debug logging:

```shell
# via `go run`
go run . -log-level=DEBUG
# via `docker run`
docker run -i -p 18080:18080 -t --rm mockserver -log-level=DEBUG
```

## Code Structure

- **Auto-generated**: Core mock server framework, routing, and SDK models (`internal/sdk/`, `internal/server/`, `internal/logging/`, `internal/tracking/`)
- **Custom**: Test-specific handlers with success and error scenarios for comprehensive testing (`internal/handler/pathgetv1search.go`, `internal/handler/pathpostv1contents.go`, `internal/handler/pathpostv1agentsruns.go`)
