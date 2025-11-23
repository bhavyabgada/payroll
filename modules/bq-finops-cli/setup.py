"""Setup configuration for bq-finops-cli."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8") if (this_directory / "README.md").exists() else "BQ FinOps CLI - BigQuery cost monitoring and optimization toolkit"

setup(
    name="bq-finops-cli",
    version="0.1.0",
    author="Bhavya Gada",
    author_email="bhavya@dataeng.io",
    description="BigQuery cost monitoring and optimization toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhavyagada/bq-finops-cli",
    project_urls={
        "Bug Tracker": "https://github.com/bhavyagada/bq-finops-cli/issues",
        "Documentation": "https://github.com/bhavyagada/bq-finops-cli#readme",
        "Source Code": "https://github.com/bhavyagada/bq-finops-cli",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "google-cloud-bigquery>=3.0.0",
        "google-cloud-logging>=3.0.0",
        "click>=8.0.0",
        "pydantic>=2.0.0",
        "tabulate>=0.9.0",
        "python-dateutil>=2.8.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-mock>=3.10.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "bq-finops=bq_finops.cli:cli",
        ],
    },
    keywords=[
        "bigquery",
        "gcp",
        "cost-optimization",
        "finops",
        "data-engineering",
        "monitoring",
        "analytics",
    ],
)

