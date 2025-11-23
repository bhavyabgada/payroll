# BQ FinOps CLI

**BigQuery cost monitoring and optimization toolkit for data engineers**

Monitor BigQuery costs, analyze usage patterns, and optimize table structures with a simple command-line interface.

[![PyPI version](https://badge.fury.io/py/bq-finops-cli.svg)](https://badge.fury.io/py/bq-finops-cli)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Features

- **Cost Analysis**: Analyze BigQuery costs over time periods
- **Query Insights**: Identify expensive queries and usage patterns
- **Table Analysis**: Evaluate table structure and optimization opportunities
- **Optimization Recommendations**: Get actionable suggestions for cost reduction
- **DDL Generation**: Auto-generate partitioning/clustering DDL
- **Multi-dimensional Breakdown**: Costs by dataset, user, table
- **CLI & Python API**: Use as command-line tool or import as library

## 📦 Installation

```bash
pip install bq-finops-cli
```

**Requirements:**
- Python 3.8+
- GCP credentials with BigQuery access
- BigQuery API enabled in your project

## 🚀 Quick Start

### 1. Setup Authentication

```bash
# Set up GCP credentials
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

### 2. Analyze Costs

```bash
# Analyze costs for the last 30 days
bq-finops analyze costs -p my-gcp-project

# Analyze specific date range
bq-finops analyze costs -p my-project \
  --start-date 2025-01-01 \
  --end-date 2025-01-31
```

**Sample Output:**

```
============================================================
💰 COST SUMMARY
============================================================
Total Cost (USD)        $1,234.56
Query Count             15,432
Avg Cost per Query      $0.0800
Total Bytes Processed   987,654,321,098

============================================================
🔥 TOP EXPENSIVE QUERIES
============================================================
╔══════════════════════╦════════════════════════╦═════════════╦══════════════╗
║ Job ID               ║ User                   ║ Cost        ║ Bytes        ║
╠══════════════════════╬════════════════════════╬═════════════╬══════════════╣
║ job_abc123...        ║ user@example.com       ║ $125.50     ║ 20,123,456   ║
║ job_def456...        ║ analyst@example.com    ║ $98.30      ║ 15,789,012   ║
╚══════════════════════╩════════════════════════╩═════════════╩══════════════╝
```

### 3. Analyze a Table

```bash
bq-finops analyze table -p my-project -d warehouse -t fact_sales
```

### 4. Generate Optimization Report

```bash
bq-finops optimize report -p my-project -d warehouse -t fact_sales
```

### 5. Generate DDL

```bash
# Add partitioning
bq-finops optimize generate-ddl -p my-project \
  -d warehouse -t fact_sales \
  --partition-column sale_date

# Add partitioning + clustering
bq-finops optimize generate-ddl -p my-project \
  -d warehouse -t fact_sales \
  --partition-column sale_date \
  --cluster-columns customer_id \
  --cluster-columns product_id
```

## 📚 Commands

### Analyze Commands

#### `bq-finops analyze costs`
Analyze BigQuery costs over a time period.

**Options:**
- `-p, --project-id`: GCP project ID (required)
- `-s, --start-date`: Start date (YYYY-MM-DD)
- `-e, --end-date`: End date (YYYY-MM-DD)
- `-d, --datasets`: Filter by datasets (multiple allowed)
- `-f, --format`: Output format (table/json)

**Examples:**
```bash
# Last 30 days (default)
bq-finops analyze costs -p my-project

# Specific date range
bq-finops analyze costs -p my-project \
  --start-date 2025-01-01 --end-date 2025-01-31

# Specific datasets
bq-finops analyze costs -p my-project \
  -d warehouse -d marts

# JSON output
bq-finops analyze costs -p my-project --format json
```

#### `bq-finops analyze table`
Analyze a specific table for optimization opportunities.

**Options:**
- `-p, --project-id`: GCP project ID (required)
- `-d, --dataset-id`: Dataset ID (required)
- `-t, --table-id`: Table ID (required)

**Example:**
```bash
bq-finops analyze table -p my-project -d warehouse -t dim_employee
```

### Optimize Commands

#### `bq-finops optimize report`
Generate optimization report with recommendations.

**Options:**
- `-p, --project-id`: GCP project ID (required)
- `-d, --dataset-id`: Dataset ID (required)
- `-t, --table-id`: Table ID (required)

**Example:**
```bash
bq-finops optimize report -p my-project -d warehouse -t fact_payroll
```

#### `bq-finops optimize generate-ddl`
Generate DDL for table optimization.

**Options:**
- `-p, --project-id`: GCP project ID (required)
- `-d, --dataset-id`: Dataset ID (required)
- `-t, --table-id`: Table ID (required)
- `--partition-column`: Column to partition by
- `--cluster-columns`: Columns to cluster by (multiple allowed)

**Examples:**
```bash
# Partition only
bq-finops optimize generate-ddl -p my-project \
  -d warehouse -t fact_sales \
  --partition-column sale_date

# Cluster only
bq-finops optimize generate-ddl -p my-project \
  -d warehouse -t fact_sales \
  --cluster-columns customer_id --cluster-columns product_id

# Both
bq-finops optimize generate-ddl -p my-project \
  -d warehouse -t fact_sales \
  --partition-column sale_date \
  --cluster-columns customer_id --cluster-columns product_id
```

### Utility Commands

#### `bq-finops examples`
Show example commands.

#### `bq-finops --version`
Show version.

#### `bq-finops --help`
Show help.

## 🐍 Python API

Use BQ FinOps programmatically:

### Cost Analysis

```python
from bq_finops import CostAnalyzer

# Initialize analyzer
analyzer = CostAnalyzer(project_id="my-gcp-project")

# Analyze costs
report = analyzer.analyze_period(
    start_date="2025-01-01",
    end_date="2025-01-31",
    datasets=["warehouse", "marts"]
)

print(f"Total cost: ${report.total_cost:.2f}")
print(f"Query count: {report.query_count}")

# Analyze a specific table
table_analysis = analyzer.analyze_table("warehouse", "fact_sales")
print(f"Table size: {table_analysis['size_gb']} GB")

# Get dataset cost
dataset_cost = analyzer.get_dataset_cost("warehouse", days=30)
print(f"Dataset cost: ${dataset_cost['total_cost_usd']:.2f}")
```

### Query Optimization

```python
from bq_finops import QueryOptimizer

# Initialize optimizer
optimizer = QueryOptimizer(project_id="my-gcp-project")

# Generate partition DDL
ddl = optimizer.generate_partition_ddl(
    "warehouse",
    "fact_sales",
    "sale_date"
)
print(ddl)

# Generate cluster DDL
ddl = optimizer.generate_cluster_ddl(
    "warehouse",
    "fact_sales",
    ["customer_id", "product_id"],
    partition_column="sale_date"
)
print(ddl)

# Analyze a query
query = "SELECT * FROM `project.dataset.table` WHERE date > '2025-01-01'"
analysis = optimizer.analyze_query(query)
print(f"Recommendations: {analysis['recommendations']}")

# Generate optimization report
report = optimizer.generate_optimization_report("warehouse", "fact_sales")
print(f"Current state: {report['current_state']}")
print(f"Recommendations: {report['recommendations']}")
```

## 💰 Cost Optimization Tips

### 1. Partition Large Tables
- **Impact**: 50-90% cost reduction
- **Best for**: Tables > 1 GB with date/timestamp column
- **Recommended**: Partition by DATE or TIMESTAMP column

### 2. Cluster Frequently Filtered Columns
- **Impact**: 10-30% performance improvement
- **Best for**: Tables > 1 GB with common filter patterns
- **Recommended**: Cluster by 2-4 columns max

### 3. Set Data Retention Policies
- **Impact**: Reduces storage costs
- **Best for**: Time-series data
- **Recommended**: Set partition expiration (e.g., 90 days)

### 4. Avoid SELECT *
- **Impact**: 50-80% cost reduction per query
- **Recommendation**: Select only needed columns

### 5. Use Partition Filters
- **Impact**: 90%+ cost reduction per query
- **Recommendation**: Always filter on partition column

## 🎯 Use Cases

### FinOps Dashboard
Monitor monthly BigQuery spending:
```bash
# Get current month costs
bq-finops analyze costs -p my-project \
  --start-date 2025-11-01 \
  --format json > november_costs.json
```

### Optimization Audit
Audit all tables for optimization opportunities:
```bash
# Check each table
for table in fact_sales fact_orders fact_inventory; do
  bq-finops optimize report -p my-project -d warehouse -t $table
done
```

### CI/CD Integration
Add cost checks to your CI pipeline:
```bash
# Validate query before deployment
bq-finops analyze costs -p dev-project --format json | \
  jq '.total_cost < 100' # Fail if > $100
```

## 🔧 Development

### Setup

```bash
git clone https://github.com/yourusername/bq-finops-cli.git
cd bq-finops-cli
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=bq_finops
```

### Code Quality

```bash
black src/
flake8 src/
```

## 📖 Examples

See the `examples/` directory for sample configurations and scripts.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🔗 Links

- **PyPI**: https://pypi.org/project/bq-finops-cli/
- **GitHub**: https://github.com/yourusername/bq-finops-cli
- **Documentation**: https://github.com/yourusername/bq-finops-cli#readme

## 💡 Why BQ FinOps CLI?

- **Save Money**: Identify and fix expensive queries
- **Optimize Performance**: Proper partitioning/clustering
- **Data Governance**: Track usage by team/dataset
- **Proactive Monitoring**: Catch cost spikes early
- **Best Practices**: Built-in BigQuery optimization rules

## 🎓 Related Projects

This module is part of the **Payroll & Workforce Analytics Modernization** project:
- `synthetic-payroll-lab` - Generate test data
- `scd2-bq-engine` - SCD Type 2 automation
- `dataform-warehouse-blueprints` - SQLX template generator

---

**Built with ❤️ for data engineers who care about costs.**
