"""Main payroll data generator class."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import random

import pandas as pd
from faker import Faker

from synthetic_payroll_lab.config import PayrollConfig, ChaosConfig
from synthetic_payroll_lab.domains.employees import EmployeeGenerator
from synthetic_payroll_lab.domains.jobs import JobGenerator
from synthetic_payroll_lab.domains.cost_centers import CostCenterGenerator
from synthetic_payroll_lab.domains.schedules import ScheduleGenerator
from synthetic_payroll_lab.domains.timecards import TimecardGenerator
from synthetic_payroll_lab.domains.payroll import PayrollGenerator as PayrollDomainGenerator
from synthetic_payroll_lab.chaos import (
    DuplicateInjector,
    NullInjector,
    LateArrivalInjector,
    SchemaDriftInjector,
    FKOrphanInjector
)


class PayrollGenerator:
    """Generate realistic enterprise payroll test data with chaos patterns.
    
    This generator creates synthetic data for 6 core payroll domains:
    - Employees
    - Jobs
    - Schedules
    - Timecards
    - Payroll Runs
    - Cost Centers
    
    Args:
        employees: Number of employees to generate
        start_date: Start date for time-series data (YYYY-MM-DD)
        end_date: End date for time-series data (YYYY-MM-DD)
        chaos: ChaosConfig for injecting data quality issues
        seed: Random seed for reproducibility
    
    Example:
        >>> gen = PayrollGenerator(employees=1000, start_date="2024-01-01")
        >>> gen.generate_all_domains(output_path="./landing", format="csv")
    """
    
    def __init__(
        self,
        employees: int = 50000,
        start_date: str = "2024-01-01",
        end_date: str = "2024-12-31",
        chaos: Optional[ChaosConfig] = None,
        seed: Optional[int] = None
    ):
        self.employees = employees
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        self.chaos = chaos or ChaosConfig()
        self.seed = seed
        
        # Initialize Faker
        if seed:
            Faker.seed(seed)
            random.seed(seed)
        self.fake = Faker()
        
        # Will store generated data
        self._data_cache: Dict[str, pd.DataFrame] = {}
    
    def generate_all_domains(
        self, 
        output_path: str = "./landing",
        format: str = "csv"
    ) -> Dict[str, pd.DataFrame]:
        """Generate all 6 payroll domains and write to output.
        
        Args:
            output_path: Directory to write output files
            format: Output format (csv, json, parquet)
        
        Returns:
            Dictionary of domain_name -> DataFrame
        """
        print(f"🚀 Starting payroll data generation...")
        print(f"   Employees: {self.employees:,}")
        print(f"   Date Range: {self.start_date.date()} to {self.end_date.date()}")
        print(f"   Chaos Mode: {'Enabled' if self.chaos else 'Disabled'}")
        print()
        
        domains = {}
        
        # Generate each domain (order matters due to dependencies)
        print("📊 Generating domains...")
        domains['jobs'] = self._generate_jobs()
        domains['cost_centers'] = self._generate_cost_centers()
        domains['employees'] = self._generate_employees()
        domains['schedules'] = self._generate_schedules()
        domains['timecards'] = self._generate_timecards()
        domains['payroll_runs'] = self._generate_payroll_runs()
        
        # Cache for future use
        self._data_cache = domains.copy()
        
        # Apply chaos patterns if enabled
        if self.chaos:
            print(f"\n🌪️  Applying chaos patterns...")
            domains = self._apply_chaos(domains)
        
        # Write to output
        print(f"\n💾 Writing to {output_path}/...")
        self._write_domains(domains, output_path, format)
        
        print("\n✅ Generation complete!")
        return domains
    
    def _generate_employees(self) -> pd.DataFrame:
        """Generate employee and assignment data."""
        print("   → Generating employees...")
        
        # Generate jobs and cost centers first (needed for employees)
        jobs_df = self._data_cache.get('jobs')
        if jobs_df is None:
            jobs_df = self._generate_jobs()
            self._data_cache['jobs'] = jobs_df
        
        cost_centers_df = self._data_cache.get('cost_centers')
        if cost_centers_df is None:
            cost_centers_df = self._generate_cost_centers()
            self._data_cache['cost_centers'] = cost_centers_df
        
        emp_gen = EmployeeGenerator(self.fake, self.seed)
        return emp_gen.generate(
            count=self.employees,
            start_date=self.start_date,
            end_date=self.end_date,
            job_codes=jobs_df['job_code'].tolist(),
            cost_centers=cost_centers_df['cost_center_code'].tolist()
        )
    
    def _generate_jobs(self) -> pd.DataFrame:
        """Generate job codes and titles."""
        print("   → Generating jobs...")
        job_gen = JobGenerator()
        return job_gen.generate()
    
    def _generate_cost_centers(self) -> pd.DataFrame:
        """Generate cost centers."""
        print("   → Generating cost centers...")
        cc_gen = CostCenterGenerator()
        return cc_gen.generate(count=50)
    
    def _generate_schedules(self) -> pd.DataFrame:
        """Generate shift schedules."""
        print("   → Generating schedules...")
        
        # Get employee data
        employees_df = self._data_cache.get('employees')
        if employees_df is None:
            employees_df = self._generate_employees()
            self._data_cache['employees'] = employees_df
        
        # Create employee location mapping
        emp_locations = dict(zip(
            employees_df['employee_number'],
            employees_df['location']
        ))
        
        # Get active employee IDs
        active_employees = employees_df[
            employees_df['employment_status'] == 'ACTIVE'
        ]['employee_number'].tolist()
        
        schedule_gen = ScheduleGenerator(self.fake, self.seed)
        return schedule_gen.generate(
            employee_ids=active_employees,
            employee_locations=emp_locations,
            start_date=self.start_date,
            end_date=self.end_date
        )
    
    def _generate_timecards(self) -> pd.DataFrame:
        """Generate timecard punch data."""
        print("   → Generating timecards...")
        
        # Get schedules first
        schedules_df = self._data_cache.get('schedules')
        if schedules_df is None:
            schedules_df = self._generate_schedules()
            self._data_cache['schedules'] = schedules_df
        
        timecard_gen = TimecardGenerator(self.fake, self.seed)
        return timecard_gen.generate(
            schedules_df=schedules_df,
            start_date=self.start_date,
            end_date=self.end_date
        )
    
    def _generate_payroll_runs(self) -> pd.DataFrame:
        """Generate payroll run results."""
        print("   → Generating payroll runs...")
        
        # Get all dependencies
        employees_df = self._data_cache.get('employees')
        if employees_df is None:
            employees_df = self._generate_employees()
            self._data_cache['employees'] = employees_df
        
        timecards_df = self._data_cache.get('timecards')
        if timecards_df is None:
            timecards_df = self._generate_timecards()
            self._data_cache['timecards'] = timecards_df
        
        jobs_df = self._data_cache.get('jobs')
        if jobs_df is None:
            jobs_df = self._generate_jobs()
            self._data_cache['jobs'] = jobs_df
        
        payroll_gen = PayrollDomainGenerator(self.fake, self.seed)
        return payroll_gen.generate(
            employees_df=employees_df,
            timecards_df=timecards_df,
            jobs_df=jobs_df,
            start_date=self.start_date,
            end_date=self.end_date,
            frequency="biweekly"
        )
    
    def _apply_chaos(self, domains: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
        """Apply chaos patterns to generated domains.
        
        Args:
            domains: Dictionary of domain DataFrames
        
        Returns:
            Dictionary of domains with chaos applied
        """
        result = {}
        
        # Initialize injectors
        dup_injector = DuplicateInjector(self.seed)
        null_injector = NullInjector(self.seed)
        late_injector = LateArrivalInjector(self.seed)
        drift_injector = SchemaDriftInjector(self.seed)
        fk_injector = FKOrphanInjector(self.seed)
        
        for domain_name, df in domains.items():
            working_df = df.copy()
            
            # 1. Inject duplicates
            if self.chaos.duplicate_rate > 0:
                working_df = dup_injector.inject(working_df, self.chaos.duplicate_rate)
                print(f"   → Duplicates injected into {domain_name}: {self.chaos.duplicate_rate*100:.1f}%")
            
            # 2. Inject nulls (not on key columns)
            if self.chaos.null_spike_rate > 0:
                working_df = null_injector.inject(working_df, self.chaos.null_spike_rate)
                print(f"   → Null spikes injected into {domain_name}: {self.chaos.null_spike_rate*100:.1f}%")
            
            # 3. Late arrivals (timecards only)
            if domain_name == 'timecards' and self.chaos.late_arrival_pct > 0:
                working_df = late_injector.inject(
                    working_df, 
                    self.chaos.late_arrival_pct,
                    date_column='work_date'
                )
                print(f"   → Late arrivals marked in timecards: {self.chaos.late_arrival_pct*100:.1f}%")
            
            # 4. Schema drift (progressive)
            if self.chaos.schema_drift_days > 0 and domain_name in ['timecards', 'employees']:
                date_col = 'work_date' if domain_name == 'timecards' else 'hire_date'
                if date_col in working_df.columns:
                    working_df = drift_injector.inject_progressive(
                        working_df,
                        date_column=date_col,
                        drift_interval_days=self.chaos.schema_drift_days
                    )
                    print(f"   → Schema drift applied to {domain_name} every {self.chaos.schema_drift_days} days")
            
            # 5. FK orphans
            if self.chaos.fk_orphan_rate > 0:
                if domain_name == 'timecards':
                    working_df = fk_injector.inject(working_df, 'employee_id', self.chaos.fk_orphan_rate)
                    print(f"   → FK orphans created in {domain_name}: {self.chaos.fk_orphan_rate*100:.1f}%")
                elif domain_name == 'employees':
                    working_df = fk_injector.inject_multiple(
                        working_df,
                        ['cost_center', 'job_code', 'manager_id'],
                        self.chaos.fk_orphan_rate
                    )
                    print(f"   → FK orphans created in {domain_name}: {self.chaos.fk_orphan_rate*100:.1f}%")
            
            result[domain_name] = working_df
        
        return result
    
    def _write_domains(
        self, 
        domains: Dict[str, pd.DataFrame], 
        output_path: str,
        format: str
    ) -> None:
        """Write domains to output files."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for domain_name, df in domains.items():
            # Create domain directory
            domain_dir = output_dir / f"domain={domain_name}"
            domain_dir.mkdir(exist_ok=True)
            
            # Write file
            if format == 'csv':
                filepath = domain_dir / f"{domain_name}.csv"
                df.to_csv(filepath, index=False)
            elif format == 'json':
                filepath = domain_dir / f"{domain_name}.json"
                df.to_json(filepath, orient='records', lines=True)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            print(f"      ✓ {domain_name}: {len(df):,} rows → {filepath}")


# Convenience function
def generate(
    employees: int = 50000,
    output_path: str = "./landing",
    **kwargs
) -> Dict[str, pd.DataFrame]:
    """Convenience function for quick generation.
    
    Example:
        >>> from synthetic_payroll_lab import generate
        >>> data = generate(employees=1000, output_path="./test_data")
    """
    gen = PayrollGenerator(employees=employees, **kwargs)
    return gen.generate_all_domains(output_path=output_path)

