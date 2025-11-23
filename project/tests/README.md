# Project Tests

Comprehensive test suite for the Payroll Analytics Platform

## 📊 Test Coverage

### Test Files
1. **test_dataform_sqlx.py** (16 tests) ✅
   - Dataform structure validation
   - Source definitions
   - Staging layer SQLX files
   - Warehouse layer SQLX files
   - Marts layer SQLX files
   - SQL quality checks

2. **test_data_quality_checks.py** (3 tests)
   - Data quality script functionality
   - Great Expectations integration
   - Checkpoint execution

3. **test_finops_monitoring.py** (4 tests)
   - Cost analysis functionality
   - Table optimization
   - Budget checking

4. **test_airflow_dags.py** (12 tests)
   - DAG structure validation
   - Configuration checks
   - Task dependencies

### Test Results Summary
```
✅ test_dataform_sqlx.py:        16/16 PASSED
✅ test_data_quality_checks.py:  3/3 PASSED
✅ test_finops_monitoring.py:    4/4 PASSED
✅ test_airflow_dags.py:         12/12 PASSED (requires Airflow)
────────────────────────────────────────────
Total:                           35 tests
```

## 🚀 Running Tests

### Run All Tests

```bash
# Using the test runner script
./run_tests.sh

# Or using pytest directly
pytest tests/ -v
```

### Run Specific Test Files

```bash
# Dataform tests only
pytest tests/test_dataform_sqlx.py -v

# Data quality tests
pytest tests/test_data_quality_checks.py -v

# FinOps tests
pytest tests/test_finops_monitoring.py -v

# Airflow DAG tests
pytest tests/test_airflow_dags.py -v
```

### Run with Coverage

```bash
pytest tests/ --cov=scripts --cov-report=term-missing --cov-report=html
```

View coverage report: `htmlcov/index.html`

## 📋 Test Requirements

```bash
pip install pytest pytest-mock pytest-cov
```

## 🧪 Test Categories

### Unit Tests
- Scripts functionality
- Configuration validation
- Helper functions

### Integration Tests
- File existence checks
- Configuration integrity
- SQLX structure validation

### Smoke Tests
- DAG loading
- Syntax validation
- Import checks

## ✅ What's Tested

### ✅ Dataform SQLX
- Config blocks presence
- SQL syntax
- Partitioning configuration
- Descriptions
- SCD2 logic (dim_employee)
- Aggregation logic (marts)
- No SELECT * anti-pattern

### ✅ Data Quality
- Checkpoint execution
- Great Expectations config
- Expectation suites
- Validation results

### ✅ FinOps Monitoring
- Cost analysis
- Table optimization
- Budget checking
- Report generation

### ✅ Airflow DAGs
- DAG loading
- Configuration
- Task presence
- Dependencies
- Schedule intervals

## 🐛 Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`:

```bash
# Install project dependencies
pip install -r requirements.txt

# Install test dependencies
pip install -r requirements-dev.txt
```

### Airflow Tests Skipped

Airflow DAG tests require Airflow to be installed:

```bash
pip install apache-airflow>=2.7.0
```

Or run without Airflow tests:

```bash
pytest tests/ -k "not airflow"
```

### Great Expectations Errors

If GE tests fail:

```bash
pip install great-expectations>=0.18.0
```

## 📝 Writing New Tests

### Test File Template

```python
"""
Tests for [component name]
"""

import pytest
from pathlib import Path


class TestComponentName:
    """Test suite for [component]."""
    
    def test_something(self):
        """Test description."""
        # Arrange
        ...
        
        # Act
        ...
        
        # Assert
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Best Practices

1. **Descriptive names**: `test_dim_employee_has_scd2_columns`
2. **One assertion per test**: Focus on single behavior
3. **Arrange-Act-Assert**: Clear test structure
4. **Mock external dependencies**: Don't hit real GCP
5. **Use fixtures**: Share setup code

## 🎯 CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-cov
      - run: pytest tests/ --cov=scripts
```

## 📊 Coverage Goals

Target coverage by component:
- Scripts: 80%+
- Configuration: 100%
- SQLX validation: 100%

## 🔗 Related Documentation

- [pytest documentation](https://docs.pytest.org/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

---

**Test with confidence! 🧪✅**
