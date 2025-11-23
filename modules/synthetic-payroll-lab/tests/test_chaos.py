"""Tests for chaos injectors."""

import pytest
import pandas as pd
from datetime import datetime

from synthetic_payroll_lab.chaos import (
    DuplicateInjector,
    NullInjector,
    LateArrivalInjector,
    SchemaDriftInjector,
    FKOrphanInjector
)


class TestDuplicateInjector:
    """Test DuplicateInjector."""
    
    def test_inject_duplicates(self):
        """Test duplicate injection."""
        df = pd.DataFrame({'id': [1, 2, 3, 4, 5], 'value': ['a', 'b', 'c', 'd', 'e']})
        injector = DuplicateInjector(seed=42)
        
        result = injector.inject(df, rate=0.40)  # 40% duplicates
        
        assert len(result) > len(df)  # Should have more rows
        assert len(result) >= len(df) * 1.4  # At least 40% more
    
    def test_no_duplicates_with_zero_rate(self):
        """Test no duplicates with zero rate."""
        df = pd.DataFrame({'id': [1, 2, 3]})
        injector = DuplicateInjector()
        
        result = injector.inject(df, rate=0.0)
        assert len(result) == len(df)


class TestNullInjector:
    """Test NullInjector."""
    
    def test_inject_nulls(self):
        """Test null injection."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'name': ['a', 'b', 'c', 'd', 'e'],
            'value': [10, 20, 30, 40, 50]
        })
        injector = NullInjector(seed=42)
        
        result = injector.inject(df, rate=0.50)  # 50% null rate
        
        # Should have some nulls (not in id column though)
        assert result['name'].isna().sum() > 0 or result['value'].isna().sum() > 0
    
    def test_exclude_key_columns(self):
        """Test that key columns are excluded."""
        df = pd.DataFrame({
            'employee_id': [1, 2, 3],
            'person_id': [10, 20, 30],
            'name': ['a', 'b', 'c']
        })
        injector = NullInjector(seed=42)
        
        result = injector.inject(df, rate=0.50)
        
        # Key columns should not have nulls
        assert result['employee_id'].notna().all()
        assert result['person_id'].notna().all()


class TestLateArrivalInjector:
    """Test LateArrivalInjector."""
    
    def test_inject_late_arrivals(self):
        """Test late arrival marking."""
        df = pd.DataFrame({
            'timecard_id': ['TC001', 'TC002', 'TC003'],
            'work_date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
        })
        injector = LateArrivalInjector(seed=42)
        
        result = injector.inject(df, rate=0.50, date_column='work_date')
        
        assert 'late_arrival_flag' in result.columns
        assert '_simulated_load_date' in result.columns
        assert result['late_arrival_flag'].sum() > 0  # Should have some late arrivals
    
    def test_late_load_dates(self):
        """Test that late load dates are after work dates."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'work_date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03'])
        })
        injector = LateArrivalInjector(seed=42)
        
        result = injector.inject(df, rate=1.0, date_column='work_date')  # All late
        
        for idx, row in result.iterrows():
            if pd.notna(row['_simulated_load_date']) and row['late_arrival_flag']:
                assert row['_simulated_load_date'] > row['work_date']


class TestSchemaDriftInjector:
    """Test SchemaDriftInjector."""
    
    def test_add_column(self):
        """Test adding new column."""
        df = pd.DataFrame({'id': [1, 2, 3], 'name': ['a', 'b', 'c']})
        injector = SchemaDriftInjector(seed=42)
        
        result = injector.inject(df, drift_type='add_column', column_name='new_field')
        
        assert 'new_field' in result.columns
        assert len(result.columns) == len(df.columns) + 1
    
    def test_progressive_drift(self):
        """Test progressive drift over time."""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'date': pd.to_datetime(['2024-01-01', '2024-06-01', '2024-12-01'])
        })
        injector = SchemaDriftInjector(seed=42)
        
        result = injector.inject_progressive(df, date_column='date', drift_interval_days=90)
        
        # Should have added drift columns
        drift_columns = [col for col in result.columns if 'drift_field_' in col]
        assert len(drift_columns) > 0


class TestFKOrphanInjector:
    """Test FKOrphanInjector."""
    
    def test_inject_orphans(self):
        """Test FK orphan injection."""
        df = pd.DataFrame({
            'id': [1, 2, 3, 4, 5],
            'employee_id': ['EMP000001', 'EMP000002', 'EMP000003', 'EMP000004', 'EMP000005']
        })
        injector = FKOrphanInjector(seed=42)
        
        result = injector.inject(df, fk_column='employee_id', rate=0.40)
        
        # Should have some invalid employee IDs
        orphan_count = result['employee_id'].str.contains('9').sum()
        assert orphan_count > 0  # Should have orphaned some


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

