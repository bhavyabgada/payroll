"""Shift schedule generator."""

import random
from datetime import datetime, timedelta
from typing import List

import pandas as pd
from faker import Faker


class ScheduleGenerator:
    """Generate shift schedules for employees."""
    
    def __init__(self, fake: Faker, seed: int = None):
        self.fake = fake
        if seed:
            random.seed(seed)
        
        # Define shift types
        self.shift_types = {
            "DAY": (9, 17),      # 9 AM - 5 PM
            "EVENING": (14, 22),  # 2 PM - 10 PM
            "NIGHT": (22, 6),     # 10 PM - 6 AM
            "SWING": (13, 21),    # 1 PM - 9 PM
        }
        
        # Timezones for locations
        self.timezones = {
            "New York, NY": "America/New_York",
            "San Francisco, CA": "America/Los_Angeles",
            "Chicago, IL": "America/Chicago",
            "Austin, TX": "America/Chicago",
            "Boston, MA": "America/New_York",
            "Seattle, WA": "America/Los_Angeles",
            "Denver, CO": "America/Denver",
            "Atlanta, GA": "America/New_York",
            "Los Angeles, CA": "America/Los_Angeles",
            "Portland, OR": "America/Los_Angeles"
        }
    
    def generate(
        self,
        employee_ids: List[str],
        employee_locations: dict,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """Generate shift schedules for employees.
        
        Args:
            employee_ids: List of employee IDs to schedule
            employee_locations: Dict mapping employee_id to location
            start_date: Start date for schedules
            end_date: End date for schedules
        
        Returns:
            DataFrame with schedule data
        """
        schedules = []
        schedule_id = 0
        
        # Generate schedules for each day
        current_date = start_date
        while current_date <= end_date:
            # Skip some weekends (not all employees work weekends)
            is_weekend = current_date.weekday() >= 5
            
            for emp_id in employee_ids:
                # Not everyone works every day
                if is_weekend and random.random() < 0.7:  # 70% don't work weekends
                    continue
                if not is_weekend and random.random() < 0.05:  # 5% absence rate
                    continue
                
                location = employee_locations.get(emp_id, "New York, NY")
                timezone = self.timezones.get(location, "America/New_York")
                
                # Select shift type (most people work day shift)
                shift_type = random.choices(
                    list(self.shift_types.keys()),
                    weights=[0.70, 0.15, 0.10, 0.05]
                )[0]
                
                start_hour, end_hour = self.shift_types[shift_type]
                
                # Handle overnight shifts
                if end_hour < start_hour:
                    end_date_adj = current_date + timedelta(days=1)
                else:
                    end_date_adj = current_date
                
                shift_start = datetime.combine(current_date.date(), datetime.min.time()) + \
                              timedelta(hours=start_hour)
                shift_end = datetime.combine(end_date_adj.date(), datetime.min.time()) + \
                            timedelta(hours=end_hour)
                
                schedule_type = random.choices(
                    ["REGULAR", "ONCALL", "OVERTIME", "PTO", "TRAINING"],
                    weights=[0.75, 0.10, 0.08, 0.05, 0.02]
                )[0]
                
                schedules.append({
                    "schedule_id": f"SCH{schedule_id:08d}",
                    "employee_id": emp_id,
                    "shift_date": current_date.date(),
                    "shift_start": shift_start,
                    "shift_end": shift_end,
                    "shift_type": shift_type,
                    "timezone": timezone,
                    "location": location,
                    "schedule_type": schedule_type,
                    "hours_scheduled": 8.0 if schedule_type != "PTO" else 0.0
                })
                
                schedule_id += 1
            
            current_date += timedelta(days=1)
        
        return pd.DataFrame(schedules)

