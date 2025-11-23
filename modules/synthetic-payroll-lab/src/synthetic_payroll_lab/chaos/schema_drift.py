"""Schema drift injector."""

import random
import pandas as pd
import numpy as np


class SchemaDriftInjector:
    """Inject schema changes to simulate evolving schemas."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def inject(
        self, 
        df: pd.DataFrame, 
        drift_type: str = 'add_column',
        column_name: str = None
    ) -> pd.DataFrame:
        """Inject schema drift into DataFrame.
        
        Args:
            df: Input DataFrame
            drift_type: Type of drift ('add_column', 'rename_column', 'change_type')
            column_name: Name for new/renamed column
        
        Returns:
            DataFrame with schema drift applied
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        if drift_type == 'add_column':
            # Add a new column with random data
            col_name = column_name or f'new_column_{random.randint(1000, 9999)}'
            result[col_name] = np.random.choice(
                ['Value_A', 'Value_B', 'Value_C', None],
                size=len(result),
                p=[0.4, 0.3, 0.2, 0.1]
            )
        
        elif drift_type == 'rename_column':
            # Rename a random non-key column
            eligible_columns = [
                col for col in result.columns 
                if '_id' not in col.lower() and 'key' not in col.lower()
            ]
            if eligible_columns:
                old_col = random.choice(eligible_columns)
                new_col = column_name or f'{old_col}_renamed'
                result = result.rename(columns={old_col: new_col})
        
        elif drift_type == 'change_type':
            # Change data type of a column (e.g., numeric to string)
            numeric_columns = result.select_dtypes(include=[np.number]).columns.tolist()
            if numeric_columns:
                col = random.choice(numeric_columns)
                result[col] = result[col].astype(str)
        
        return result
    
    def inject_progressive(
        self,
        df: pd.DataFrame,
        date_column: str,
        drift_interval_days: int = 90
    ) -> pd.DataFrame:
        """Inject progressive schema drift based on dates.
        
        Simulates new columns being added over time.
        
        Args:
            df: Input DataFrame
            date_column: Column to use for date-based drift
            drift_interval_days: Add new column every N days
        
        Returns:
            DataFrame with progressive schema drift
        """
        if df.empty or date_column not in df.columns:
            return df
        
        result = df.copy()
        result[date_column] = pd.to_datetime(result[date_column])
        
        # Get date range
        min_date = result[date_column].min()
        max_date = result[date_column].max()
        
        # Calculate drift points
        current_date = min_date + pd.Timedelta(days=drift_interval_days)
        drift_num = 1
        
        while current_date <= max_date:
            # Add column for records after this date
            col_name = f'drift_field_{drift_num}'
            mask = result[date_column] >= current_date
            result.loc[mask, col_name] = f'Value_{drift_num}'
            result.loc[~mask, col_name] = None  # Older records don't have this column
            
            current_date += pd.Timedelta(days=drift_interval_days)
            drift_num += 1
        
        return result

