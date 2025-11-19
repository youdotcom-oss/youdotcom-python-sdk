#!/bin/bash
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
MOCKSERVER_DIR="$PROJECT_ROOT/tests/mockserver"
MOCKSERVER_PID=""

# Cleanup function
cleanup() {
    if [ ! -z "$MOCKSERVER_PID" ]; then
        echo -e "\n${YELLOW}Stopping mock server (PID: $MOCKSERVER_PID)...${NC}"
        kill $MOCKSERVER_PID 2>/dev/null || true
        wait $MOCKSERVER_PID 2>/dev/null || true
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT INT TERM

# Parse arguments
CLEANUP=false
if [[ "$1" == "--cleanup" ]] || [[ "$1" == "-c" ]]; then
    CLEANUP=true
fi

echo -e "${GREEN}Setting up test environment...${NC}"

# Change to project root
cd "$PROJECT_ROOT"

# Start mock server
echo -e "${GREEN}Starting mock server...${NC}"
cd "$MOCKSERVER_DIR"

if command -v go &> /dev/null; then
    echo "Starting mock server with Go..."
    go run . > /tmp/mockserver.log 2>&1 &
    MOCKSERVER_PID=$!
elif command -v docker &> /dev/null; then
    echo "Starting mock server with Docker..."
    docker build -t mockserver . > /dev/null 2>&1
    docker run -d -p 18080:18080 --name mockserver-test mockserver > /dev/null 2>&1
    # Wait a moment for container to start
    sleep 2
else
    echo -e "${RED}Error: Neither Go nor Docker found. Please install one to run the mock server.${NC}"
    exit 1
fi

# Wait for mock server to be ready
echo "Waiting for mock server to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:18080/_mockserver/health > /dev/null 2>&1; then
        echo -e "${GREEN}Mock server is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}Error: Mock server failed to start${NC}"
        if [ ! -z "$MOCKSERVER_PID" ]; then
            echo "Mock server log:"
            tail -20 /tmp/mockserver.log 2>/dev/null || echo "No log file found"
        fi
        exit 1
    fi
    sleep 1
done

# Give it an extra moment to fully initialize
sleep 1

cd "$PROJECT_ROOT"

# Check if uv is available
if command -v uv &> /dev/null; then
    echo -e "${GREEN}Using uv for dependency management${NC}"
    
    # Create venv and install dependencies
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        uv venv
    fi
    
    echo "Installing dependencies..."
    uv sync --dev
    
    # Activate venv and run tests
    source "$VENV_DIR/bin/activate"
    echo -e "${GREEN}Running tests...${NC}"
    pytest tests/ -v
    
    # Deactivate venv
    deactivate
    
elif command -v python3 &> /dev/null; then
    echo -e "${YELLOW}uv not found, using standard venv + pip${NC}"
    
    # Create venv if it doesn't exist
    if [ ! -d "$VENV_DIR" ]; then
        echo "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate venv
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
    
    # Install the package in editable mode with dev dependencies
    echo "Installing dependencies..."
    pip install -e ".[dev]" > /dev/null
    
    # Run tests
    echo -e "${GREEN}Running tests...${NC}"
    pytest tests/ -v
    
    # Deactivate venv
    deactivate
    
else
    echo -e "${RED}Error: Neither uv nor python3 found. Please install Python 3.9.2 or higher.${NC}"
    exit 1
fi

# Stop mock server (cleanup function will handle it)
cleanup

# Cleanup Docker container if used
if command -v docker &> /dev/null && docker ps -a --format '{{.Names}}' | grep -q "^mockserver-test$"; then
    docker stop mockserver-test > /dev/null 2>&1 || true
    docker rm mockserver-test > /dev/null 2>&1 || true
fi

# Cleanup venv if requested
if [ "$CLEANUP" = true ]; then
    echo -e "${YELLOW}Cleaning up virtual environment...${NC}"
    rm -rf "$VENV_DIR"
    echo -e "${GREEN}Cleanup complete.${NC}"
else
    echo -e "${GREEN}Tests completed. Virtual environment kept at $VENV_DIR${NC}"
    echo -e "${YELLOW}To clean up, run: rm -rf $VENV_DIR${NC}"
    echo -e "${YELLOW}Or run this script with --cleanup flag to auto-cleanup${NC}"
fi

echo -e "${GREEN}Done!${NC}"

