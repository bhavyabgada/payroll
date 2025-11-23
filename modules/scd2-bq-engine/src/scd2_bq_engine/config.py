"""Configuration models for SCD2 generation."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SCD2Config(BaseModel):
    """Configuration for SCD Type 2 dimension generation.
    
    Attributes:
        dimension_name: Name of the dimension table (e.g., 'dim_employee')
        source_table: Fully qualified source table name
        business_keys: List of columns that uniquely identify a business entity
        tracked_columns: Columns to track for changes (SCD2)
        meta_columns: Additional metadata columns (excluded from hash)
        hash_algorithm: Hash algorithm for change detection ('md5' or 'sha256')
        surrogate_key_name: Name of surrogate key column
        effective_from_col: Name of effective from date column
        effective_to_col: Name of effective to date column
        is_current_col: Name of current flag column
        hash_col: Name of hash column for change detection
        handle_late_arrivals: Whether to handle late-arriving dimensions
        soft_delete: Whether to support soft deletes
        partition_by: Partitioning configuration (optional)
        cluster_by: Clustering configuration (optional)
    """
    
    dimension_name: str = Field(..., description="Target dimension table name")
    source_table: str = Field(..., description="Fully qualified source table")
    business_keys: List[str] = Field(..., description="Business key columns")
    tracked_columns: List[str] = Field(..., description="Columns to track for SCD2")
    meta_columns: List[str] = Field(default_factory=list, description="Metadata columns")
    
    # SCD2 configuration
    hash_algorithm: str = Field(default="md5", description="Hash algorithm (md5/sha256)")
    surrogate_key_name: str = Field(default="dimension_key", description="Surrogate key column")
    effective_from_col: str = Field(default="effective_from", description="Effective from column")
    effective_to_col: str = Field(default="effective_to", description="Effective to column")
    is_current_col: str = Field(default="is_current", description="Current flag column")
    hash_col: str = Field(default="row_hash", description="Hash column name")
    
    # Advanced features
    handle_late_arrivals: bool = Field(default=True, description="Handle late arrivals")
    soft_delete: bool = Field(default=True, description="Support soft deletes")
    
    # BigQuery optimization
    partition_by: Optional[str] = Field(default=None, description="Partition column")
    cluster_by: Optional[List[str]] = Field(default=None, description="Cluster columns")
    
    # Output configuration
    project_id: Optional[str] = Field(default=None, description="GCP project ID")
    dataset_id: Optional[str] = Field(default=None, description="BigQuery dataset ID")
    
    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "dimension_name": "dim_employee",
                "source_table": "project.dataset.stg_employees",
                "business_keys": ["employee_number"],
                "tracked_columns": [
                    "first_name",
                    "last_name",
                    "job_code",
                    "department",
                    "manager_id"
                ],
                "meta_columns": ["created_at", "updated_at"],
                "hash_algorithm": "md5",
                "handle_late_arrivals": True,
                "soft_delete": True,
                "partition_by": "effective_from",
                "cluster_by": ["employee_number", "is_current"]
            }
        }

