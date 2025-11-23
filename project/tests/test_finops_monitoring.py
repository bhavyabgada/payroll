"""
Unit tests for finops_monitoring.py script
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path
import json

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from finops_monitoring import analyze_costs, optimize_tables


class TestFinOpsMonitoring:
    """Test suite for FinOps monitoring script."""
    
    @patch('finops_monitoring.CostAnalyzer')
    def test_analyze_costs_success(self, mock_analyzer_class):
        """Test successful cost analysis."""
        # Setup mocks
        mock_analyzer = Mock()
        mock_report = Mock()
        mock_report.total_cost = 150.50
        mock_report.query_count = 1000
        mock_report.avg_cost_per_query = 0.1505
        mock_report.bytes_processed = 10000000
        mock_report.cost_by_dataset = {"staging": 50.0, "warehouse": 100.5}
        mock_report.top_cost_queries = [
            {"cost_usd": 25.0, "user": "user1@example.com"}
        ]
        mock_report.to_dict.return_value = {
            "total_cost": 150.50,
            "query_count": 1000
        }
        
        mock_analyzer.analyze_period.return_value = mock_report
        mock_analyzer_class.return_value = mock_analyzer
        
        # Run test
        result = analyze_costs("test-project", days=7)
        
        # Assertions
        assert result["total_cost"] == 150.50
        assert result["query_count"] == 1000
        mock_analyzer.analyze_period.assert_called_once()
    
    @patch('finops_monitoring.QueryOptimizer')
    def test_optimize_tables_success(self, mock_optimizer_class):
        """Test successful table optimization."""
        # Setup mocks
        mock_optimizer = Mock()
        mock_report = {
            "recommendations": [
                {
                    "action": "add_partitioning",
                    "priority": "high",
                    "benefit": "Reduce costs by 50%"
                }
            ]
        }
        
        mock_optimizer.generate_optimization_report.return_value = mock_report
        mock_optimizer_class.return_value = mock_optimizer
        
        # Run test
        result = optimize_tables("test-project")
        
        # Assertions
        assert isinstance(result, dict)
        # Should have checked 5 tables
        assert mock_optimizer.generate_optimization_report.call_count == 5
    
    @patch('finops_monitoring.QueryOptimizer')
    def test_optimize_tables_with_error(self, mock_optimizer_class):
        """Test table optimization with errors."""
        # Setup mocks
        mock_optimizer = Mock()
        mock_optimizer.generate_optimization_report.side_effect = Exception("Table not found")
        mock_optimizer_class.return_value = mock_optimizer
        
        # Run test - should handle exception gracefully
        result = optimize_tables("test-project")
        
        # Assertions
        assert isinstance(result, dict)
        # Should still attempt all 5 tables
        assert mock_optimizer.generate_optimization_report.call_count == 5


class TestFinOpsIntegration:
    """Integration tests for FinOps monitoring."""
    
    def test_script_exists(self):
        """Verify monitoring script exists."""
        script_path = Path(__file__).parent.parent / "scripts" / "finops_monitoring.py"
        assert script_path.exists()
    
    def test_reports_directory_exists(self):
        """Verify reports directory exists."""
        reports_dir = Path(__file__).parent.parent / "reports"
        assert reports_dir.exists()
    
    @patch('finops_monitoring.CostAnalyzer')
    @patch('finops_monitoring.QueryOptimizer')
    def test_budget_check_over_budget(self, mock_optimizer, mock_analyzer):
        """Test budget check when over budget."""
        # Setup
        mock_analyzer_inst = Mock()
        mock_report = Mock()
        mock_report.total_cost = 400.0  # Over $350 budget
        mock_report.query_count = 5000
        mock_report.avg_cost_per_query = 0.08
        mock_report.bytes_processed = 50000000
        mock_report.cost_by_dataset = {}
        mock_report.top_cost_queries = []
        mock_report.to_dict.return_value = {"total_cost": 400.0, "query_count": 5000}
        
        mock_analyzer_inst.analyze_period.return_value = mock_report
        mock_analyzer.return_value = mock_analyzer_inst
        
        # Run
        result = analyze_costs("test-project", days=7)
        
        # Assert
        assert result["total_cost"] > 350.0  # Over budget


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

