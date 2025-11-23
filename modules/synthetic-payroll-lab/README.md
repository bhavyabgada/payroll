# Synthetic Payroll Lab

**Version**: 0.1.0  
**License**: MIT  
**Status**: MVP Development

## Overview

Generate realistic, enterprise-messy payroll and timekeeping test data with configurable "chaos" knobs to stress-test data pipelines.

## Why This Module?

Existing synthetic data tools (Faker, Mockaroo) don't understand payroll domain semantics or simulate common enterprise chaos patterns like:
- Late arriving facts
- Schema drift
- Foreign key orphans
- Timezone errors
- Duplicate records

## Features (v0.1.0 MVP)

- ✅ Generate 6 core payroll domains (employees, jobs, schedules, timecards, payroll runs, cost centers)
- ✅ CSV/JSON output with Hive-style partitioning
- ✅ Configurable chaos patterns (duplicates, nulls, late arrivals, schema drift)
- ✅ Deterministic mode (seed for reproducibility)
- ✅ CLI + Python API

## Quick Start

```bash
# Install
pip install synthetic-payroll-lab

# Generate test data
synthetic-payroll generate \
    --config payroll_config.yaml \
    --output-dir ./landing \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --employees 50000
```

## Python API

```python
from synthetic_payroll_lab import PayrollGenerator, ChaosConfig

gen = PayrollGenerator(
    employees=50000,
    start_date="2024-01-01",
    chaos=ChaosConfig(
        duplicate_rate=0.02,      # 2% duplicate rows
        null_spike_rate=0.01,     # 1% random null injection
        late_arrival_pct=0.15,    # 15% timecards arrive T+2 days
        schema_drift_days=90,     # Column added every 90 days
        timezone_error_rate=0.03  # 3% wrong timezone
    )
)

gen.generate_all_domains(output_path="./landing", format="csv")
```

## Configuration

See [config_reference.md](docs/config_reference.md) for full YAML schema.

## Roadmap

- **v0.1.0** (MVP): Core domains + basic chaos
- **v0.2.0**: SCD2 dimension changes, retro adjustments
- **v1.0.0**: Multi-region support, PII variants, Parquet output

## Contributing

Issues and PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT - see [LICENSE](LICENSE)

