#!/bin/bash

# Performance Test Runner for You.com Python SDK
# 
# This script provides convenient shortcuts for running performance tests
# with common configurations.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TARGET="mock"
SERVER_URL="${PERF_TEST_SERVER_URL:-}"
ITERATIONS=5
API_KEY="${PERF_TEST_API_KEY:-test-api-key}"
OUTPUT_FORMAT="console"
DETAILED="false"
TEST_FILTER=""

# Help message
show_help() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Run performance tests for You.com Python SDK

OPTIONS:
    -h, --help              Show this help message
    -t, --target TARGET     Test target: mock, custom (default: mock)
    -u, --url URL           Server URL (required when target=custom)
    -i, --iterations N      Number of iterations per test (default: 5 for mock, 1 for custom)
    -k, --api-key KEY       API key for custom server
    -o, --output FORMAT     Output format: console, csv, json (default: console)
    -d, --detailed          Show detailed metrics for each test
    -f, --filter PATTERN    Run only tests matching pattern (pytest -k)
    
    --search                Run only Search API tests
    --agents                Run only Agents API tests
    --contents              Run only Contents API tests
    
    --quick                 Quick test: 1 iteration, basic tests only
    --full                  Full test: 20 iterations, all tests

EXAMPLES:
    # Quick smoke test against mock server
    $(basename "$0") --quick
    
    # Full test against mock server
    $(basename "$0") --full
    
    # Test against custom server with API key
    $(basename "$0") -t custom -u https://api.example.com -k YOUR_API_KEY -i 10
    
    # Test only Search API with detailed output
    $(basename "$0") --search --detailed -i 10
    
    # Test specific test case
    $(basename "$0") -f "search_basic" -i 20
    
    # Export results to CSV
    $(basename "$0") -i 20 -o csv

ENVIRONMENT VARIABLES:
    PERF_TEST_SERVER_URL    Server URL for custom target (can also use -u flag)
    PERF_TEST_API_KEY       API key (can also use -k flag)
    TEST_SERVER_URL         Custom mock server URL (for mock target only)

For more details, see tests/PERFORMANCE_TESTING.md
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -t|--target)
            TARGET="$2"
            shift 2
            ;;
        -u|--url)
            SERVER_URL="$2"
            shift 2
            ;;
        -i|--iterations)
            ITERATIONS="$2"
            shift 2
            ;;
        -k|--api-key)
            API_KEY="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        -d|--detailed)
            DETAILED="true"
            shift
            ;;
        -f|--filter)
            TEST_FILTER="$2"
            shift 2
            ;;
        --search)
            TEST_FILTER="TestSearchPerformance"
            shift
            ;;
        --agents)
            TEST_FILTER="TestAgentsPerformance"
            shift
            ;;
        --contents)
            TEST_FILTER="TestContentsPerformance"
            shift
            ;;
        --quick)
            ITERATIONS=1
            TEST_FILTER="basic"
            shift
            ;;
        --full)
            ITERATIONS=20
            shift
            ;;
        *)
            echo -e "${RED}Error: Unknown option $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate target
if [[ "$TARGET" != "mock" && "$TARGET" != "custom" ]]; then
    echo -e "${RED}Error: Invalid target '$TARGET'. Must be 'mock' or 'custom'${NC}"
    exit 1
fi

# Check server URL and API key for custom target
if [[ "$TARGET" == "custom" ]]; then
    if [[ -z "$SERVER_URL" ]]; then
        echo -e "${RED}Error: Server URL required for custom target. Use -u flag or set PERF_TEST_SERVER_URL${NC}"
        exit 1
    fi
    if [[ "$API_KEY" == "test-api-key" ]]; then
        echo -e "${YELLOW}Warning: Using default API key. Set PERF_TEST_API_KEY or use -k flag${NC}"
        echo -e "${YELLOW}Press Ctrl+C to cancel, or wait 3 seconds to continue...${NC}"
        sleep 3
    fi
fi

# Check if mock server is running (for mock target)
if [[ "$TARGET" == "mock" ]]; then
    MOCK_URL="${TEST_SERVER_URL:-http://localhost:18080}"
    if ! curl -s -o /dev/null -w "%{http_code}" "$MOCK_URL" > /dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Mock server may not be running at $MOCK_URL${NC}"
        echo -e "${YELLOW}Start it with: cd tests/mockserver && go run main.go${NC}"
        echo -e "${YELLOW}Press Ctrl+C to cancel, or wait 3 seconds to continue...${NC}"
        sleep 3
    else
        echo -e "${GREEN}✓ Mock server is running${NC}"
    fi
fi

# Build pytest command
PYTEST_CMD="pytest tests/test_performance.py"

# Add test filter if specified
if [[ -n "$TEST_FILTER" ]]; then
    PYTEST_CMD="$PYTEST_CMD -k $TEST_FILTER"
fi

# Add verbosity
PYTEST_CMD="$PYTEST_CMD -v"

# Print configuration
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  You.com SDK Performance Test Runner${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "Target:      ${GREEN}$TARGET${NC}"
if [[ "$TARGET" == "custom" ]]; then
    echo -e "Server URL:  ${GREEN}$SERVER_URL${NC}"
fi
echo -e "Iterations:  ${GREEN}$ITERATIONS${NC}"
echo -e "Output:      ${GREEN}$OUTPUT_FORMAT${NC}"
echo -e "Detailed:    ${GREEN}$DETAILED${NC}"
if [[ -n "$TEST_FILTER" ]]; then
    echo -e "Filter:      ${GREEN}$TEST_FILTER${NC}"
fi
if [[ "$TARGET" == "custom" ]]; then
    echo -e "API Key:     ${GREEN}${API_KEY:0:10}...${NC}"
fi
echo ""
echo -e "Command: ${YELLOW}$PYTEST_CMD${NC}"
echo ""

# Export environment variables
export PERF_TEST_TARGET="$TARGET"
if [[ -n "$SERVER_URL" ]]; then
    export PERF_TEST_SERVER_URL="$SERVER_URL"
fi
export PERF_TEST_ITERATIONS="$ITERATIONS"
export PERF_TEST_API_KEY="$API_KEY"
export PERF_OUTPUT_FORMAT="$OUTPUT_FORMAT"
export PERF_DETAILED="$DETAILED"

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo ""

if eval "$PYTEST_CMD"; then
    echo ""
    echo -e "${GREEN}✓ Performance tests completed successfully${NC}"
    
    if [[ "$OUTPUT_FORMAT" == "csv" ]]; then
        echo -e "${GREEN}✓ Results exported to performance_results.csv${NC}"
    fi
    
    exit 0
else
    echo ""
    echo -e "${RED}✗ Some performance tests failed${NC}"
    exit 1
fi
