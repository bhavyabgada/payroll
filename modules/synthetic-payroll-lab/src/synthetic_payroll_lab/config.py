"""Configuration classes for synthetic payroll data generation."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChaosConfig(BaseModel):
    """Configuration for chaos patterns to inject into generated data.
    
    Args:
        duplicate_rate: Percentage of duplicate rows to inject (0.0-1.0)
        null_spike_rate: Percentage of null values to inject randomly (0.0-1.0)
        late_arrival_pct: Percentage of timecards that arrive late (0.0-1.0)
        schema_drift_days: Add new column every N days
        timezone_error_rate: Percentage of timezone errors (0.0-1.0)
        fk_orphan_rate: Percentage of orphaned foreign key records (0.0-1.0)
    """
    
    duplicate_rate: float = Field(default=0.02, ge=0.0, le=1.0)
    null_spike_rate: float = Field(default=0.01, ge=0.0, le=1.0)
    late_arrival_pct: float = Field(default=0.15, ge=0.0, le=1.0)
    schema_drift_days: int = Field(default=90, gt=0)
    timezone_error_rate: float = Field(default=0.03, ge=0.0, le=1.0)
    fk_orphan_rate: float = Field(default=0.01, ge=0.0, le=1.0)


class EmployeeConfig(BaseModel):
    """Configuration for employee generation."""
    
    count: int = Field(default=50000, gt=0)
    age_min: int = Field(default=18, ge=16)
    age_max: int = Field(default=70, le=100)
    full_time_pct: float = Field(default=0.75, ge=0.0, le=1.0)
    union_pct: float = Field(default=0.30, ge=0.0, le=1.0)
    turnover_annual_rate: float = Field(default=0.15, ge=0.0, le=1.0)


class PayrollConfig(BaseModel):
    """Main configuration for payroll data generation."""
    
    employees: EmployeeConfig = Field(default_factory=EmployeeConfig)
    start_date: str = Field(default="2024-01-01")
    end_date: str = Field(default="2024-12-31")
    output_format: str = Field(default="csv", pattern="^(csv|json|parquet)$")
    chaos: Optional[ChaosConfig] = Field(default_factory=ChaosConfig)
    seed: Optional[int] = None  # For reproducibility

