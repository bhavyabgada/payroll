#!/bin/bash
# Test Runner Script
# Runs all tests for the Payroll Analytics Platform

set -e  # Exit on error

echo "=================================================="
echo "  Payroll Analytics Platform - Test Suite"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

echo ""
echo "Project Directory: $PROJECT_DIR"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo -e "${YELLOW}⚠️  pytest not found. Installing...${NC}"
    pip install pytest pytest-mock pytest-cov
fi

# Run tests
echo -e "${YELLOW}🧪 Running Tests...${NC}"
echo ""

# Test 1: Data Quality Checks
echo "1️⃣  Testing Data Quality Scripts..."
pytest "$SCRIPT_DIR/test_data_quality_checks.py" -v --tb=short || true
echo ""

# Test 2: FinOps Monitoring
echo "2️⃣  Testing FinOps Monitoring..."
pytest "$SCRIPT_DIR/test_finops_monitoring.py" -v --tb=short || true
echo ""

# Test 3: Airflow DAGs
echo "3️⃣  Testing Airflow DAGs..."
pytest "$SCRIPT_DIR/test_airflow_dags.py" -v --tb=short || true
echo ""

# Test 4: Dataform SQLX
echo "4️⃣  Testing Dataform SQLX Files..."
pytest "$SCRIPT_DIR/test_dataform_sqlx.py" -v --tb=short
echo ""

# Run all tests with coverage
echo "=================================================="
echo "  Running Full Test Suite with Coverage"
echo "=================================================="
pytest "$SCRIPT_DIR" -v --cov="$PROJECT_DIR/scripts" --cov-report=term-missing --cov-report=html

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "📊 Coverage report: htmlcov/index.html"
    exit 0
else
    echo ""
    echo -e "${RED}❌ Some tests failed!${NC}"
    exit 1
fi

