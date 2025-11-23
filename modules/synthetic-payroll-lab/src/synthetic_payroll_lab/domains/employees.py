"""Employee and assignment data generator."""

import random
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from faker import Faker


class EmployeeGenerator:
    """Generate employee and assignment data with realistic demographics."""
    
    def __init__(self, fake: Faker, seed: int = None):
        self.fake = fake
        if seed:
            random.seed(seed)
    
    def generate(
        self,
        count: int,
        start_date: datetime,
        end_date: datetime,
        job_codes: List[str],
        cost_centers: List[str]
    ) -> pd.DataFrame:
        """Generate employee and assignment data.
        
        Args:
            count: Number of employees to generate
            start_date: Start date for employment periods
            end_date: End date for employment periods
            job_codes: List of valid job codes
            cost_centers: List of valid cost center codes
        
        Returns:
            DataFrame with employee and assignment data
        """
        employees = []
        
        for i in range(count):
            emp_id = f"EMP{i:06d}"
            
            # Demographics
            first_name = self.fake.first_name()
            last_name = self.fake.last_name()
            date_of_birth = self.fake.date_of_birth(minimum_age=18, maximum_age=70)
            
            # PII fields
            ssn = self.fake.ssn()
            email = f"{first_name.lower()}.{last_name.lower()}@company.com"
            phone = self.fake.phone_number()
            address = self.fake.street_address()
            city = self.fake.city()
            state = self.fake.state_abbr()
            zip_code = self.fake.zipcode()
            
            # Employment dates
            hire_date = self.fake.date_between(
                start_date=start_date - timedelta(days=1825),  # Up to 5 years before
                end_date=end_date
            )
            
            # Random terminations (15% turnover rate)
            is_terminated = random.random() < 0.15
            termination_date = None
            employment_status = "ACTIVE"
            
            # Ensure end_date is a date object for comparison
            end_date_obj = end_date.date() if hasattr(end_date, 'date') else end_date
            
            if is_terminated and hire_date < end_date_obj - timedelta(days=90):
                termination_date = self.fake.date_between(
                    start_date=hire_date + timedelta(days=90),
                    end_date=end_date_obj
                )
                employment_status = "TERMINATED"
            
            # Assignment attributes
            job_code = random.choice(job_codes)
            department = random.choice([
                "Engineering", "Sales", "Operations", "Marketing",
                "Finance", "HR", "Customer Service", "IT"
            ])
            location = random.choice([
                "New York, NY", "San Francisco, CA", "Chicago, IL",
                "Austin, TX", "Boston, MA", "Seattle, WA", "Denver, CO"
            ])
            cost_center = random.choice(cost_centers)
            
            # Employment category
            employment_category = random.choices(
                ["FULL_TIME", "PART_TIME", "CONTRACTOR"],
                weights=[0.75, 0.15, 0.10]
            )[0]
            
            # Union membership
            union_flag = "Y" if random.random() < 0.30 else "N"
            
            # Manager (20% are managers, others report to managers)
            manager_id = None
            if i > 0 and random.random() < 0.80:
                # Report to earlier employee (simplified hierarchy)
                manager_id = f"EMP{random.randint(0, max(0, i-1)):06d}"
            
            employees.append({
                # Person attributes
                "person_id": i + 1,
                "employee_number": emp_id,
                "first_name": first_name,
                "last_name": last_name,
                "date_of_birth": date_of_birth,
                "national_identifier": ssn,  # PII
                "email_address": email,
                "phone_number": phone,
                "address": address,
                "city": city,
                "state": state,
                "zip_code": zip_code,
                
                # Employment
                "hire_date": hire_date,
                "termination_date": termination_date,
                "employment_status": employment_status,
                "effective_start_date": hire_date,
                "effective_end_date": termination_date or datetime(9999, 12, 31).date(),
                
                # Assignment
                "assignment_id": i + 1,
                "job_code": job_code,
                "department": department,
                "location": location,
                "manager_id": manager_id,
                "cost_center": cost_center,
                "employment_category": employment_category,
                "union_flag": union_flag
            })
        
        return pd.DataFrame(employees)

