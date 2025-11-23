"""Configuration models for BQ FinOps."""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class AnalysisConfig(BaseModel):
    """Configuration for cost analysis.
    
    Attributes:
        project_id: GCP project ID
        start_date: Analysis start date
        end_date: Analysis end date
        datasets: List of datasets to analyze (None = all)
        cost_threshold: Alert threshold in USD
        output_format: Output format (table, json, csv)
    """
    
    project_id: str = Field(..., description="GCP project ID")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    datasets: Optional[List[str]] = Field(None, description="Datasets to analyze")
    cost_threshold: float = Field(default=100.0, description="Cost alert threshold (USD)")
    output_format: str = Field(default="table", description="Output format")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "project_id": "my-gcp-project",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "datasets": ["warehouse", "marts"],
                "cost_threshold": 500.0,
                "output_format": "table"
            }
        }


class OptimizationConfig(BaseModel):
    """Configuration for query optimization.
    
    Attributes:
        project_id: GCP project ID
        dataset_id: Dataset ID
        table_id: Table ID
        partition_column: Column to partition by
        cluster_columns: Columns to cluster by
        retention_days: Data retention in days
    """
    
    project_id: str = Field(..., description="GCP project ID")
    dataset_id: str = Field(..., description="Dataset ID")
    table_id: str = Field(..., description="Table ID")
    partition_column: Optional[str] = Field(None, description="Partition column")
    cluster_columns: Optional[List[str]] = Field(None, description="Cluster columns")
    retention_days: Optional[int] = Field(None, description="Retention days")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "project_id": "my-gcp-project",
                "dataset_id": "warehouse",
                "table_id": "fact_sales",
                "partition_column": "sale_date",
                "cluster_columns": ["customer_id", "product_id"],
                "retention_days": 90
            }
        }


class CostReport(BaseModel):
    """Cost analysis report.
    
    Attributes:
        total_cost: Total cost in USD
        query_count: Number of queries
        avg_cost_per_query: Average cost per query
        top_cost_queries: List of most expensive queries
        cost_by_dataset: Cost breakdown by dataset
        cost_by_user: Cost breakdown by user
    """
    
    total_cost: float = Field(..., description="Total cost (USD)")
    query_count: int = Field(..., description="Number of queries")
    avg_cost_per_query: float = Field(..., description="Avg cost per query")
    bytes_processed: int = Field(..., description="Total bytes processed")
    top_cost_queries: List[dict] = Field(default_factory=list, description="Top queries")
    cost_by_dataset: dict = Field(default_factory=dict, description="Cost by dataset")
    cost_by_user: dict = Field(default_factory=dict, description="Cost by user")
    
    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "total_cost": self.total_cost,
            "query_count": self.query_count,
            "avg_cost_per_query": self.avg_cost_per_query,
            "bytes_processed": self.bytes_processed,
            "top_cost_queries": self.top_cost_queries,
            "cost_by_dataset": self.cost_by_dataset,
            "cost_by_user": self.cost_by_user,
        }

