# Performance Testing Guide

This document describes how to use the comprehensive performance testing suite for the You.com Python SDK.

## Overview

The performance testing suite measures SDK latency vs API latency across all supported endpoint combinations:

- **Search API**: 20+ test cases covering filters, livecrawl, pagination, etc.
- **Contents API**: 8 test cases covering formats and URL counts

## Quick Start

### Test Against Mock Server

```bash
# Run all performance tests against the mock server (fastest, consistent)
pytest tests/test_performance.py -v

# Run with more iterations for better statistics
PERF_TEST_ITERATIONS=20 pytest tests/test_performance.py -v
```

### Test Against Custom Server

```bash
# Run against a custom server (requires API key and server URL)
PERF_TEST_TARGET=custom \
PERF_TEST_SERVER_URL=https://api.example.com \
PERF_TEST_API_KEY=your_api_key_here \
PERF_TEST_ITERATIONS=10 \
pytest tests/test_performance.py -v
```

## Environment Variables

| Variable | Values | Default | Description |
|----------|--------|---------|-------------|
| `PERF_TEST_TARGET` | `mock`, `custom` | `mock` | Which API to test against |
| `PERF_TEST_SERVER_URL` | URL string | - | Server URL (required for `custom` target) |
| `PERF_TEST_ITERATIONS` | Integer (1-100) | `5` for mock, `1` for custom | Number of iterations per test |
| `PERF_TEST_API_KEY` | String | `test-api-key` | API key for custom server |
| `PERF_OUTPUT_FORMAT` | `console`, `csv`, `json` | `console` | Output format for results |
| `PERF_DETAILED` | `true`, `false` | `false` | Show detailed metrics per test |

## Running Specific Test Groups

### Search Tests Only

```bash
pytest tests/test_performance.py::TestSearchPerformance -v
```

### Contents Tests Only

```bash
pytest tests/test_performance.py::TestContentsPerformance -v
```

### Individual Test

```bash
pytest tests/test_performance.py::TestSearchPerformance::test_search_with_livecrawl_markdown -v
```

## Understanding the Output

### Summary Table

After all tests complete, a summary table is printed:

```
====================================================================================================================
                                     Performance Test Results - Target: custom                                      
====================================================================================================================

Endpoint                                             P50        P95        P99       Mean   Overhead      %
-------------------------------------------------- ---------- ---------- ---------- ---------- ---------- ------
Search: basic query                                  245ms      312ms      401ms      258ms       8ms   3.1%
Search: with count=10                                267ms      334ms      425ms      279ms       9ms   3.2%
Search: freshness=DAY                                251ms      318ms      407ms      264ms       8ms   3.0%
...
--------------------------------------------------------------------------------------------------------------------

Summary:
  Total test cases: 29
  Total iterations: 145
  Success rate: 145/145 (100.0%)

SDK Overhead Analysis:
  Average overhead: 9.2ms (3.1%)
  Min overhead: 7ms (best case)
  Max overhead: 12ms (worst case)
  Median overhead: 9ms
```

### Metrics Explained

- **P50 (Median)**: 50% of requests completed faster than this
- **P95**: 95% of requests completed faster than this
- **P99**: 99% of requests completed faster than this
- **Mean**: Average time across all iterations
- **Overhead**: SDK processing time (serialization + parsing)
- **%**: Overhead as percentage of total time

### Detailed Metrics

Enable detailed output to see breakdown per test:

```bash
PERF_DETAILED=true pytest tests/test_performance.py::TestSearchPerformance::test_search_basic -v
```

Output includes:

```
================================================================================
Detailed Metrics: Search: basic query
================================================================================

Iterations: 20
Success rate: 20/20 (100.0%)

SDK Total Time:
  Min:    242ms
  Max:    289ms
  Mean:   258ms
  Median: 255ms
  P95:    281ms
  P99:    287ms
  StdDev: 13.2ms

HTTP Time:
  Min:    235ms
  Max:    281ms
  Mean:   250ms
  Median: 247ms
  P95:    273ms
  P99:    279ms
  StdDev: 12.8ms

SDK Overhead:
  Min:    7ms
  Max:    10ms
  Mean:   8ms (3.1%)
  Median: 8ms
  P95:    9ms
  P99:    10ms
```

## Exporting Results

### CSV Export

```bash
PERF_OUTPUT_FORMAT=csv pytest tests/test_performance.py -v
# Creates: performance_results.csv
```

The CSV includes all metrics for further analysis in Excel, Google Sheets, or data analysis tools.

