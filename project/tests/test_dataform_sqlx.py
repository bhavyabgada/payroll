"""
Tests for Dataform SQLX files
Validates SQL syntax and structure
"""

import pytest
from pathlib import Path
import re


class TestDataformStructure:
    """Test Dataform project structure."""
    
    def test_dataform_config_exists(self):
        """Verify dataform.json exists."""
        dataform_dir = Path(__file__).parent.parent / "dataform"
        assert (dataform_dir / "dataform.json").exists()
    
    def test_package_json_exists(self):
        """Verify package.json exists."""
        dataform_dir = Path(__file__).parent.parent / "dataform"
        assert (dataform_dir / "package.json").exists()
    
    def test_workflow_settings_exists(self):
        """Verify workflow_settings.yaml exists."""
        dataform_dir = Path(__file__).parent.parent / "dataform"
        assert (dataform_dir / "workflow_settings.yaml").exists()


class TestSourceDefinitions:
    """Test source table definitions."""
    
    def test_sources_file_exists(self):
        """Verify sources.js file exists."""
        sources_file = Path(__file__).parent.parent / "dataform" / "definitions" / "sources" / "sources.js"
        assert sources_file.exists()
    
    def test_sources_file_syntax(self):
        """Test sources.js has valid syntax."""
        sources_file = Path(__file__).parent.parent / "dataform" / "definitions" / "sources" / "sources.js"
        
        content = sources_file.read_text()
        
        # Check for declare statements
        assert "declare(" in content
        assert "raw_employees" in content
        assert "raw_jobs" in content
        assert "raw_payroll_runs" in content


class TestStagingLayer:
    """Test staging layer SQLX files."""
    
    def test_staging_files_exist(self):
        """Verify all staging SQLX files exist."""
        staging_dir = Path(__file__).parent.parent / "dataform" / "definitions" / "staging"
        
        assert (staging_dir / "stg_employees.sqlx").exists()
        assert (staging_dir / "stg_jobs.sqlx").exists()
        assert (staging_dir / "stg_payroll_runs.sqlx").exists()
    
    def test_staging_files_have_config(self):
        """Test staging files have config blocks."""
        staging_dir = Path(__file__).parent.parent / "dataform" / "definitions" / "staging"
        
        for sqlx_file in staging_dir.glob("*.sqlx"):
            content = sqlx_file.read_text()
            assert "config {" in content, f"{sqlx_file.name} missing config block"
            assert "type:" in content, f"{sqlx_file.name} missing type"
            assert "schema:" in content, f"{sqlx_file.name} missing schema"
    
    def test_staging_files_have_sql(self):
        """Test staging files have SQL queries."""
        staging_dir = Path(__file__).parent.parent / "dataform" / "definitions" / "staging"
        
        for sqlx_file in staging_dir.glob("*.sqlx"):
            content = sqlx_file.read_text()
            assert "SELECT" in content.upper(), f"{sqlx_file.name} missing SELECT"
            assert "FROM" in content.upper(), f"{sqlx_file.name} missing FROM"


class TestWarehouseLayer:
    """Test warehouse layer SQLX files."""
    
    def test_warehouse_files_exist(self):
        """Verify warehouse SQLX files exist."""
        warehouse_dir = Path(__file__).parent.parent / "dataform" / "definitions" / "warehouse"
        
        assert (warehouse_dir / "dim_employee.sqlx").exists()
        assert (warehouse_dir / "fact_payroll_run.sqlx").exists()
    
    def test_dim_employee_is_scd2(self):
        """Test dim_employee has SCD2 logic."""
        dim_file = Path(__file__).parent.parent / "dataform" / "definitions" / "warehouse" / "dim_employee.sqlx"
        content = dim_file.read_text()
        
        # Check for SCD2 columns
        assert "effective_from" in content or "effective_date" in content
        assert "effective_to" in content or "end_date" in content
        assert "is_current" in content
    
    def test_fact_payroll_has_keys(self):
        """Test fact_payroll_run has key columns."""
        fact_file = Path(__file__).parent.parent / "dataform" / "definitions" / "warehouse" / "fact_payroll_run.sqlx"
        content = fact_file.read_text()
        
        # Check for expected columns
        assert "payroll_id" in content
        assert "employee_id" in content
        assert "pay_date" in content


class TestMartsLayer:
    """Test marts layer SQLX files."""
    
    def test_marts_files_exist(self):
        """Verify marts SQLX files exist."""
        marts_dir = Path(__file__).parent.parent / "dataform" / "definitions" / "marts"
        
        assert (marts_dir / "mart_payroll_summary_by_dept.sqlx").exists()
    
    def test_mart_has_aggregation(self):
        """Test mart has aggregation logic."""
        mart_file = Path(__file__).parent.parent / "dataform" / "definitions" / "marts" / "mart_payroll_summary_by_dept.sqlx"
        content = mart_file.read_text()
        
        # Check for aggregate functions
        assert any(agg in content.upper() for agg in ["SUM(", "COUNT(", "AVG("])
        assert "GROUP BY" in content.upper() or "group by" in content


class TestSQLXQuality:
    """Test SQLX file quality."""
    
    def test_all_sqlx_have_partition_config(self):
        """Test that tables have partitioning configuration."""
        definitions_dir = Path(__file__).parent.parent / "dataform" / "definitions"
        
        for sqlx_file in definitions_dir.rglob("*.sqlx"):
            content = sqlx_file.read_text()
            
            # Should have either partition config or be a source
            if "staging" in str(sqlx_file) or "warehouse" in str(sqlx_file):
                assert "partitionBy" in content or "PARTITION BY" in content.upper(), \
                    f"{sqlx_file.name} should have partitioning"
    
    def test_all_sqlx_have_descriptions(self):
        """Test that tables have descriptions."""
        definitions_dir = Path(__file__).parent.parent / "dataform" / "definitions"
        
        for sqlx_file in definitions_dir.rglob("*.sqlx"):
            if "sources.js" in str(sqlx_file):
                continue
            
            content = sqlx_file.read_text()
            
            # Should have either description in config or as comment
            assert "description:" in content or "-- " in content, \
                f"{sqlx_file.name} should have description"
    
    def test_no_select_star(self):
        """Test that SQLX files don't use SELECT *."""
        definitions_dir = Path(__file__).parent.parent / "dataform" / "definitions"
        
        for sqlx_file in definitions_dir.rglob("*.sqlx"):
            content = sqlx_file.read_text()
            
            # Check for SELECT * (but allow in subqueries)
            lines = content.split("\n")
            for line in lines:
                if "SELECT" in line.upper() and "*" in line:
                    # Allow if it's a comment
                    if not line.strip().startswith("--"):
                        pytest.fail(f"{sqlx_file.name} contains SELECT * on line: {line}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

