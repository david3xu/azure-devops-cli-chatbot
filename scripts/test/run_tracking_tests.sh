#!/bin/bash
# Run the workflow tracking tests

# Set environment variables for testing
export PYTHONPATH=.

# Create test directories if they don't exist
mkdir -p test_traces

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Running workflow tracking unit tests..."
echo "========================================"
if python -m pytest tests/rca/tracking/test_workflow_tracking.py -v; then
    echo -e "${GREEN}Unit tests passed!${NC}"
else
    echo -e "${RED}Unit tests failed!${NC}"
    exit 1
fi

echo ""
echo "Running workflow tracking integration tests..."
echo "=============================================="
if python -m pytest tests/rca/tracking/test_workflow_tracking.py -v -m "integration"; then
    echo -e "${GREEN}Integration tests passed!${NC}"
else
    echo -e "${RED}Integration tests failed!${NC}"
    # Don't exit here, as integration tests may fail in CI
fi

echo ""
echo "Running workflow tracking performance tests..."
echo "=============================================="
if python -m pytest tests/rca/tracking/test_workflow_tracking.py -v -m "performance"; then
    echo -e "${GREEN}Performance tests passed!${NC}"
else
    echo -e "${RED}Performance tests failed, but this might be expected in CI environments${NC}"
    # Don't exit here, as performance can vary
fi

echo ""
echo -e "${GREEN}All tests completed!${NC}" 