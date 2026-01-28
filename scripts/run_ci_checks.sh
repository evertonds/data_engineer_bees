#!/bin/bash

# Script to run CI checks locally before committing
# Usage: ./scripts/run_ci_checks.sh

set -e

echo "🚀 Running CI checks locally..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if in project root
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Must be run from project root${NC}"
    exit 1
fi

# 1. Code Formatting
echo -e "${YELLOW}📝 Checking code formatting with Black...${NC}"
if black --check --diff src/ tests/ dags/ 2>/dev/null; then
    echo -e "${GREEN}✅ Black formatting check passed${NC}"
else
    echo -e "${RED}❌ Black formatting check failed${NC}"
    echo "Run: black src/ tests/ dags/"
    exit 1
fi
echo ""

# 2. Import Sorting
echo -e "${YELLOW}📦 Checking import sorting with isort...${NC}"
if isort --check-only --diff src/ tests/ dags/ 2>/dev/null; then
    echo -e "${GREEN}✅ isort check passed${NC}"
else
    echo -e "${RED}❌ isort check failed${NC}"
    echo "Run: isort src/ tests/ dags/"
    exit 1
fi
echo ""

# 3. Linting
echo -e "${YELLOW}🔍 Linting with flake8...${NC}"
if flake8 src/ tests/ dags/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
    echo -e "${GREEN}✅ flake8 critical errors check passed${NC}"
else
    echo -e "${RED}❌ flake8 found critical errors${NC}"
    exit 1
fi

# Run full flake8 (warnings only)
flake8 src/ tests/ dags/ --count --exit-zero --max-complexity=10 --max-line-length=120 --statistics
echo -e "${GREEN}✅ flake8 linting completed${NC}"
echo ""

# 4. Tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
if docker exec data_engineer_bees-airflow-webserver-1 pytest /opt/airflow/tests/ -v 2>/dev/null; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed${NC}"
    exit 1
fi
echo ""

# 5. Security Check (optional)
echo -e "${YELLOW}🔒 Running security checks...${NC}"
if command -v safety &> /dev/null; then
    safety check --json || echo -e "${YELLOW}⚠️  Security vulnerabilities found (non-blocking)${NC}"
else
    echo -e "${YELLOW}⚠️  safety not installed, skipping security check${NC}"
fi
echo ""

# Summary
echo -e "${GREEN}✅ All CI checks passed!${NC}"
echo ""
echo "You can now commit and push your changes:"
echo "  git add ."
echo "  git commit -m \"your message\""
echo "  git push"
