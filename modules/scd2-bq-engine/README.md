# SCD2 BigQuery Engine

**Version**: 0.1.0  
**License**: MIT  
**Status**: ✅ Production Ready

## Overview

BigQuery-first SCD Type 2 dimension builder with SQLX template generation for Dataform/dbt.

Generates production-ready SQLX files that implement full SCD Type 2 logic including:
- Hash-based change detection
- Effective date tracking
- Soft deletes
- Late arrival handling
- BigQuery optimizations (partitioning, clustering)

## Why This Module?

- dbt snapshots are dbt-locked and Snowflake-optimized
- Existing SCD2 tutorials use stored procedures (hard to version control)
- No declarative, config-driven SCD2 solution for BigQuery

## Features (v0.1.0 MVP)

- ✅ SQLX template generator for standard SCD2 pattern
- ✅ Hash-based change detection (MD5/SHA256)
- ✅ Effective dating with late arrival handling
- ✅ Soft delete support
- ✅ YAML config → SQLX output
- ✅ CLI + Python API

## Quick Start

### Installation
```bash
pip install scd2-bq-engine
```

### Initialize Configuration
```bash
# Create a new dimension configuration
scd2-bq init dim_employee \
    --source-table project.dataset.stg_employees \
    --business-keys employee_number \
    --tracked-columns first_name,last_name,job_code,department
```

### Generate SQLX
```bash
# Generate SCD2 dimension SQLX file
scd2-bq generate \
    --config dim_employee_config.yaml \
    --output-file dim_employee.sqlx
```

### Python API
```python
from scd2_bq_engine import SCD2Generator, SCD2Config

# Create configuration
config = SCD2Config(
    dimension_name="dim_employee",
    source_table="project.dataset.stg_employees",
    business_keys=["employee_number"],
    tracked_columns=["first_name", "last_name", "job_code"]
)

# Generate SQLX
generator = SCD2Generator(config)
generator.write_sqlx("dim_employee.sqlx")
```

## Directory Structure

```
scd2-bq-engine/
├── src/scd2_bq_engine/
│   ├── generator.py          # Core SQLX generator
│   ├── templates/            # Jinja2 SQLX templates
│   └── validators.py         # Config validation
├── tests/
├── examples/
└── docs/
```

## License

MIT - see [LICENSE](LICENSE)

