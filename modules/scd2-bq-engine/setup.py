"""Setup configuration for scd2-bq-engine."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="scd2-bq-engine",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="BigQuery SCD Type 2 dimension builder with SQLX generation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/scd2-bq-engine",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Database",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
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
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "scd2-bq=scd2_bq_engine.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "scd2_bq_engine": ["templates/*.j2"],
    },
)

