"""Late arrival fact injector."""

import random
from datetime import timedelta
import pandas as pd


class LateArrivalInjector:
    """Mark records as late-arriving to simulate delayed data."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
    
    def inject(
        self, 
        df: pd.DataFrame, 
        rate: float = 0.15,
        date_column: str = 'work_date',
        max_lag_days: int = 3
    ) -> pd.DataFrame:
        """Mark records as late-arriving.
        
        Args:
            df: Input DataFrame
            rate: Percentage of records that arrive late (0.0-1.0)
            date_column: Name of the date column
            max_lag_days: Maximum days late (1-7)
        
        Returns:
            DataFrame with late_arrival_flag and simulated load dates
        """
        if rate <= 0 or df.empty or date_column not in df.columns:
            return df
        
        result = df.copy()
        
        # Add late arrival tracking columns
        result['late_arrival_flag'] = False
        result['_simulated_load_date'] = pd.NaT
        
        # Select random records to mark as late
        num_late = int(len(result) * rate)
        if num_late > 0:
            late_indices = random.sample(range(len(result)), num_late)
            
            for idx in late_indices:
                result.loc[idx, 'late_arrival_flag'] = True
                
                # Calculate late load date
                work_date_val = result.loc[idx, date_column]
                if pd.notna(work_date_val):
                    work_date = pd.to_datetime(work_date_val)
                    lag_days = random.randint(1, max_lag_days)
                    load_date = work_date + timedelta(days=lag_days)
                    result.loc[idx, '_simulated_load_date'] = load_date
        
        # For non-late records, load date is same as work date
        non_late_mask = ~result['late_arrival_flag']
        non_late_valid_dates = non_late_mask & result[date_column].notna()
        result.loc[non_late_valid_dates, '_simulated_load_date'] = pd.to_datetime(
            result.loc[non_late_valid_dates, date_column]
        )
        
        return result

