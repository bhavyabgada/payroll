"""BQ FinOps CLI - BigQuery cost monitoring and optimization toolkit."""

__version__ = "0.1.0"

from bq_finops.analyzer import CostAnalyzer
from bq_finops.optimizer import QueryOptimizer

__all__ = ["CostAnalyzer", "QueryOptimizer", "__version__"]

