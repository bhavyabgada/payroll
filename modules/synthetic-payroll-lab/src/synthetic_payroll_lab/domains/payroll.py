"""Payroll run results generator."""

import random
from datetime import datetime, timedelta

import pandas as pd
from faker import Faker


class PayrollGenerator:
    """Generate payroll run results."""
    
    def __init__(self, fake: Faker, seed: int = None):
        self.fake = fake
        if seed:
            random.seed(seed)
    
    def generate(
        self,
        employees_df: pd.DataFrame,
        timecards_df: pd.DataFrame,
        jobs_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime,
        frequency: str = "biweekly"
    ) -> pd.DataFrame:
        """Generate payroll run results.
        
        Args:
            employees_df: Employee data
            timecards_df: Timecard data
            jobs_df: Job data with salary ranges
            start_date: Start date for payroll periods
            end_date: End date for payroll periods
            frequency: Payroll frequency (weekly, biweekly, semimonthly, monthly)
        
        Returns:
            DataFrame with payroll run data
        """
        # Create job lookup for salary info
        job_lookup = jobs_df.set_index('job_code')[['min_salary', 'max_salary']].to_dict('index')
        
        payroll_runs = []
        run_id = 1001
        
        # Generate pay periods based on frequency
        pay_periods = self._generate_pay_periods(start_date, end_date, frequency)
        
        for period_start, period_end in pay_periods:
            # Get timecards for this period
            period_timecards = timecards_df[
                (timecards_df['work_date'] >= period_start.date()) &
                (timecards_df['work_date'] <= period_end.date())
            ].copy()
            
            # Process each employee
            for _, employee in employees_df.iterrows():
                emp_id = employee['employee_number']
                job_code = employee['job_code']
                
                # Skip if terminated before period
                termination_date = employee['termination_date']
                if pd.notna(termination_date):
                    if isinstance(termination_date, str):
                        termination_date = pd.to_datetime(termination_date).date()
                    if termination_date < period_start.date():
                        continue
                
                # Get employee's timecards for period
                emp_timecards = period_timecards[period_timecards['employee_id'] == emp_id]
                
                # Calculate hours
                hours_regular = emp_timecards['hours_regular'].sum()
                hours_overtime = emp_timecards['hours_overtime'].sum()
                hours_pto = emp_timecards['hours_pto'].sum()
                total_hours = hours_regular + hours_overtime + hours_pto
                
                # Calculate pay based on job
                job_info = job_lookup.get(job_code, {'min_salary': 50000, 'max_salary': 80000})
                annual_salary = random.uniform(job_info['min_salary'], job_info['max_salary'])
                
                # Calculate hourly rate (assuming 2080 hours/year)
                hourly_rate = annual_salary / 2080
                overtime_rate = hourly_rate * 1.5
                
                # Gross pay
                gross_pay_regular = hours_regular * hourly_rate
                gross_pay_overtime = hours_overtime * overtime_rate
                gross_pay_pto = hours_pto * hourly_rate
                gross_pay = gross_pay_regular + gross_pay_overtime + gross_pay_pto
                
                # Taxes (simplified)
                tax_federal = gross_pay * 0.12  # Simplified federal tax
                tax_state = gross_pay * 0.05    # Simplified state tax
                tax_fica = gross_pay * 0.0765   # FICA (Social Security + Medicare)
                total_taxes = tax_federal + tax_state + tax_fica
                
                # Deductions
                deduction_401k = gross_pay * random.choice([0.03, 0.05, 0.06, 0.00])
                deduction_health = random.choice([0, 150, 300, 450])  # Monthly premium
                deduction_dental = random.choice([0, 25, 50])
                total_deductions = deduction_401k + deduction_health + deduction_dental
                
                # Net pay
                net_pay = gross_pay - total_taxes - total_deductions
                
                # Run type
                run_type = random.choices(
                    ['REGULAR', 'BONUS', 'ADJUSTMENT', 'CORRECTION'],
                    weights=[0.90, 0.05, 0.03, 0.02]
                )[0]
                
                payroll_runs.append({
                    "run_id": run_id,
                    "run_date": period_end.date(),
                    "period_start": period_start.date(),
                    "period_end": period_end.date(),
                    "run_type": run_type,
                    "employee_id": emp_id,
                    "gross_pay": round(gross_pay, 2),
                    "net_pay": round(net_pay, 2),
                    "tax_federal": round(tax_federal, 2),
                    "tax_state": round(tax_state, 2),
                    "tax_fica": round(tax_fica, 2),
                    "deduction_401k": round(deduction_401k, 2),
                    "deduction_health": round(deduction_health, 2),
                    "deduction_dental": round(deduction_dental, 2),
                    "hours_base": round(hours_regular, 2),
                    "hours_overtime": round(hours_overtime, 2),
                    "hours_pto": round(hours_pto, 2),
                    "hourly_rate": round(hourly_rate, 2),
                    "annual_salary": round(annual_salary, 2)
                })
            
            run_id += 1
        
        return pd.DataFrame(payroll_runs)
    
    def _generate_pay_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        frequency: str
    ) -> list:
        """Generate list of pay periods.
        
        Args:
            start_date: Start date
            end_date: End date
            frequency: Payroll frequency
        
        Returns:
            List of (period_start, period_end) tuples
        """
        periods = []
        current = start_date
        
        if frequency == "weekly":
            delta = timedelta(days=7)
        elif frequency == "biweekly":
            delta = timedelta(days=14)
        elif frequency == "semimonthly":
            delta = timedelta(days=15)  # Simplified
        elif frequency == "monthly":
            delta = timedelta(days=30)  # Simplified
        else:
            delta = timedelta(days=14)  # Default to biweekly
        
        while current < end_date:
            period_end = min(current + delta, end_date)
            periods.append((current, period_end))
            current = period_end + timedelta(days=1)
        
        return periods

