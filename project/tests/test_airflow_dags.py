"""
Unit tests for Airflow DAGs
Tests DAG structure, dependencies, and configuration
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add airflow dags directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "airflow" / "dags"))


class TestDAGStructure:
    """Test DAG structure and configuration."""
    
    def test_main_pipeline_dag_loads(self):
        """Test that main pipeline DAG loads without errors."""
        try:
            from payroll_main_pipeline import dag
            assert dag is not None
            assert dag.dag_id == "payroll_main_pipeline"
        except ImportError as e:
            pytest.skip(f"DAG requires Airflow: {e}")
    
    def test_cost_monitoring_dag_loads(self):
        """Test that cost monitoring DAG loads without errors."""
        try:
            from cost_monitoring_dag import dag
            assert dag is not None
            assert dag.dag_id == "cost_monitoring_weekly"
        except ImportError as e:
            pytest.skip(f"DAG requires Airflow: {e}")
    
    def test_test_data_dag_loads(self):
        """Test that test data generation DAG loads without errors."""
        try:
            from generate_test_data_dag import dag
            assert dag is not None
            assert dag.dag_id == "generate_test_data"
        except ImportError as e:
            pytest.skip(f"DAG requires Airflow: {e}")


class TestMainPipelineDAG:
    """Test main pipeline DAG configuration."""
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_configuration(self):
        """Test DAG configuration settings."""
        from payroll_main_pipeline import dag
        
        assert dag.schedule_interval == "0 2 * * *"  # Daily at 2 AM
        assert dag.catchup is False
        assert dag.max_active_runs == 1
        assert "payroll" in dag.tags
        assert "dataform" in dag.tags
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_has_expected_tasks(self):
        """Test that DAG has all expected tasks."""
        from payroll_main_pipeline import dag
        
        task_ids = [task.task_id for task in dag.tasks]
        
        # Check for key tasks
        assert "check_employees_data" in task_ids
        assert "check_payroll_data" in task_ids
        assert "compile_dataform" in task_ids
        assert "notify_success" in task_ids
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_task_dependencies(self):
        """Test DAG task dependencies are correct."""
        from payroll_main_pipeline import dag
        
        # Get task by ID
        compile_task = dag.get_task("compile_dataform")
        
        # Check upstream dependencies
        upstream_ids = [t.task_id for t in compile_task.upstream_list]
        assert "check_employees_data" in upstream_ids
        assert "check_payroll_data" in upstream_ids


class TestCostMonitoringDAG:
    """Test cost monitoring DAG configuration."""
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_configuration(self):
        """Test DAG configuration settings."""
        from cost_monitoring_dag import dag
        
        assert dag.schedule_interval == "0 8 * * MON"  # Monday 8 AM
        assert dag.catchup is False
        assert "finops" in dag.tags
        assert "cost" in dag.tags
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_has_expected_tasks(self):
        """Test that DAG has all expected tasks."""
        from cost_monitoring_dag import dag
        
        task_ids = [task.task_id for task in dag.tasks]
        
        assert "analyze_weekly_costs" in task_ids
        assert "send_cost_report" in task_ids
        assert "archive_reports" in task_ids


class TestTestDataGenerationDAG:
    """Test data generation DAG configuration."""
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_configuration(self):
        """Test DAG configuration settings."""
        from generate_test_data_dag import dag
        
        assert dag.schedule_interval is None  # Manual trigger
        assert dag.catchup is False
        assert "testing" in dag.tags
        assert "synthetic-data" in dag.tags
    
    @pytest.mark.skipif(True, reason="Requires Airflow installation")
    def test_dag_has_expected_tasks(self):
        """Test that DAG has all expected tasks."""
        from generate_test_data_dag import dag
        
        task_ids = [task.task_id for task in dag.tasks]
        
        assert "generate_data" in task_ids
        assert "upload_to_gcs" in task_ids
        assert "load_to_bigquery" in task_ids
        assert "trigger_pipeline" in task_ids


class TestDAGFiles:
    """Test DAG file structure."""
    
    def test_dag_files_exist(self):
        """Verify all expected DAG files exist."""
        dags_dir = Path(__file__).parent.parent / "airflow" / "dags"
        
        assert (dags_dir / "payroll_main_pipeline.py").exists()
        assert (dags_dir / "cost_monitoring_dag.py").exists()
        assert (dags_dir / "generate_test_data_dag.py").exists()
    
    def test_dag_files_syntax(self):
        """Test that DAG files have valid Python syntax."""
        dags_dir = Path(__file__).parent.parent / "airflow" / "dags"
        
        for dag_file in dags_dir.glob("*.py"):
            if dag_file.name.startswith("_"):
                continue
            
            try:
                with open(dag_file, "r") as f:
                    compile(f.read(), str(dag_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Syntax error in {dag_file.name}: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

