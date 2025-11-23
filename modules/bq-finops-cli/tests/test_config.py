"""Unit tests for configuration models."""

import pytest
from pydantic import ValidationError

from bq_finops.config import AnalysisConfig, OptimizationConfig, CostReport


def test_analysis_config_valid():
    """Test creating a valid AnalysisConfig."""
    config = AnalysisConfig(
        project_id="my-project",
        start_date="2025-01-01",
        end_date="2025-01-31",
        datasets=["warehouse", "marts"],
        cost_threshold=500.0
    )
    
    assert config.project_id == "my-project"
    assert config.start_date == "2025-01-01"
    assert len(config.datasets) == 2


def test_analysis_config_defaults():
    """Test default values in AnalysisConfig."""
    config = AnalysisConfig(project_id="test-project")
    
    assert config.cost_threshold == 100.0
    assert config.output_format == "table"
    assert config.datasets is None


def test_analysis_config_missing_project_id():
    """Test that missing project_id raises ValidationError."""
    with pytest.raises(ValidationError):
        AnalysisConfig()


def test_optimization_config_valid():
    """Test creating a valid OptimizationConfig."""
    config = OptimizationConfig(
        project_id="my-project",
        dataset_id="warehouse",
        table_id="fact_sales",
        partition_column="sale_date",
        cluster_columns=["customer_id", "product_id"],
        retention_days=90
    )
    
    assert config.project_id == "my-project"
    assert config.dataset_id == "warehouse"
    assert config.table_id == "fact_sales"
    assert config.partition_column == "sale_date"
    assert len(config.cluster_columns) == 2


def test_optimization_config_optional_fields():
    """Test OptimizationConfig with only required fields."""
    config = OptimizationConfig(
        project_id="my-project",
        dataset_id="warehouse",
        table_id="fact_sales"
    )
    
    assert config.partition_column is None
    assert config.cluster_columns is None
    assert config.retention_days is None


def test_cost_report_valid():
    """Test creating a valid CostReport."""
    report = CostReport(
        total_cost=150.50,
        query_count=1000,
        avg_cost_per_query=0.1505,
        bytes_processed=10000000,
        top_cost_queries=[{"query": "SELECT *", "cost": 50.0}],
        cost_by_dataset={"warehouse": 100.0, "marts": 50.5},
        cost_by_user={"user1@example.com": 150.50}
    )
    
    assert report.total_cost == 150.50
    assert report.query_count == 1000
    assert len(report.cost_by_dataset) == 2


def test_cost_report_defaults():
    """Test default values in CostReport."""
    report = CostReport(
        total_cost=100.0,
        query_count=50,
        avg_cost_per_query=2.0,
        bytes_processed=5000000
    )
    
    assert report.top_cost_queries == []
    assert report.cost_by_dataset == {}
    assert report.cost_by_user == {}


def test_cost_report_to_dict():
    """Test CostReport to_dict conversion."""
    report = CostReport(
        total_cost=100.0,
        query_count=50,
        avg_cost_per_query=2.0,
        bytes_processed=5000000
    )
    
    report_dict = report.to_dict()
    
    assert isinstance(report_dict, dict)
    assert report_dict["total_cost"] == 100.0
    assert report_dict["query_count"] == 50
    assert "top_cost_queries" in report_dict

