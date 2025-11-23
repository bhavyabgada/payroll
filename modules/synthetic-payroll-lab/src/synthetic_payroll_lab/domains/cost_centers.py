"""Cost center and GL code generator."""

import pandas as pd


class CostCenterGenerator:
    """Generate cost centers with GL mappings."""
    
    def generate(self, count: int = 50) -> pd.DataFrame:
        """Generate cost center definitions.
        
        Args:
            count: Number of cost centers to generate
        
        Returns:
            DataFrame with cost center data
        """
        departments = [
            "Engineering", "Sales", "Marketing", "Operations",
            "Finance", "HR", "IT", "Customer Service",
            "Research", "Product", "Legal", "Facilities"
        ]
        
        locations = [
            "New York, NY", "San Francisco, CA", "Chicago, IL",
            "Austin, TX", "Boston, MA", "Seattle, WA", "Denver, CO",
            "Atlanta, GA", "Los Angeles, CA", "Portland, OR"
        ]
        
        cost_centers = []
        
        for i in range(1, count + 1):
            dept = departments[i % len(departments)]
            location = locations[i % len(locations)]
            
            cost_centers.append({
                "cost_center_id": i,
                "cost_center_code": f"CC{i:04d}",
                "cost_center_name": f"{dept} - {location}",
                "department": dept,
                "location": location,
                "gl_account": f"{6000 + (i % 10):05d}",  # GL accounts 60000-60009
                "active_flag": "Y",
                "budget_annual": (100000 + (i * 50000)) % 5000000  # Varying budgets
            })
        
        return pd.DataFrame(cost_centers)