## Best Practices

### For Reliable Results

1. **Use mock server for CI/CD**: Consistent, fast, no API costs
2. **Use custom server for realistic metrics**: Real-world performance data
3. **Run multiple iterations**: At least 10-20 for statistical significance
4. **Warm-up**: First request may be slower (DNS, connection setup)
5. **Consistent environment**: Run on same machine/network for comparisons

### For Development

```bash
# Quick check during development (fast, 1 iteration)
PERF_TEST_ITERATIONS=1 pytest tests/test_performance.py -k "search_basic" -v

# Full regression test before release (comprehensive)
PERF_TEST_ITERATIONS=20 pytest tests/test_performance.py -v
```

### For CI/CD

```bash
# Add to your CI pipeline
PERF_TEST_TARGET=mock \
PERF_TEST_ITERATIONS=10 \
PERF_OUTPUT_FORMAT=csv \
pytest tests/test_performance.py -v --tb=short

# Optional: Assert overhead stays below threshold
# (Add assertions in test code if needed)
```

## Interpreting Results

### What's Normal?

- **Mock server**: Overhead 1-5ms (most time is SDK processing)
- **Real API servers**: Overhead 5-15ms (small % of total time)
- **Overhead percentage**: Typically <5% for real API calls

### Red Flags

- Overhead >50ms: Potential SDK performance issue
- Overhead >10%: SDK processing dominates (may indicate issue)
- High variance (stddev): Inconsistent performance, investigate

## Troubleshooting

### Tests Fail to Connect

```
Error: Connection refused
```

**Solution**: Make sure mock server is running:

```bash
cd tests/mockserver
go run main.go
```

### Authentication Errors with Custom Server

```
Error: 401 Unauthorized
```

**Solution**: Check your API key:

```bash
export PERF_TEST_API_KEY=your_actual_api_key
pytest tests/test_performance.py -v
```

### No Timing Data Captured

```
RuntimeError: No HTTP timing captured
```

**Solution**: This indicates the TimingHTTPClient isn't being used. Check test setup.

## Advanced Usage

### Custom Test Target

```bash
# Test against custom server
TEST_SERVER_URL=http://localhost:8080 \
PERF_TEST_TARGET=mock \
pytest tests/test_performance.py -v
```

### Parallel Execution

```bash
# Run tests in parallel (faster, but results may vary)
pytest tests/test_performance.py -n auto -v
```

Note: Parallel execution may affect timing accuracy due to resource contention.

## Architecture

### Components

1. **`timing_client.py`**: HTTP client wrapper that tracks request timing
2. **`metrics.py`**: Statistical analysis and reporting utilities
3. **`test_performance.py`**: Comprehensive test suite

### How It Works

```
┌─────────────────┐
│  Test Function  │
│  (SDK Call)     │
└────────┬────────┘
         │
         ├──> SDK Start Time
         │
         ▼
┌─────────────────┐
│   SDK Methods   │
│   (serialize)   │
└────────┬────────┘
         │
         ├──> HTTP Start Time
         │
         ▼
┌─────────────────┐
│ TimingHTTPClient│
│  (HTTP request) │
└────────┬────────┘
         │
         ├──> HTTP End Time
         │
         ▼
┌─────────────────┐
│   SDK Methods   │
│    (parse)      │
└────────┬────────┘
         │
         ├──> SDK End Time
         │
         ▼
┌─────────────────┐
│ Calculate       │
│ Overhead        │
└─────────────────┘
```

**Overhead** = (SDK End - SDK Start) - (HTTP End - HTTP Start)

## Contributing

To add new test cases:

1. Add test method to appropriate class
2. Use `measure_sdk_call()` helper
3. Follow naming convention: `test_<endpoint>_<variant>`
4. Add descriptive endpoint name for reporting

Example:

```python
def test_search_with_new_filter(self, server_url, api_key, iterations, show_detailed):
    """Test description."""
    client = create_test_http_client("post_/v1/search")
    
    with You(server_url=server_url, client=client, api_key_auth=api_key) as you:
        def call():
            you.search(query="test", new_filter="value")
        
        metrics = measure_sdk_call(call, client, iterations, "Search: new filter")
        ALL_METRICS.append(metrics)
        if show_detailed:
            print_detailed_metrics(metrics)
```

## Support

For issues or questions:
- Check existing tests for examples
- Review error messages carefully
- Ensure mock server is running (for mock tests)
- Verify API key and server URL (for custom server tests)
