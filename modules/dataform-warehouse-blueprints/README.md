# Dataform Warehouse Blueprints

**Production-ready Dataform SQLX templates for data warehouse patterns**

Generate clean, maintainable Dataform SQLX files from simple YAML configurations. Supports staging, dimension, fact, and aggregate table patterns with best practices built-in.

[![PyPI version](https://badge.fury.io/py/dataform-warehouse-blueprints.svg)](https://badge.fury.io/py/dataform-warehouse-blueprints)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Features

- **Multiple Table Patterns**: Staging, Dimension, Fact, Aggregate/Mart tables
- **Best Practices**: Partitioning, clustering, incremental loading built-in
- **Simple YAML Config**: Define tables without writing boilerplate SQL
- **CLI & Python API**: Use as command-line tool or Python library
- **Validation**: Catch configuration errors before generation
- **Batch Generation**: Process multiple configs at once
- **Dataform-Ready**: Generates valid SQLX for Dataform projects

## 📦 Installation

```bash
pip install dataform-warehouse-blueprints
```

## 🚀 Quick Start

### CLI Usage

**1. Initialize a configuration file:**

```bash
dataform-blueprints init \
  -t dim_employee \
  -l warehouse \
  --table-type dimension \
  -o dim_employee_config.yaml
```

**2. Edit the generated YAML:**

```yaml
table_name: dim_employee
layer: warehouse
table_type: dimension
source_table: ${ref('stg_employees')}
columns:
  - employee_id
  - first_name
  - last_name
  - email
partition_by: updated_at
cluster_by: [employee_id]
primary_keys: [employee_id]
incremental: true
tags: [dimension, hr]
```

**3. Generate SQLX:**

```bash
dataform-blueprints generate \
  -c dim_employee_config.yaml \
  -o definitions/dim_employee.sqlx
```

**4. Generated SQLX output:**

```sql
config {
  type: "incremental",
  schema: "warehouse",
  name: "dim_employee",
  bigquery: {
    partitionBy: "updated_at",
    clusterBy: ["employee_id"],
  },
  tags: ["dimension", "hr"],
}

-- Dimension Table: dim_employee
-- Layer: WAREHOUSE (Gold)

SELECT
  employee_id,
  first_name,
  last_name,
  email,
  CURRENT_TIMESTAMP() AS _loaded_at
FROM ${ref('stg_employees')}

${ when(incremental(), `
  WHERE updated_at > (SELECT MAX(updated_at) FROM ${self()})
`) }
```

### Python API

```python
from dataform_blueprints import TableConfig, BlueprintGenerator, LayerType, TableType

# Define configuration
config = TableConfig(
    table_name="dim_employee",
    layer=LayerType.WAREHOUSE,
    table_type=TableType.DIMENSION,
    source_table="${ref('stg_employees')}",
    columns=["employee_id", "first_name", "last_name"],
    primary_keys=["employee_id"],
    partition_by="updated_at",
    cluster_by=["employee_id"],
    incremental=True,
    tags=["dimension", "hr"]
)

# Generate SQLX
generator = BlueprintGenerator(config)
sqlx_content = generator.generate_sqlx()

# Write to file
generator.write_sqlx("definitions/dim_employee.sqlx")
```

## 📚 Table Patterns

### 1. Staging Tables (Raw → Staging)

Clean and standardize data from raw sources.

```yaml
table_name: stg_employees
layer: staging
table_type: source
source_table: ${ref('raw_employees')}
columns:
  - employee_id
  - first_name
  - last_name
incremental: true
```

### 2. Dimension Tables (SCD Type 1)

Business entities for analytics.

```yaml
table_name: dim_employee
layer: warehouse
table_type: dimension
source_table: ${ref('stg_employees')}
columns:
  - employee_id
  - first_name
  - last_name
primary_keys: [employee_id]
partition_by: updated_at
cluster_by: [employee_id]
```

### 3. Fact Tables

Transactional business events.

```yaml
table_name: fact_payroll_run
layer: warehouse
table_type: fact
source_table: ${ref('stg_payroll')}
columns:
  - payroll_id
  - employee_id
  - gross_pay
  - net_pay
primary_keys: [payroll_id]
partition_by: pay_date
cluster_by: [employee_id, pay_date]
```

### 4. Aggregate/Mart Tables

Pre-aggregated data for reporting.

```yaml
table_name: mart_payroll_summary
layer: marts
table_type: aggregate
source_table: ${ref('fact_payroll_run')}
columns:
  - department
  - SUM(gross_pay) as total_pay
  - COUNT(*) as payroll_count
primary_keys: [department]
```

## 🛠️ CLI Commands

### `init` - Create Configuration

```bash
dataform-blueprints init -t <table_name> -l <layer> --table-type <type>
```

Options:
- `-t, --table-name`: Table name (required)
- `-l, --layer`: Layer (raw/staging/warehouse/marts) (required)
- `--table-type`: Pattern (source/dimension/fact/aggregate) (required)
- `-o, --output`: Output file path (default: table_config.yaml)

### `generate` - Generate SQLX

```bash
dataform-blueprints generate -c <config.yaml> -o <output.sqlx>
```

Options:
- `-c, --config`: YAML config file (required)
- `-o, --output`: Output SQLX file
- `--validate-only`: Only validate, don't generate

### `batch` - Batch Generate

```bash
dataform-blueprints batch -d <configs_dir> -o <output_dir>
```

Options:
- `-d, --directory`: Directory with YAML configs (required)
- `-o, --output-dir`: Output directory (default: definitions)

### `examples` - Show Examples

```bash
dataform-blueprints examples
```

## 📋 Configuration Reference

### Required Fields

```yaml
table_name: string       # Table name
layer: string           # raw | staging | warehouse | marts
table_type: string      # source | dimension | fact | aggregate | view
columns: list           # Column names
```

### Optional Fields

```yaml
source_table: string         # Source table reference (e.g., ${ref('table')})
partition_by: string         # Partition column
cluster_by: list            # Clustering columns
primary_keys: list          # Primary key columns
description: string         # Table description
tags: list                  # Tags for organization
incremental: bool           # Enable incremental (default: true)
dataset_id: string          # Override default dataset
dependencies: list          # Explicit dependencies
assertions: list            # Data quality assertions
```

## 🎯 Use Cases

### Data Warehouse Modernization

Generate consistent SQLX files across your entire warehouse:

```bash
# Generate all staging tables
dataform-blueprints batch -d configs/staging -o definitions/staging

# Generate all dimensions
dataform-blueprints batch -d configs/dimensions -o definitions/warehouse

# Generate all facts
dataform-blueprints batch -d configs/facts -o definitions/warehouse
```

### Rapid Prototyping

Quickly scaffold new tables:

```bash
dataform-blueprints init -t fact_sales -l warehouse --table-type fact
# Edit config...
dataform-blueprints generate -c fact_sales.yaml
```

### CI/CD Integration

Validate configs in CI:

```bash
dataform-blueprints generate -c dim_employee.yaml --validate-only
```

## 🔧 Development

### Setup

```bash
git clone https://github.com/yourusername/dataform-warehouse-blueprints.git
cd dataform-warehouse-blueprints
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=dataform_blueprints
```

### Code Quality

```bash
black src/
flake8 src/
```

## 📖 Examples

See the `examples/` directory for:
- `dim_employee_config.yaml` - Dimension table
- `fact_payroll_config.yaml` - Fact table
- `mart_payroll_summary_config.yaml` - Aggregate table

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- **PyPI**: https://pypi.org/project/dataform-warehouse-blueprints/
- **GitHub**: https://github.com/yourusername/dataform-warehouse-blueprints
- **Documentation**: https://github.com/yourusername/dataform-warehouse-blueprints#readme

## 💡 Why Dataform Blueprints?

- **Consistency**: Standardize table patterns across your warehouse
- **Speed**: Generate tables 10x faster than writing SQL by hand
- **Best Practices**: Partitioning, clustering, incremental built-in
- **Maintainability**: YAML configs easier to review than SQL
- **Reusability**: Share table patterns across projects/teams

## 🎓 Related Projects

This module is part of the **Payroll & Workforce Analytics Modernization** project:
- `synthetic-payroll-lab` - Generate test data
- `scd2-bq-engine` - SCD Type 2 automation
- `bq-finops-cli` - BigQuery cost optimization

---

**Built with ❤️ for data engineers who value clean, maintainable SQL.**
