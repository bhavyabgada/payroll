#!/bin/bash
# Push Docker Images to GCR
# Payroll Analytics Platform

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=================================================="
echo "  Pushing Docker Images to GCR"
echo "=================================================="

# Get project ID from environment or use default
GCP_PROJECT_ID=${GCP_PROJECT_ID:-"payroll-analytics-dev"}
echo -e "${YELLOW}GCP Project ID: ${GCP_PROJECT_ID}${NC}"

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &>/dev/null; then
    echo -e "${RED}❌ Not authenticated with gcloud. Run: gcloud auth login${NC}"
    exit 1
fi

# Configure Docker for GCR
echo ""
echo -e "${YELLOW}Configuring Docker for GCR...${NC}"
gcloud auth configure-docker

# Push Airflow image
echo ""
echo -e "${GREEN}1/2 Pushing Airflow image...${NC}"
docker push gcr.io/$GCP_PROJECT_ID/airflow:latest

# Push Utils image
echo ""
echo -e "${GREEN}2/2 Pushing Utils image...${NC}"
docker push gcr.io/$GCP_PROJECT_ID/utils:latest

echo ""
echo -e "${GREEN}✅ Push complete!${NC}"
echo ""
echo "Images available at:"
echo "  - gcr.io/$GCP_PROJECT_ID/airflow:latest"
echo "  - gcr.io/$GCP_PROJECT_ID/utils:latest"

