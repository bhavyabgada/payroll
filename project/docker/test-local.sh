#!/bin/bash
# Local Testing Script
# Tests the entire platform locally using Docker Compose

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo "════════════════════════════════════════════════════════════════"
echo -e "${BLUE}  🧪 Payroll Analytics Platform - Local Testing${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Step 1: Check if images exist
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}📦 Step 1: Checking Docker Images${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if docker images | grep -q "payroll/airflow"; then
    echo -e "${GREEN}✅ Airflow image exists${NC}"
else
    echo -e "${YELLOW}⚠️  Airflow image not found. Building...${NC}"
    ./build.sh
fi

if docker images | grep -q "payroll/utils"; then
    echo -e "${GREEN}✅ Utils image exists${NC}"
else
    echo -e "${YELLOW}⚠️  Utils image not found. Building...${NC}"
    ./build.sh
fi

echo ""

# Step 2: Generate test data
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}📊 Step 2: Generating Test Data${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_DATA_DIR="$SCRIPT_DIR/test-data"
mkdir -p "$TEST_DATA_DIR"

echo "Generating 1,000 employee records..."
docker run --rm -v "$TEST_DATA_DIR:/data" payroll/utils:latest \
    synthetic-payroll generate \
    --num-employees 1000 \
    --output-dir /data \
    --format csv 2>/dev/null || true

if [ -f "$TEST_DATA_DIR/employees.csv" ]; then
    echo -e "${GREEN}✅ Test data generated${NC}"
    echo "   - $(wc -l < "$TEST_DATA_DIR/employees.csv") employee records"
    echo "   - $(wc -l < "$TEST_DATA_DIR/jobs.csv") job records"
    echo "   - $(wc -l < "$TEST_DATA_DIR/payroll_runs.csv") payroll records"
else
    echo -e "${YELLOW}⚠️  Test data generation skipped (module might need installation)${NC}"
fi

echo ""

# Step 3: Start Docker Compose
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🐳 Step 3: Starting Docker Compose${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Set AIRFLOW_UID
export AIRFLOW_UID=$(id -u)
echo "AIRFLOW_UID=$AIRFLOW_UID" > .env

echo "Starting services..."
docker-compose up -d

echo ""
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Step 4: Check service status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}🔍 Step 4: Service Status${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker-compose ps

echo ""

# Step 5: Wait for Airflow to be ready
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${YELLOW}⏳ Step 5: Waiting for Airflow to be ready...${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Airflow is ready!${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Airflow taking longer than expected. Check logs:${NC}"
    echo "   docker-compose logs airflow-webserver"
fi

echo ""

# Step 6: Show access information
echo "════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ LOCAL TESTING ENVIRONMENT READY!${NC}"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}📱 Access Points:${NC}"
echo "   Airflow UI:     http://localhost:8080"
echo "   Username:       airflow"
echo "   Password:       airflow"
echo ""
echo -e "${BLUE}🔧 Useful Commands:${NC}"
echo "   View logs:      docker-compose logs -f"
echo "   Stop services:  docker-compose down"
echo "   Restart:        docker-compose restart"
echo "   Shell access:   docker-compose exec airflow-webserver bash"
echo ""
echo -e "${BLUE}📊 Test Data:${NC}"
echo "   Location:       $TEST_DATA_DIR"
echo "   Files:          employees.csv, jobs.csv, payroll_runs.csv"
echo ""
echo -e "${BLUE}🧪 Next Steps:${NC}"
echo "   1. Open http://localhost:8080 in your browser"
echo "   2. Login with airflow/airflow"
echo "   3. Enable and trigger 'generate_test_data' DAG"
echo "   4. Enable and trigger 'payroll_main_pipeline' DAG"
echo "   5. Monitor execution in Airflow UI"
echo ""
echo -e "${YELLOW}💡 Tip: Press Ctrl+C to view logs, or run:${NC}"
echo "   docker-compose logs -f airflow-scheduler"
echo ""
echo "════════════════════════════════════════════════════════════════"

