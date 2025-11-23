"""Job codes and titles generator."""

import pandas as pd


class JobGenerator:
    """Generate job codes, titles, and grades."""
    
    def generate(self) -> pd.DataFrame:
        """Generate standard job codes and titles.
        
        Returns:
            DataFrame with job definitions
        """
        jobs = [
            # Executive
            {"job_code": "C_LEVEL", "job_title": "C-Level Executive", "job_family": "Executive", 
             "job_level": 10, "pay_grade": "E1", "union_eligible": "N", 
             "min_salary": 250000, "max_salary": 500000},
            {"job_code": "VP", "job_title": "Vice President", "job_family": "Executive",
             "job_level": 9, "pay_grade": "E2", "union_eligible": "N",
             "min_salary": 180000, "max_salary": 300000},
            
            # Management
            {"job_code": "DIR", "job_title": "Director", "job_family": "Management",
             "job_level": 8, "pay_grade": "M1", "union_eligible": "N",
             "min_salary": 130000, "max_salary": 200000},
            {"job_code": "MGR", "job_title": "Manager", "job_family": "Management",
             "job_level": 7, "pay_grade": "M2", "union_eligible": "N",
             "min_salary": 90000, "max_salary": 140000},
            {"job_code": "SUPV", "job_title": "Supervisor", "job_family": "Management",
             "job_level": 6, "pay_grade": "M3", "union_eligible": "Y",
             "min_salary": 65000, "max_salary": 95000},
            
            # Engineering
            {"job_code": "ENG_SR", "job_title": "Senior Engineer", "job_family": "Engineering",
             "job_level": 6, "pay_grade": "P3", "union_eligible": "N",
             "min_salary": 120000, "max_salary": 180000},
            {"job_code": "ENG", "job_title": "Engineer", "job_family": "Engineering",
             "job_level": 5, "pay_grade": "P4", "union_eligible": "N",
             "min_salary": 80000, "max_salary": 120000},
            {"job_code": "ENG_JR", "job_title": "Junior Engineer", "job_family": "Engineering",
             "job_level": 4, "pay_grade": "P5", "union_eligible": "N",
             "min_salary": 60000, "max_salary": 85000},
            
            # Sales
            {"job_code": "SALES_SR", "job_title": "Senior Sales Representative", "job_family": "Sales",
             "job_level": 5, "pay_grade": "S2", "union_eligible": "N",
             "min_salary": 70000, "max_salary": 120000},
            {"job_code": "SALES", "job_title": "Sales Representative", "job_family": "Sales",
             "job_level": 4, "pay_grade": "S3", "union_eligible": "N",
             "min_salary": 50000, "max_salary": 80000},
            
            # Operations
            {"job_code": "OPS_LEAD", "job_title": "Operations Lead", "job_family": "Operations",
             "job_level": 5, "pay_grade": "O2", "union_eligible": "Y",
             "min_salary": 55000, "max_salary": 75000},
            {"job_code": "OPS_SPEC", "job_title": "Operations Specialist", "job_family": "Operations",
             "job_level": 4, "pay_grade": "O3", "union_eligible": "Y",
             "min_salary": 45000, "max_salary": 60000},
            {"job_code": "OPS", "job_title": "Operations Associate", "job_family": "Operations",
             "job_level": 3, "pay_grade": "O4", "union_eligible": "Y",
             "min_salary": 35000, "max_salary": 50000},
            
            # Support
            {"job_code": "ADMIN_SR", "job_title": "Senior Administrator", "job_family": "Administrative",
             "job_level": 4, "pay_grade": "A2", "union_eligible": "Y",
             "min_salary": 50000, "max_salary": 70000},
            {"job_code": "ADMIN", "job_title": "Administrator", "job_family": "Administrative",
             "job_level": 3, "pay_grade": "A3", "union_eligible": "Y",
             "min_salary": 40000, "max_salary": 55000},
            
            # Customer Service
            {"job_code": "CS_SR", "job_title": "Senior Customer Service Rep", "job_family": "Customer Service",
             "job_level": 4, "pay_grade": "C2", "union_eligible": "Y",
             "min_salary": 45000, "max_salary": 60000},
            {"job_code": "CS", "job_title": "Customer Service Representative", "job_family": "Customer Service",
             "job_level": 3, "pay_grade": "C3", "union_eligible": "Y",
             "min_salary": 35000, "max_salary": 48000},
        ]
        
        return pd.DataFrame(jobs)

