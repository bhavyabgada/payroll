"""Unit tests for QueryOptimizer."""

import pytest
from unittest.mock import Mock, patch

from bq_finops.optimizer import QueryOptimizer
from bq_finops.config import OptimizationConfig


def test_query_optimizer_init():
    """Test QueryOptimizer initialization."""
    with patch('bq_finops.optimizer.bigquery.Client'):
        optimizer = QueryOptimizer(project_id="test-project")
        assert optimizer.project_id == "test-project"


def test_generate_partition_ddl():
    """Test partition DDL generation."""
    mock_client = Mock()
    mock_table = Mock()
    mock_field = Mock()
    mock_field.name = "id"
    mock_field.field_type = "INTEGER"
    mock_table.schema = [mock_field]
    mock_client.get_table.return_value = mock_table
    
    optimizer = QueryOptimizer(project_id="test-project", client=mock_client)
    
    ddl = optimizer.generate_partition_ddl(
        "test_dataset",
        "test_table",
        "created_at"
    )
    
    assert "PARTITION BY DAY(created_at)" in ddl
    assert "CREATE OR REPLACE TABLE" in ddl
    assert "test_dataset.test_table" in ddl


def test_generate_cluster_ddl():
    """Test cluster DDL generation."""
    mock_client = Mock()
    mock_table = Mock()
    mock_field = Mock()
    mock_field.name = "id"
    mock_field.field_type = "INTEGER"
    mock_table.schema = [mock_field]
    mock_client.get_table.return_value = mock_table
    
    optimizer = QueryOptimizer(project_id="test-project", client=mock_client)
    
    ddl = optimizer.generate_cluster_ddl(
        "test_dataset",
        "test_table",
        ["customer_id", "product_id"]
    )
    
    assert "CLUSTER BY customer_id, product_id" in ddl
    assert "CREATE OR REPLACE TABLE" in ddl


def test_analyze_query():
    """Test query analysis."""
    with patch('bq_finops.optimizer.bigquery.Client'):
        optimizer = QueryOptimizer(project_id="test-project")
        
        # Test query with SELECT *
        query1 = "SELECT * FROM table"
        analysis1 = optimizer.analyze_query(query1)
        
        assert "recommendations" in analysis1
        assert len(analysis1["recommendations"]) > 0
        assert any("SELECT *" in str(rec) for rec in analysis1["recommendations"])
        
        # Test query with proper columns
        query2 = "SELECT id, name FROM table WHERE date > '2025-01-01' LIMIT 100"
        analysis2 = optimizer.analyze_query(query2)
        
        assert "recommendations" in analysis2


def test_generate_optimization_report():
    """Test optimization report generation."""
    mock_client = Mock()
    mock_table = Mock()
    mock_table.num_rows = 1000000
    mock_table.num_bytes = 50 * (1024 ** 3)  # 50 GB
    mock_table.time_partitioning = None
    mock_table.clustering_fields = None
    
    mock_client.get_table.return_value = mock_table
    
    optimizer = QueryOptimizer(project_id="test-project", client=mock_client)
    
    report = optimizer.generate_optimization_report("test_dataset", "test_table")
    
    assert "table" in report
    assert "current_state" in report
    assert "recommendations" in report
    assert report["current_state"]["partitioned"] is False


def test_query_optimizer_from_config():
    """Test creating optimizer from config."""
    config = OptimizationConfig(
        project_id="test-project",
        dataset_id="test_dataset",
        table_id="test_table"
    )
    
    with patch('bq_finops.optimizer.bigquery.Client'):
        optimizer = QueryOptimizer.from_config(config)
        assert optimizer.project_id == "test-project"


def test_set_table_expiration_non_partitioned():
    """Test setting expiration on non-partitioned table."""
    mock_client = Mock()
    mock_table = Mock()
    mock_table.time_partitioning = None
    mock_client.get_table.return_value = mock_table
    
    optimizer = QueryOptimizer(project_id="test-project", client=mock_client)
    
    result = optimizer.set_table_expiration("test_dataset", "test_table", 90)
    
    assert result is False  # Should fail for non-partitioned table

