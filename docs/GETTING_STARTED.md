# Getting Started

Quick start guide for setting up the payroll lakehouse data engineering project.

## Prerequisites

### Required
- **Python 3.9+** - For all modules and Airflow
- **Node.js 16+** - For Dataform
- **GCP Account** - With billing enabled
- **gcloud CLI** - Authenticated to your project
- **Git** - Version control

### Optional
- **Docker & Docker Compose** - For local Airflow
- **Terraform** - For IaC (optional for MVP)
- **Make** - For convenience commands

## Quick Start (5 Minutes)

```bash
# 1. Clone repository
cd /path/to/your/workspace
# (Repository already initialized at /Applications/MAMP/htdocs/dataengineeringprojects/projects/payroll)

# 2. Set up Python environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install modules (once we build them)
cd modules/synthetic-payroll-lab
pip install -e .
cd ../..

# 4. Set environment variables
cp .env.example .env
# Edit .env with your GCP project ID

# 5. Generate test data
cd project
synthetic-payroll generate \
    --config config/synthetic_payroll_config.yaml \
    --output-dir landing \
    --employees 1000 \
    --start-date 2024-01-01 \
    --end-date 2024-01-31
```

## Development Setup (Full)

### Step 1: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install development tools
pip install black flake8 pytest pytest-cov mypy
```

### Step 2: Install Modules (Development Mode)

```bash
# Install each module in editable mode
cd modules/synthetic-payroll-lab
pip install -e ".[dev]"
cd ../..

cd modules/scd2-bq-engine
pip install -e ".[dev]"
cd ../..

cd modules/bq-finops-cli
pip install -e ".[dev]"
cd ../..

# Install project dependencies
cd project
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Step 3: Configure GCP

```bash
# Authenticate with GCP
gcloud auth login
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable dataform.googleapis.com
```

### Step 4: Create Environment File

```bash
# Create .env file in project root
cat > project/.env << EOF
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=US
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Environment
ENV=dev

# BigQuery Datasets
DATASET_RAW=payroll_raw_dev
DATASET_STAGING=payroll_staging_dev
DATASET_WAREHOUSE=payroll_warehouse_dev
DATASET_MARTS=payroll_marts_dev
EOF
```

### Step 5: Run Setup Scripts

```bash
cd project/scripts/setup

# 1. Generate synthetic test data
./01_generate_test_data.sh

# 2. Create BigQuery datasets
./02_create_datasets.sh --env dev

# 3. Set up local Airflow (optional)
./03_setup_airflow.sh

# 4. Initialize Great Expectations
./04_init_great_expectations.sh
```

## Directory Navigation

```
Current directory structure:
payroll/
├── docs/               ← You are here (GETTING_STARTED.md)
├── modules/            ← OSS modules (4 packages)
└── project/            ← Main implementation
```

## Development Workflow

### Phase 0: Module Development (Current)

```bash
# Work on Module A (synthetic data)
cd modules/synthetic-payroll-lab

# Run tests
pytest

# Run linting
black src/ tests/
flake8 src/ tests/

# Build package
python setup.py sdist bdist_wheel
```

### Phase 1: Data Generation

```bash
# Generate synthetic data
cd project
synthetic-payroll generate \
    --config config/synthetic_payroll_config.yaml \
    --output-dir landing \
    --employees 50000

# Upload to GCS
gsutil -m cp -r landing/* gs://payroll-landing-dev/
```

### Phase 2: Dataform Development

```bash
# Navigate to dataform
cd project/dataform

# Install dependencies
npm install

# Compile SQLX
dataform compile

# Run in dev
dataform run --env dev
```

### Phase 3: Airflow Development

```bash
# Start local Airflow
cd project/airflow
docker-compose up -d

# Access UI
open http://localhost:8080
# Credentials: airflow / airflow

# Trigger DAG
airflow dags trigger payroll_ingestion
```

## Testing

```bash
# Run all tests
cd project
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Open coverage report
open htmlcov/index.html
```

## Common Tasks

### Generate Test Data (Different Sizes)

```bash
# Small (for unit tests)
synthetic-payroll generate --employees 100 --output-dir test_data

# Medium (for dev)
synthetic-payroll generate --employees 10000 --output-dir landing

# Large (for staging)
synthetic-payroll generate --employees 50000 --output-dir landing
```

### Create BigQuery Datasets

```bash
cd project/scripts/setup
./02_create_datasets.sh --env dev
```

### Deploy Dataform

```bash
cd project/scripts/deploy
./deploy_dataform.sh --env dev
```

### Run FinOps Report

```bash
bq-finops report \
    --project your-project-id \
    --start-date 2024-01-01 \
    --end-date 2024-01-31
```

### Backfill Data

```bash
cd project/scripts/utilities
./backfill.sh 2024-01-01 2024-01-31 staging
```

## Troubleshooting

### "Module not found" errors

```bash
# Reinstall in editable mode
pip install -e modules/synthetic-payroll-lab/
```

### GCP authentication issues

```bash
# Re-authenticate
gcloud auth application-default login
```

### Airflow not starting

```bash
# Check Docker
docker-compose ps

# View logs
docker-compose logs airflow-webserver
```

### BigQuery quota exceeded

```bash
# Check quotas
gcloud compute project-info describe --project=YOUR_PROJECT_ID

# Request increase via GCP Console
```

## Next Steps

1. **Read the master spec**: `/README.md`
2. **Review architecture**: `/project/docs/architecture.md`
3. **Follow roadmap**: `/docs/EXECUTION_ROADMAP.md`
4. **Start Phase 0**: Build Module A (synthetic data generator)

## Getting Help

- **Documentation**: `/docs/` and `/project/docs/`
- **Runbook**: `/project/docs/runbook.md` (operational issues)
- **Architecture**: `/README.md` (complete technical design)

## Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Dataform Documentation](https://cloud.google.com/dataform/docs)
- [Apache Airflow Documentation](https://airflow.apache.org/docs/)
- [Great Expectations Documentation](https://docs.greatexpectations.io/)

---

**Status**: ✅ Directory structure created, ready for Phase 0 development

**Current Phase**: Phase 0 - Module development (see `/docs/EXECUTION_ROADMAP.md`)

