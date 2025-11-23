#!/bin/bash
# Build Docker Images
# Payroll Analytics Platform

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=================================================="
echo "  Building Docker Images"
echo "=================================================="

# Get project ID from environment or use default
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"payroll-analytics-dev"}
echo -e "${YELLOW}GCP Project ID: ${GCP_PROJECT_ID}${NC}"

# Build Airflow image
echo ""
echo -e "${GREEN}1/2 Building Airflow image...${NC}"
docker build -f Dockerfile.airflow -t payroll/airflow:latest -t gcr.io/$GCP_PROJECT_ID/airflow:latest ..

# Build Utils image
echo ""
echo -e "${GREEN}2/2 Building Utils image...${NC}"
docker build -f Dockerfile.utils -t payroll/utils:latest -t gcr.io/$GCP_PROJECT_ID/utils:latest ..

echo ""
echo -e "${GREEN}✅ Build complete!${NC}"
echo ""
echo "Local tags:"
echo "  - payroll/airflow:latest"
echo "  - payroll/utils:latest"
echo ""
echo "GCR tags:"
echo "  - gcr.io/$GCP_PROJECT_ID/airflow:latest"
echo "  - gcr.io/$GCP_PROJECT_ID/utils:latest"
echo ""
echo "To push to GCR:"
echo "  ./push.sh"

