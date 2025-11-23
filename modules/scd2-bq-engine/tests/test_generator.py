"""Tests for SCD2Generator."""

import pytest
from pathlib import Path
from scd2_bq_engine import SCD2Generator, SCD2Config


class TestSCD2Generator:
    """Test SCD2Generator class."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name", "value"]
        )
        
        generator = SCD2Generator(config)
        assert generator.config == config
        assert generator.template_env is not None
    
    def test_sqlx_generation(self):
        """Test SQLX generation."""
        config = SCD2Config(
            dimension_name="dim_employee",
            source_table="project.dataset.stg_employees",
            business_keys=["employee_id"],
            tracked_columns=["first_name", "last_name", "department"]
        )
        
        generator = SCD2Generator(config)
        sqlx = generator.generate_sqlx()
        
        assert len(sqlx) > 0
        assert "dim_employee" in sqlx
        assert "employee_id" in sqlx
        assert "first_name" in sqlx
        assert "SCD Type 2" in sqlx
        assert "config {" in sqlx
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name"]
        )
        
        generator = SCD2Generator(config)
        errors = generator.validate_config()
        
        assert len(errors) == 0
    
    def test_validate_config_no_business_keys(self):
        """Test validation fails without business keys."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=[],
            tracked_columns=["name"]
        )
        
        generator = SCD2Generator(config)
        errors = generator.validate_config()
        
        assert len(errors) > 0
        assert any("business key" in err.lower() for err in errors)
    
    def test_validate_config_no_tracked_columns(self):
        """Test validation fails without tracked columns."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=[]
        )
        
        generator = SCD2Generator(config)
        errors = generator.validate_config()
        
        assert len(errors) > 0
        assert any("tracked column" in err.lower() for err in errors)
    
    def test_validate_config_invalid_hash(self):
        """Test validation fails with invalid hash algorithm."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name"],
            hash_algorithm="invalid"
        )
        
        generator = SCD2Generator(config)
        errors = generator.validate_config()
        
        assert len(errors) > 0
        assert any("hash algorithm" in err.lower() for err in errors)
    
    def test_from_dict(self):
        """Test creating generator from dictionary."""
        config_dict = {
            "dimension_name": "dim_test",
            "source_table": "project.dataset.stg_test",
            "business_keys": ["test_id"],
            "tracked_columns": ["name", "value"]
        }
        
        generator = SCD2Generator.from_dict(config_dict)
        assert generator.config.dimension_name == "dim_test"
        assert len(generator.config.tracked_columns) == 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

