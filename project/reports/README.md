# Generated Reports

This directory contains generated reports, dashboards, and analysis artifacts.

## Structure

```
reports/
├── optimization_report.md         # Before/after FinOps metrics
├── data_quality_dashboard.png     # GE validation results
├── lineage_diagram.png            # Data lineage visualization
├── cost_reports/
│   ├── 2025-01/
│   │   ├── cost_by_team.csv
│   │   ├── cost_by_dataset.csv
│   │   └── antipatterns.txt
│   └── 2025-02/
├── dq_reports/
│   ├── staging_checkpoint_2025-01-23.html
│   └── warehouse_checkpoint_2025-01-23.html
└── performance/
    ├── query_performance.csv
    └── pipeline_duration_trends.png
```

## Report Types

### 1. FinOps Reports (Module D)
- Cost by team/user/dataset
- Anti-pattern detection results
- Before/after optimization tracking
- Monthly cost summaries

### 2. Data Quality Reports (Great Expectations)
- Checkpoint validation results (HTML)
- DQ metrics over time
- Failed expectation details

### 3. Performance Reports
- Pipeline duration trends
- Query performance metrics
- SLA compliance tracking

### 4. Lineage & Documentation
- Data lineage diagrams
- Schema documentation
- Impact analysis

## Automated Generation

Reports are generated automatically by:
- **Daily**: FinOps cost reports (GitHub Actions cron)
- **Per run**: Great Expectations validation reports (Airflow)
- **Weekly**: Performance trend reports
- **On deployment**: Lineage diagrams

## Archival

- Reports retained for 90 days
- Monthly summaries retained indefinitely
- Published to internal wiki/dashboard

## Usage

```bash
# Generate FinOps report manually
bq-finops report \
    --project payroll-analytics-prod \
    --start-date 2025-01-01 \
    --output reports/cost_reports/$(date +%Y-%m)/cost_by_team.csv

# View GE report
open reports/dq_reports/staging_checkpoint_$(date +%Y-%m-%d).html
```

## Git Ignore

Most reports are gitignored (generated artifacts), except:
- `optimization_report.md` (portfolio showcase)
- Key diagrams for documentation

