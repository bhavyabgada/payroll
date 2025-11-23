"""Unit tests for CostAnalyzer."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from bq_finops.analyzer import CostAnalyzer
from bq_finops.config import AnalysisConfig, CostReport


def test_cost_analyzer_init():
    """Test CostAnalyzer initialization."""
    with patch('bq_finops.analyzer.bigquery.Client'):
        analyzer = CostAnalyzer(project_id="test-project")
        assert analyzer.project_id == "test-project"


def test_calculate_query_cost():
    """Test query cost calculation."""
    with patch('bq_finops.analyzer.bigquery.Client'):
        analyzer = CostAnalyzer(project_id="test-project")
        
        # 1 TB = $6.25
        bytes_1tb = 1024 ** 4
        cost = analyzer.calculate_query_cost(bytes_1tb)
        assert cost == 6.25
        
        # 0.5 TB = $3.125
        cost_half = analyzer.calculate_query_cost(bytes_1tb // 2)
        assert abs(cost_half - 3.125) < 0.01


def test_cost_analyzer_from_config():
    """Test creating analyzer from config."""
    config = AnalysisConfig(
        project_id="test-project",
        start_date="2025-01-01",
        end_date="2025-01-31"
    )
    
    with patch('bq_finops.analyzer.bigquery.Client'):
        analyzer = CostAnalyzer.from_config(config)
        assert analyzer.project_id == "test-project"


def test_analyze_period_empty_results():
    """Test analyze_period with no query results."""
    mock_client = Mock()
    mock_result = Mock()
    mock_result.result.side_effect = Exception("No data")
    mock_client.query.return_value = mock_result
    
    analyzer = CostAnalyzer(project_id="test-project", client=mock_client)
    
    report = analyzer.analyze_period()
    
    assert isinstance(report, CostReport)
    assert report.total_cost == 0.0
    assert report.query_count == 0


def test_analyze_table_metadata():
    """Test table analysis."""
    mock_client = Mock()
    mock_table = Mock()
    mock_table.num_rows = 1000000
    mock_table.num_bytes = 10 * (1024 ** 3)  # 10 GB
    mock_table.created = "2025-01-01"
    mock_table.modified = "2025-01-15"
    mock_table.time_partitioning = None
    mock_table.clustering_fields = None
    
    mock_client.get_table.return_value = mock_table
    
    analyzer = CostAnalyzer(project_id="test-project", client=mock_client)
    
    analysis = analyzer.analyze_table("test_dataset", "test_table")
    
    assert "table" in analysis
    assert "num_rows" in analysis
    assert "recommendations" in analysis
    assert analysis["num_rows"] == 1000000


def test_get_dataset_cost():
    """Test dataset cost calculation."""
    mock_client = Mock()
    mock_result = Mock()
    mock_result.result.side_effect = Exception("No data")
    mock_client.query.return_value = mock_result
    
    analyzer = CostAnalyzer(project_id="test-project", client=mock_client)
    
    cost_info = analyzer.get_dataset_cost("test_dataset", days=30)
    
    assert isinstance(cost_info, dict)
    assert "dataset_id" in cost_info
    assert cost_info["dataset_id"] == "test_dataset"

