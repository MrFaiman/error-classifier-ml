#!/bin/bash
# Integration test runner - starts services and runs tests

set -e

echo "🚀 Starting Integration Tests"
echo "=============================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if API server is running
echo -e "${YELLOW}Checking API server...${NC}"
if ! curl -s http://localhost:3100/api/status > /dev/null; then
    echo -e "${RED}❌ API server not running on port 3100${NC}"
    echo "Please start: cd ../core && python3 src/server.py"
    exit 1
fi
echo -e "${GREEN}✓ API server running${NC}"

# Check if UI dev server is running
echo -e "${YELLOW}Checking UI dev server...${NC}"
if ! curl -s http://localhost:5173 > /dev/null; then
    echo -e "${RED}❌ UI dev server not running on port 5173${NC}"
    echo "Please start: npm run dev"
    exit 1
fi
echo -e "${GREEN}✓ UI dev server running${NC}"

# Install dependencies if needed
if [ ! -d "node_modules/puppeteer" ]; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    npm install --save-dev puppeteer jest
fi

# Run tests
echo -e "${YELLOW}Running E2E tests...${NC}"
npm test

echo -e "${GREEN}✅ All tests completed${NC}"
