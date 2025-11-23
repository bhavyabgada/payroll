"""Configuration models for Dataform blueprints."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class LayerType(str, Enum):
    """Data warehouse layer types."""
    RAW = "raw"
    STAGING = "staging"
    WAREHOUSE = "warehouse"
    MARTS = "marts"


class TableType(str, Enum):
    """Table pattern types."""
    SOURCE = "source"
    DIMENSION = "dimension"
    FACT = "fact"
    AGGREGATE = "aggregate"
    VIEW = "view"


class TableConfig(BaseModel):
    """Configuration for generating a Dataform table.
    
    Attributes:
        table_name: Name of the table
        layer: Data warehouse layer (raw/staging/warehouse/marts)
        table_type: Type of table (dimension/fact/aggregate/view)
        source_table: Fully qualified source table name
        columns: List of column names to include
        partition_by: Column to partition by
        cluster_by: Columns to cluster by
        primary_keys: Primary key columns
        description: Table description
        tags: Tags for the table
        incremental: Whether to use incremental loading
        dependencies: List of table dependencies
    """
    
    table_name: str = Field(..., description="Target table name")
    layer: LayerType = Field(..., description="Warehouse layer")
    table_type: TableType = Field(..., description="Table pattern type")
    source_table: Optional[str] = Field(None, description="Source table reference")
    
    # Schema
    columns: List[str] = Field(default_factory=list, description="Column names")
    partition_by: Optional[str] = Field(None, description="Partition column")
    cluster_by: Optional[List[str]] = Field(None, description="Cluster columns")
    primary_keys: Optional[List[str]] = Field(None, description="Primary key columns")
    
    # Metadata
    description: Optional[str] = Field(None, description="Table description")
    tags: List[str] = Field(default_factory=list, description="Table tags")
    
    # Loading strategy
    incremental: bool = Field(default=True, description="Use incremental loading")
    dependencies: List[str] = Field(default_factory=list, description="Table dependencies")
    
    # Additional config
    dataset_id: Optional[str] = Field(None, description="BigQuery dataset ID")
    assertions: List[Dict[str, Any]] = Field(default_factory=list, description="Data quality assertions")
    
    class Config:
        """Pydantic config."""
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "table_name": "dim_employee",
                "layer": "warehouse",
                "table_type": "dimension",
                "source_table": "${ref('stg_employees')}",
                "columns": ["employee_id", "first_name", "last_name"],
                "partition_by": "updated_at",
                "cluster_by": ["employee_id"],
                "primary_keys": ["employee_id"],
                "description": "Employee dimension",
                "tags": ["dimension", "hr"],
                "incremental": True
            }
        }


class ProjectConfig(BaseModel):
    """Configuration for a Dataform project.
    
    Attributes:
        project_name: Name of the Dataform project
        default_dataset: Default BigQuery dataset
        default_location: Default BigQuery location
        tables: List of table configurations
    """
    
    project_name: str = Field(..., description="Project name")
    default_dataset: str = Field(..., description="Default dataset")
    default_location: str = Field(default="US", description="BigQuery location")
    tables: List[TableConfig] = Field(default_factory=list, description="Table configurations")

