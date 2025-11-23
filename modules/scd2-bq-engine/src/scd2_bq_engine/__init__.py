"""SCD2 BigQuery Engine - SCD Type 2 dimension builder for BigQuery."""

__version__ = "0.1.0"

from scd2_bq_engine.config import SCD2Config
from scd2_bq_engine.generator import SCD2Generator

__all__ = ["SCD2Config", "SCD2Generator", "__version__"]

