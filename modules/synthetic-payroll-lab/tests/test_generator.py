"""Tests for PayrollGenerator."""

import pytest
from datetime import datetime
import pandas as pd

from synthetic_payroll_lab import PayrollGenerator, ChaosConfig


class TestPayrollGenerator:
    """Test PayrollGenerator class."""
    
    def test_init_basic(self):
        """Test basic initialization."""
        gen = PayrollGenerator(employees=100)
        assert gen.employees == 100
        assert gen.start_date.year == 2024
        assert gen.end_date.year == 2024
    
    def test_init_with_dates(self):
        """Test initialization with custom dates."""
        gen = PayrollGenerator(
            employees=50,
            start_date="2023-01-01",
            end_date="2023-12-31"
        )
        assert gen.start_date.year == 2023
        assert gen.end_date.year == 2023
    
    def test_init_with_chaos(self):
        """Test initialization with chaos config."""
        chaos = ChaosConfig(duplicate_rate=0.05)
        gen = PayrollGenerator(employees=10, chaos=chaos)
        assert gen.chaos.duplicate_rate == 0.05
    
    def test_generate_all_domains(self, tmp_path):
        """Test generating all domains."""
        gen = PayrollGenerator(
            employees=5,
            start_date="2024-01-01",
            end_date="2024-01-07",
            seed=42
        )
        
        domains = gen.generate_all_domains(
            output_path=str(tmp_path),
            format="csv"
        )
        
        # Check all domains present
        assert "employees" in domains
        assert "jobs" in domains
        assert "cost_centers" in domains
        assert "schedules" in domains
        assert "timecards" in domains
        assert "payroll_runs" in domains
        
        # Check data types
        for domain_name, df in domains.items():
            assert isinstance(df, pd.DataFrame)
            assert len(df) > 0
    
    def test_deterministic_generation(self):
        """Test that seed produces deterministic results."""
        gen1 = PayrollGenerator(employees=10, seed=42)
        gen2 = PayrollGenerator(employees=10, seed=42)
        
        domains1 = gen1.generate_all_domains(output_path="./temp1", format="csv")
        domains2 = gen2.generate_all_domains(output_path="./temp2", format="csv")
        
        # Should have same number of rows
        assert len(domains1['employees']) == len(domains2['employees'])
        
    def test_employees_generation(self):
        """Test employee data has required columns."""
        gen = PayrollGenerator(employees=10, seed=42)
        employees_df = gen._generate_employees()
        
        required_columns = [
            'employee_number', 'first_name', 'last_name',
            'hire_date', 'employment_status', 'job_code', 'cost_center'
        ]
        
        for col in required_columns:
            assert col in employees_df.columns
        
        assert len(employees_df) == 10
    
    def test_jobs_generation(self):
        """Test job data generation."""
        gen = PayrollGenerator(employees=10)
        jobs_df = gen._generate_jobs()
        
        assert 'job_code' in jobs_df.columns
        assert 'job_title' in jobs_df.columns
        assert len(jobs_df) > 0
    
    def test_cost_centers_generation(self):
        """Test cost center generation."""
        gen = PayrollGenerator(employees=10)
        cc_df = gen._generate_cost_centers()
        
        assert 'cost_center_code' in cc_df.columns
        assert len(cc_df) > 0


class TestChaosConfig:
    """Test ChaosConfig class."""
    
    def test_default_config(self):
        """Test default chaos configuration."""
        chaos = ChaosConfig()
        assert chaos.duplicate_rate == 0.02
        assert chaos.null_spike_rate == 0.01
        assert chaos.late_arrival_pct == 0.15
    
    def test_custom_config(self):
        """Test custom chaos configuration."""
        chaos = ChaosConfig(
            duplicate_rate=0.05,
            null_spike_rate=0.03,
            late_arrival_pct=0.20
        )
        assert chaos.duplicate_rate == 0.05
        assert chaos.null_spike_rate == 0.03
        assert chaos.late_arrival_pct == 0.20
    
    def test_validation(self):
        """Test config validation."""
        # Should raise error for invalid rate
        with pytest.raises(Exception):
            ChaosConfig(duplicate_rate=1.5)  # Over 1.0
        
        with pytest.raises(Exception):
            ChaosConfig(duplicate_rate=-0.1)  # Negative


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

