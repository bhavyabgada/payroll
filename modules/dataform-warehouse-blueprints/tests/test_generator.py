"""Unit tests for SQLX generator."""

import pytest
from pathlib import Path
import tempfile

from dataform_blueprints.config import TableConfig, LayerType, TableType
from dataform_blueprints.generator import BlueprintGenerator


def test_generator_initialization():
    """Test BlueprintGenerator initialization."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.STAGING,
        table_type=TableType.SOURCE,
        columns=["col1", "col2"],
    )
    
    generator = BlueprintGenerator(config)
    assert generator.config == config
    assert generator.template_env is not None


def test_generator_staging_table():
    """Test generating staging table SQLX."""
    config = TableConfig(
        table_name="stg_employees",
        layer=LayerType.STAGING,
        table_type=TableType.SOURCE,
        source_table="${ref('raw_employees')}",
        columns=["employee_id", "first_name", "last_name", "updated_at"],
        partition_by="updated_at",
        cluster_by=["employee_id"],
        incremental=True,
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    # Check that SQLX contains expected elements
    assert "config {" in sqlx
    assert 'type: "incremental"' in sqlx
    assert 'schema: "staging"' in sqlx
    assert 'name: "stg_employees"' in sqlx
    assert "employee_id" in sqlx
    assert "first_name" in sqlx
    assert "${ref('raw_employees')}" in sqlx


def test_generator_dimension_table():
    """Test generating dimension table SQLX."""
    config = TableConfig(
        table_name="dim_employee",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        source_table="${ref('stg_employees')}",
        columns=["employee_id", "first_name", "last_name", "email"],
        primary_keys=["employee_id"],
        partition_by="updated_at",
        cluster_by=["employee_id"],
        description="Employee dimension",
        tags=["dimension", "hr"],
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    assert "config {" in sqlx
    assert 'schema: "warehouse"' in sqlx
    assert 'name: "dim_employee"' in sqlx
    assert "-- Dimension Table: dim_employee" in sqlx
    assert "employee_id" in sqlx
    assert "_loaded_at" in sqlx


def test_generator_fact_table():
    """Test generating fact table SQLX."""
    config = TableConfig(
        table_name="fact_payroll",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.FACT,
        source_table="${ref('stg_payroll')}",
        columns=["payroll_id", "employee_id", "gross_pay", "net_pay"],
        primary_keys=["payroll_id"],
        partition_by="pay_date",
        cluster_by=["employee_id"],
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    assert "-- Fact Table: fact_payroll" in sqlx
    assert 'name: "fact_payroll"' in sqlx
    assert "payroll_id" in sqlx
    assert "gross_pay" in sqlx


def test_generator_aggregate_table():
    """Test generating aggregate/mart table SQLX."""
    config = TableConfig(
        table_name="mart_payroll_summary",
        layer=LayerType.MARTS,
        table_type=TableType.AGGREGATE,
        source_table="${ref('fact_payroll')}",
        columns=["department", "SUM(gross_pay) as total_pay"],
        primary_keys=["department"],
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    assert "-- Aggregate/Mart Table: mart_payroll_summary" in sqlx
    assert 'schema: "marts"' in sqlx
    assert "department" in sqlx
    assert "GROUP BY" in sqlx


def test_generator_with_custom_dataset():
    """Test generator with custom dataset ID."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        dataset_id="custom_dataset",
        columns=["id", "name"],
        primary_keys=["id"],
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    assert 'schema: "custom_dataset"' in sqlx


def test_generator_write_sqlx():
    """Test writing SQLX to file."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.STAGING,
        table_type=TableType.SOURCE,
        columns=["col1", "col2"],
    )
    
    generator = BlueprintGenerator(config)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_table.sqlx"
        generator.write_sqlx(str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "config {" in content
        assert "test_table" in content


def test_generator_validate_config_success():
    """Test config validation with valid config."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        source_table="${ref('source')}",
        columns=["id", "name"],
        primary_keys=["id"],
    )
    
    generator = BlueprintGenerator(config)
    errors = generator.validate_config()
    
    assert len(errors) == 0


def test_generator_validate_config_missing_table_name():
    """Test validation with missing table name."""
    config = TableConfig(
        table_name="",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        columns=["col1"],
    )
    
    generator = BlueprintGenerator(config)
    errors = generator.validate_config()
    
    assert len(errors) > 0
    assert any("Table name" in error for error in errors)


def test_generator_validate_config_missing_source():
    """Test validation with missing source table."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        # Missing source_table
        columns=["col1"],
        primary_keys=["col1"],
    )
    
    generator = BlueprintGenerator(config)
    errors = generator.validate_config()
    
    assert len(errors) > 0
    assert any("Source table" in error for error in errors)


def test_generator_validate_config_missing_columns():
    """Test validation with no columns."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        source_table="${ref('source')}",
        columns=[],  # Empty columns
        primary_keys=["id"],
    )
    
    generator = BlueprintGenerator(config)
    errors = generator.validate_config()
    
    assert len(errors) > 0
    assert any("column" in error for error in errors)


def test_generator_validate_config_missing_primary_keys():
    """Test validation with missing primary keys for dimension."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.WAREHOUSE,
        table_type=TableType.DIMENSION,
        source_table="${ref('source')}",
        columns=["col1", "col2"],
        # Missing primary_keys
    )
    
    generator = BlueprintGenerator(config)
    errors = generator.validate_config()
    
    assert len(errors) > 0
    assert any("primary keys" in error.lower() for error in errors)


def test_generator_from_dict():
    """Test creating generator from dictionary."""
    config_dict = {
        "table_name": "test_table",
        "layer": "warehouse",
        "table_type": "dimension",
        "source_table": "${ref('source')}",
        "columns": ["id", "name"],
        "primary_keys": ["id"],
    }
    
    generator = BlueprintGenerator.from_dict(config_dict)
    
    assert generator.config.table_name == "test_table"
    assert generator.config.layer == "warehouse"


def test_generator_from_yaml():
    """Test creating generator from YAML file."""
    yaml_content = """
table_name: test_table
layer: warehouse
table_type: dimension
source_table: ${ref('source')}
columns:
  - id
  - name
primary_keys:
  - id
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        yaml_path = f.name
    
    try:
        generator = BlueprintGenerator.from_yaml(yaml_path)
        
        assert generator.config.table_name == "test_table"
        assert generator.config.layer == "warehouse"
        assert len(generator.config.columns) == 2
    finally:
        Path(yaml_path).unlink()


def test_generator_non_incremental():
    """Test generating non-incremental table."""
    config = TableConfig(
        table_name="test_table",
        layer=LayerType.STAGING,
        table_type=TableType.SOURCE,
        source_table="${ref('raw')}",
        columns=["col1", "col2"],
        incremental=False,
    )
    
    generator = BlueprintGenerator(config)
    sqlx = generator.generate_sqlx()
    
    assert 'type: "table"' in sqlx
    assert "incremental()" not in sqlx

