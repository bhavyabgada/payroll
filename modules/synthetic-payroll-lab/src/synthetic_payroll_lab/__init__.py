"""Synthetic Payroll Lab - Generate realistic enterprise payroll test data."""

__version__ = "0.1.0"

from synthetic_payroll_lab.generator import PayrollGenerator
from synthetic_payroll_lab.config import ChaosConfig

__all__ = ["PayrollGenerator", "ChaosConfig", "__version__"]

