"""
Unit tests for run_data_quality_checks.py script
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_data_quality_checks import run_checkpoint


class TestDataQualityChecks:
    """Test suite for data quality check script."""
    
    @patch('run_data_quality_checks.gx')
    def test_run_checkpoint_success(self, mock_gx):
        """Test successful checkpoint execution."""
        # Setup mocks
        mock_context = Mock()
        mock_checkpoint = Mock()
        mock_result = {
            "success": True,
            "run_results": {}
        }
        
        mock_context.get_checkpoint.return_value = mock_checkpoint
        mock_checkpoint.run.return_value = mock_result
        
        # Run test
        result = run_checkpoint(mock_context, "test_checkpoint")
        
        # Assertions
        assert result is True
        mock_context.get_checkpoint.assert_called_once_with("test_checkpoint")
        mock_checkpoint.run.assert_called_once()
    
    @patch('run_data_quality_checks.gx')
    def test_run_checkpoint_failure(self, mock_gx):
        """Test failed checkpoint execution."""
        # Setup mocks
        mock_context = Mock()
        mock_checkpoint = Mock()
        mock_result = {
            "success": False,
            "run_results": {
                "validation1": {
                    "validation_result": {
                        "results": [
                            {
                                "success": False,
                                "expectation_config": {
                                    "expectation_type": "expect_column_values_to_not_be_null"
                                },
                                "result": {
                                    "observed_value": "50% null"
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        mock_context.get_checkpoint.return_value = mock_checkpoint
        mock_checkpoint.run.return_value = mock_result
        
        # Run test
        result = run_checkpoint(mock_context, "test_checkpoint")
        
        # Assertions
        assert result is False
    
    @patch('run_data_quality_checks.gx')
    def test_run_checkpoint_exception(self, mock_gx):
        """Test checkpoint execution with exception."""
        # Setup mocks
        mock_context = Mock()
        mock_context.get_checkpoint.side_effect = Exception("Checkpoint not found")
        
        # Run test
        result = run_checkpoint(mock_context, "nonexistent_checkpoint")
        
        # Assertions
        assert result is False


class TestDataQualityIntegration:
    """Integration tests for data quality checks."""
    
    def test_checkpoint_files_exist(self):
        """Verify checkpoint files exist."""
        ge_dir = Path(__file__).parent.parent / "great_expectations"
        checkpoints_dir = ge_dir / "checkpoints"
        
        assert (checkpoints_dir / "staging_checkpoint.yml").exists()
        assert (checkpoints_dir / "warehouse_checkpoint.yml").exists()
    
    def test_expectation_suites_exist(self):
        """Verify expectation suite files exist."""
        ge_dir = Path(__file__).parent.parent / "great_expectations"
        expectations_dir = ge_dir / "expectations"
        
        assert (expectations_dir / "staging" / "stg_employees_suite.json").exists()
        assert (expectations_dir / "warehouse" / "fact_payroll_run_suite.json").exists()
    
    def test_ge_config_exists(self):
        """Verify Great Expectations config exists."""
        ge_dir = Path(__file__).parent.parent / "great_expectations"
        assert (ge_dir / "great_expectations.yml").exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

