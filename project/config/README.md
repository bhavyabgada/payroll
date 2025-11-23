# Configuration Files

This directory contains all configuration files for the payroll data platform.

## Structure

```
config/
├── synthetic_payroll_config.yaml      # Module A: Test data generation config
├── finops_rules.yaml                   # Module D: Cost optimization rules
├── dimensions/
│   ├── dim_employee_scd2.yaml         # Module B: SCD2 config for employee dim
│   └── dim_job_scd1.yaml              # Module B: Type 1 config for job dim
├── great_expectations/
│   ├── great_expectations.yml         # GE context config
│   └── checkpoints/
│       ├── raw_checkpoint.yml         # Post-ingestion validation
│       ├── staging_checkpoint.yml     # Post-staging validation
│       └── warehouse_checkpoint.yml   # Post-warehouse validation
├── environments/
│   ├── dev.yaml                       # Dev environment config
│   ├── test.yaml                      # Test environment config
│   └── prod.yaml                      # Prod environment config
└── datasets.yaml                      # BigQuery dataset definitions
```

## Configuration Strategy

- **Environment-specific**: `environments/{env}.yaml` for GCP project IDs, dataset names
- **Module configs**: Configs for OSS modules (synthetic data, SCD2, FinOps)
- **Data Quality**: Great Expectations checkpoints and suites
- **Secrets**: NOT stored in git; use Secret Manager or `.env` files (gitignored)

## Usage

```bash
# Generate test data
synthetic-payroll generate --config config/synthetic_payroll_config.yaml

# Generate SCD2 dimension
scd2-bq generate --config config/dimensions/dim_employee_scd2.yaml

# Run FinOps scan
bq-finops detect --rules config/finops_rules.yaml
```

## Environment Variables

Required environment variables (set in `.env` or export):

```bash
export GCP_PROJECT_ID="payroll-analytics-prod"
export GCP_LOCATION="US"
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

