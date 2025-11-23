"""Tests for SCD2Config."""

import pytest
from scd2_bq_engine import SCD2Config


class TestSCD2Config:
    """Test SCD2Config class."""
    
    def test_basic_config(self):
        """Test basic configuration."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name", "value"]
        )
        
        assert config.dimension_name == "dim_test"
        assert config.source_table == "project.dataset.stg_test"
        assert config.business_keys == ["test_id"]
        assert len(config.tracked_columns) == 2
    
    def test_default_values(self):
        """Test default configuration values."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name"]
        )
        
        assert config.hash_algorithm == "md5"
        assert config.surrogate_key_name == "dimension_key"
        assert config.effective_from_col == "effective_from"
        assert config.effective_to_col == "effective_to"
        assert config.is_current_col == "is_current"
        assert config.hash_col == "row_hash"
        assert config.handle_late_arrivals is True
        assert config.soft_delete is True
    
    def test_custom_values(self):
        """Test custom configuration values."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name"],
            hash_algorithm="sha256",
            surrogate_key_name="sk",
            effective_from_col="valid_from",
            effective_to_col="valid_to",
            partition_by="valid_from",
            cluster_by=["test_id", "is_current"]
        )
        
        assert config.hash_algorithm == "sha256"
        assert config.surrogate_key_name == "sk"
        assert config.effective_from_col == "valid_from"
        assert config.effective_to_col == "valid_to"
        assert config.partition_by == "valid_from"
        assert config.cluster_by == ["test_id", "is_current"]
    
    def test_meta_columns(self):
        """Test metadata columns."""
        config = SCD2Config(
            dimension_name="dim_test",
            source_table="project.dataset.stg_test",
            business_keys=["test_id"],
            tracked_columns=["name"],
            meta_columns=["created_at", "updated_at"]
        )
        
        assert len(config.meta_columns) == 2
        assert "created_at" in config.meta_columns
        assert "updated_at" in config.meta_columns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

