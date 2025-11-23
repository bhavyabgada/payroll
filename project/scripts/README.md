# Utility Scripts

This directory contains setup, deployment, and utility scripts for the payroll platform.

## Structure

```
scripts/
├── setup/
│   ├── 01_generate_test_data.sh       # Generate synthetic data (Module A)
│   ├── 02_create_datasets.sh          # Create BigQuery datasets
│   ├── 03_setup_airflow.sh            # Initialize local Airflow
│   └── 04_init_great_expectations.sh  # Setup GE context
├── deploy/
│   ├── deploy_dataform.sh             # Deploy SQLX to BigQuery
│   └── deploy_airflow_dags.sh         # Deploy DAGs to Airflow
└── utilities/
    ├── backfill.sh                    # Backfill utility for date ranges
    └── rollback.sh                    # Rollback to previous snapshot
```

## Setup Scripts (One-time)

Run these in order for initial setup:

```bash
cd scripts/setup

# 1. Generate synthetic test data
./01_generate_test_data.sh

# 2. Create BigQuery datasets (dev/test/prod)
./02_create_datasets.sh --env dev

# 3. Setup local Airflow
./03_setup_airflow.sh

# 4. Initialize Great Expectations
./04_init_great_expectations.sh
```

## Deployment Scripts

```bash
cd scripts/deploy

# Deploy Dataform to dev
./deploy_dataform.sh --env dev

# Deploy Airflow DAGs
./deploy_airflow_dags.sh --env dev
```

## Utility Scripts

```bash
cd scripts/utilities

# Backfill date range
./backfill.sh 2024-01-01 2024-01-31 staging

# Rollback to snapshot
./rollback.sh --snapshot dim_employee_snapshot_20250123
```

## Script Conventions

- All scripts are idempotent (safe to re-run)
- Use `set -e` (fail on error)
- Accept `--env` flag for environment (dev/test/prod)
- Log output to `logs/` directory
- Exit with meaningful error messages

