# Chaos Injectors

This directory contains chaos pattern injectors that simulate real-world data quality issues:

- `duplicates.py` - Inject duplicate rows
- `nulls.py` - Random null spike injection
- `late_arrivals.py` - Simulate late-arriving facts
- `schema_drift.py` - Add/remove/rename columns over time
- `fk_orphans.py` - Create orphaned foreign key references

Each injector implements:
```python
class ChaosInjector:
    def inject(self, df: pd.DataFrame, rate: float) -> pd.DataFrame:
        """Apply chaos pattern to DataFrame."""
        pass
```

