"""Timecard and punch data generator."""

import random
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from faker import Faker


class TimecardGenerator:
    """Generate timecard punch records."""
    
    def __init__(self, fake: Faker, seed: int = None):
        self.fake = fake
        if seed:
            random.seed(seed)
    
    def generate(
        self,
        schedules_df: pd.DataFrame,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Generate timecard records based on schedules.
        
        Args:
            schedules_df: DataFrame with schedule data
            start_date: Start date for timecards
            end_date: End date for timecards
        
        Returns:
            DataFrame with timecard data
        """
        timecards = []
        timecard_id = 0
        
        for _, schedule in schedules_df.iterrows():
            # Skip PTO schedules (no punches)
            if schedule['schedule_type'] == 'PTO':
                continue
            
            emp_id = schedule['employee_id']
            work_date = schedule['shift_date']
            scheduled_start = schedule['shift_start']
            scheduled_end = schedule['shift_end']
            
            # Simulate punch variations
            # 10% late, 5% early, 85% on time
            punch_variation = random.choices(
                ['late', 'early', 'ontime'],
                weights=[0.10, 0.05, 0.85]
            )[0]
            
            if punch_variation == 'late':
                punch_in = scheduled_start + timedelta(minutes=random.randint(1, 30))
            elif punch_variation == 'early':
                punch_in = scheduled_start - timedelta(minutes=random.randint(1, 15))
            else:
                punch_in = scheduled_start
            
            # End time variations
            end_variation = random.choices(
                ['early', 'late', 'ontime'],
                weights=[0.05, 0.15, 0.80]  # 15% work overtime
            )[0]
            
            if end_variation == 'early':
                punch_out = scheduled_end - timedelta(minutes=random.randint(1, 30))
            elif end_variation == 'late':
                punch_out = scheduled_end + timedelta(minutes=random.randint(1, 180))  # Up to 3 hrs OT
            else:
                punch_out = scheduled_end
            
            # Calculate hours
            hours_worked = (punch_out - punch_in).total_seconds() / 3600
            hours_scheduled = schedule['hours_scheduled']
            
            # Overtime calculation (over 8 hours/day or 40 hours/week)
            if hours_worked > 8:
                hours_overtime = hours_worked - 8
                hours_regular = 8.0
            else:
                hours_overtime = 0.0
                hours_regular = hours_worked
            
            # PTO hours (if applicable)
            hours_pto = 0.0
            if schedule['schedule_type'] == 'PTO':
                hours_pto = 8.0
                hours_regular = 0.0
            
            # Approval status
            approval_status = random.choices(
                ['PENDING', 'APPROVED', 'REJECTED'],
                weights=[0.05, 0.93, 0.02]
            )[0]
            
            # Adjustment flag (for late-arriving corrections)
            adjustment_flag = False
            if random.random() < 0.05:  # 5% are adjustments
                adjustment_flag = True
            
            timecards.append({
                "timecard_id": f"TC{timecard_id:08d}",
                "employee_id": emp_id,
                "work_date": work_date,
                "punch_in": punch_in,
                "punch_out": punch_out,
                "hours_worked": round(hours_worked, 2),
                "hours_regular": round(hours_regular, 2),
                "hours_overtime": round(hours_overtime, 2),
                "hours_pto": round(hours_pto, 2),
                "approval_status": approval_status,
                "adjustment_flag": adjustment_flag,
                "shift_type": schedule['shift_type']
            })
            
            timecard_id += 1
        
        return pd.DataFrame(timecards)

