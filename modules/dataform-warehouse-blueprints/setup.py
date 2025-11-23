"""Setup configuration for dataform-warehouse-blueprints."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="dataform-warehouse-blueprints",
    version="0.1.0",
    author="Bhavya Gada",
    author_email="bhavya@dataeng.io",
    description="Production-ready Dataform SQLX templates for data warehouse patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bhavyagada/dataform-warehouse-blueprints",
    project_urls={
        "Bug Tracker": "https://github.com/bhavyagada/dataform-warehouse-blueprints/issues",
        "Documentation": "https://github.com/bhavyagada/dataform-warehouse-blueprints#readme",
        "Source Code": "https://github.com/bhavyagada/dataform-warehouse-blueprints",
    },
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "dataform_blueprints": ["templates/*.j2"],
    },
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: SQL",
    ],
    python_requires=">=3.8",
    install_requires=[
        "jinja2>=3.0.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "dataform-blueprints=dataform_blueprints.cli:cli",
        ],
    },
    keywords=[
        "dataform",
        "bigquery",
        "sql",
        "sqlx",
        "data-warehouse",
        "data-engineering",
        "templates",
        "code-generation",
    ],
)
