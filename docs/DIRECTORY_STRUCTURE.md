# Directory Structure

This repository contains both the OSS modules and the main payroll lakehouse project.

## Root Structure

```
/payroll/                                   # Root directory
├── README.md                               # Master README (technical design spec)
├── docs/                                   # Master documentation
│   ├── DIRECTORY_STRUCTURE.md             # This file
│   ├── GETTING_STARTED.md                 # Setup guide
│   └── EXECUTION_ROADMAP.md               # Implementation phases
│
├── modules/                                # Open-source reusable modules
│   ├── synthetic-payroll-lab/             # Module A: Test data generator
│   ├── scd2-bq-engine/                    # Module B: SCD2 templates
│   ├── dataform-warehouse-blueprints/     # Module C: Dataform templates
│   └── bq-finops-cli/                     # Module D: FinOps toolkit
│
└── project/                                # Main project: payroll-lakehouse-gcp
    ├── README.md                           # Project-specific README
    ├── airflow/                            # Airflow DAGs
    ├── dataform/                           # Dataform SQLX definitions
    ├── config/                             # Configuration files
    ├── scripts/                            # Utility scripts
    ├── tests/                              # Integration tests
    ├── terraform/                          # Infrastructure as Code
    ├── reports/                            # Generated reports
    └── docs/                               # Project-specific documentation
```

## Separation of Concerns

- **modules/**: Reusable, publishable OSS packages (can be extracted to separate repos later)
- **project/**: The main payroll lakehouse implementation that uses the modules
- **docs/**: Master-level documentation (architecture, design decisions)
- **project/docs/**: Project-specific operational docs (runbooks, deployment guides)

## Next Steps

See `docs/GETTING_STARTED.md` for setup instructions.

