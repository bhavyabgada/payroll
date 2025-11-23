"""Null value spike injector."""

import random
import pandas as pd
import numpy as np


class NullInjector:
    """Inject random null values to simulate data quality spikes."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
            np.random.seed(seed)
    
    def inject(
        self, 
        df: pd.DataFrame, 
        rate: float = 0.01,
        exclude_columns: list = None
    ) -> pd.DataFrame:
        """Inject null values randomly into DataFrame.
        
        Args:
            df: Input DataFrame
            rate: Percentage of values to null (0.0-1.0)
            exclude_columns: List of columns to exclude from null injection
        
        Returns:
            DataFrame with nulls injected
        """
        if rate <= 0 or df.empty:
            return df
        
        result = df.copy()
        exclude_columns = exclude_columns or []
        
        # Get eligible columns (excluding specified and key columns)
        key_patterns = ['_id', '_key', 'person_id', 'assignment_id']
        eligible_columns = [
            col for col in result.columns 
            if col not in exclude_columns and 
            not any(pattern in col.lower() for pattern in key_patterns)
        ]
        
        if not eligible_columns:
            return result
        
        # Inject nulls randomly
        for col in eligible_columns:
            # Skip if column already has nulls
            if result[col].dtype == object or pd.api.types.is_numeric_dtype(result[col]):
                # Randomly null out values
                mask = np.random.random(len(result)) < rate
                result.loc[mask, col] = None
        
        return result

