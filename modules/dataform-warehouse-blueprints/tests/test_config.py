"""Unit tests for configuration models."""

import pytest
from pydantic import ValidationError

from dataform_blueprints.config import TableConfig, LayerType, TableType


def test_table_config_valid():
    """Test creating a valid TableConfig."""
    config = TableConfig(
        table_name="dim_employee",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        source_table="${ref('stg_employees')}",
        columns=["employee_id", "first_name", "last_name"],
        primary_keys=["employee_id"],
    )
    
    assert config.table_name == "dim_employee"
    assert config.layer == "warehouse"
    assert config.table_type == "dimension"
    assert len(config.columns) == 3


def test_table_config_enums():
    """Test that enum values work correctly."""
    config = TableConfig(
        table_name="test_table",
        layer="staging",
        table_type="fact",
        columns=["col1"],
    )
    
    assert config.layer == "staging"
    assert config.table_type == "fact"


def test_table_config_defaults():
    """Test default values in TableConfig."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.RAW,
        table_type=TableType.SOURCE,
        columns=["col1"],
    )
    
    assert config.incremental is True
    assert config.tags == []
    assert config.dependencies == []
    assert config.assertions == []


def test_table_config_with_partition_cluster():
    """Test TableConfig with partitioning and clustering."""
    config = TableConfig(
        table_name="fact_sales",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.FACT,
        columns=["sale_id", "amount", "sale_date"],
        partition_by="sale_date",
        cluster_by=["sale_id", "customer_id"],
        primary_keys=["sale_id"],
    )
    
    assert config.partition_by == "sale_date"
    assert len(config.cluster_by) == 2
    assert config.cluster_by[0] == "sale_id"


def test_table_config_with_metadata():
    """Test TableConfig with description and tags."""
    config = TableConfig(
        table_name="dim_product",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        columns=["product_id", "product_name"],
        description="Product dimension table",
        tags=["dimension", "sales"],
        primary_keys=["product_id"],
    )
    
    assert config.description == "Product dimension table"
    assert len(config.tags) == 2
    assert "dimension" in config.tags


def test_table_config_missing_required_fields():
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        TableConfig(
            # Missing table_name
            layer=LayerType.WAREHOUSE,
            table_type=TableType.DIMENSION,
            columns=["col1"],
        )


def test_table_config_invalid_layer():
    """Test that invalid layer raises ValidationError."""
    with pytest.raises(ValidationError):
        TableConfig(
            table_name="test",
            layer="invalid_layer",  # Should fail
            table_type=TableType.DIMENSION,
            columns=["col1"],
        )


def test_table_config_invalid_table_type():
    """Test that invalid table_type raises ValidationError."""
    with pytest.raises(ValidationError):
        TableConfig(
            table_name="test",
            layer=LayerType.WAREHOUSE,
            table_type="invalid_type",  # Should fail
            columns=["col1"],
        )


def test_table_config_assertions():
    """Test TableConfig with assertions."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.FACT,
        columns=["col1"],
        assertions=[
            {"description": "Check primary key uniqueness"},
            {"description": "Check no nulls in required fields"},
        ],
    )
    
    assert len(config.assertions) == 2
    assert config.assertions[0]["description"] == "Check primary key uniqueness"


def test_layer_type_enum():
    """Test LayerType enum values."""
    assert LayerType.RAW == "raw"
    assert LayerType.STAGING == "staging"
    assert LayerType.WAREHOUSE == "warehouse"
    assert LayerType.MARTS == "marts"


def test_table_type_enum():
    """Test TableType enum values."""
    assert TableType.SOURCE == "source"
    assert TableType.DIMENSION == "dimension"
    assert TableType.FACT == "fact"
    assert TableType.AGGREGATE == "aggregate"
    assert TableType.VIEW == "view"

