"""Setup configuration for synthetic-payroll-lab package."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="synthetic-payroll-lab",
    version="0.1.0",
    author="Data Engineering Team",
    author_email="dataeng@company.com",
    description="Generate realistic enterprise payroll test data with chaos patterns",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourorg/synthetic-payroll-lab",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Testing",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=[
        "faker>=20.0.0",
        "mimesis>=11.0.0",
        "pandas>=2.0.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
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
            "synthetic-payroll=synthetic_payroll_lab.cli:main",
        ],
    },
)

