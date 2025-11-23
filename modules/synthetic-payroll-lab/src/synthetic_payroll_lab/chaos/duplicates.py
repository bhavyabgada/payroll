"""Duplicate row injector."""

import random
import pandas as pd


class DuplicateInjector:
    """Inject duplicate rows to simulate data quality issues."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
    
    def inject(self, df: pd.DataFrame, rate: float = 0.02) -> pd.DataFrame:
        """Inject duplicate rows into DataFrame.
        
        Args:
            df: Input DataFrame
            rate: Percentage of rows to duplicate (0.0-1.0)
        
        Returns:
            DataFrame with duplicates injected
        """
        if rate <= 0 or df.empty:
            return df
        
        # Calculate number of duplicates to inject
        num_duplicates = int(len(df) * rate)
        
        if num_duplicates == 0:
            return df
        
        # Randomly select rows to duplicate
        duplicate_indices = random.sample(range(len(df)), min(num_duplicates, len(df)))
        duplicates = df.iloc[duplicate_indices].copy()
        
        # Append duplicates
        result = pd.concat([df, duplicates], ignore_index=True)
        
        # Shuffle to mix duplicates throughout
        result = result.sample(frac=1.0).reset_index(drop=True)
        
        return result

