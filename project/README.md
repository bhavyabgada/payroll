# Payroll Lakehouse GCP

**Enterprise Payroll Lakehouse → Warehouse Modernization on GCP with DataOps, FinOps, and Privacy-Safe Analytics**

## Overview

This is the main implementation project that uses the reusable OSS modules to build a Fortune-500 scale payroll analytics platform.

## Architecture

See [/docs/README.md](/docs/README.md) in the root for complete technical design specification.

## Project Structure

```
project/
├── airflow/              # Airflow DAGs and orchestration
├── dataform/             # Dataform SQLX definitions
├── config/               # Configuration files (YAML)
├── scripts/              # Setup and utility scripts
├── tests/                # Integration tests
├── terraform/            # Infrastructure as Code (optional)
├── reports/              # Generated reports and dashboards
└── docs/                 # Project-specific documentation
```

## Dependencies

This project uses the following modules:
- `synthetic-payroll-lab==0.1.0` - Test data generation
- `scd2-bq-engine==0.1.0` - SCD2 dimension templates
- `bq-finops-cli==0.1.0` - Cost monitoring

Plus Dataform Warehouse Blueprints template (initialized in `/dataform`)

## Quick Start

See `/docs/GETTING_STARTED.md` for setup instructions.

## Success Metrics

| Metric | Baseline | Target | Status |
|--------|----------|--------|--------|
| Freshness | T+3 days | T+0 by 9 AM | 🚧 In Progress |
| Pipeline Runtime | 3-5 hours | < 60 min | 🚧 In Progress |
| DQ Block Rate | 0% | 90% pre-prod | 🚧 In Progress |
| Cost Reduction | Baseline | 30-60% | 🚧 In Progress |
| PII Storage | 12 tables | 3-4 tables | 🚧 In Progress |

## License

MIT - see [LICENSE](LICENSE)

