# Domain Generators

This directory contains data generators for each payroll domain:

- `employees.py` - Employee and assignment data
- `jobs.py` - Job codes, titles, and grades
- `schedules.py` - Shift schedules
- `timecards.py` - Timecard and punch data
- `payroll.py` - Payroll run results
- `cost_centers.py` - Cost center and GL mappings

Each domain generator follows the same interface:
```python
class DomainGenerator:
    def generate(self, config: DomainConfig) -> pd.DataFrame:
        """Generate domain data as DataFrame."""
        pass
```

