"""Foreign key orphan injector."""

import random
import pandas as pd


class FKOrphanInjector:
    """Create orphaned foreign key references."""
    
    def __init__(self, seed: int = None):
        if seed:
            random.seed(seed)
    
    def inject(
        self, 
        df: pd.DataFrame, 
        fk_column: str,
        rate: float = 0.01
    ) -> pd.DataFrame:
        """Inject orphaned foreign key values.
        
        Args:
            df: Input DataFrame
            fk_column: Name of foreign key column
            rate: Percentage of FKs to orphan (0.0-1.0)
        
        Returns:
            DataFrame with orphaned FK values
        """
        if rate <= 0 or df.empty or fk_column not in df.columns:
            return df
        
        result = df.copy()
        
        # Calculate number of orphans to create
        num_orphans = int(len(result) * rate)
        
        if num_orphans == 0:
            return result
        
        # Select random rows to orphan
        orphan_indices = random.sample(range(len(result)), num_orphans)
        
        # Generate fake FK values that don't exist
        for idx in orphan_indices:
            current_value = result.loc[idx, fk_column]
            
            if pd.isna(current_value):
                continue
            
            # Generate an orphaned value
            if isinstance(current_value, str):
                if current_value.startswith('EMP'):
                    # Employee ID - generate non-existent one
                    result.loc[idx, fk_column] = f'EMP{random.randint(900000, 999999):06d}'
                elif current_value.startswith('CC'):
                    # Cost center - generate non-existent one
                    result.loc[idx, fk_column] = f'CC{random.randint(9000, 9999):04d}'
                else:
                    # Generic - append '_INVALID'
                    result.loc[idx, fk_column] = f'{current_value}_INVALID'
            else:
                # Numeric FK - use very large number
                result.loc[idx, fk_column] = 999999
        
        return result
    
    def inject_multiple(
        self,
        df: pd.DataFrame,
        fk_columns: list,
        rate: float = 0.01
    ) -> pd.DataFrame:
        """Inject orphans across multiple FK columns.
        
        Args:
            df: Input DataFrame
            fk_columns: List of FK column names
            rate: Percentage of FKs to orphan per column
        
        Returns:
            DataFrame with orphaned FKs
        """
        result = df.copy()
        
        for fk_col in fk_columns:
            if fk_col in result.columns:
                result = self.inject(result, fk_col, rate)
        
        return result

