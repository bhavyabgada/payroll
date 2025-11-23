"""SCD2 SQLX Generator."""

import os
from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader, Template

from scd2_bq_engine.config import SCD2Config


class SCD2Generator:
    """Generate SCD Type 2 dimension SQLX files from configuration.
    
    This generator creates Dataform-compatible SQLX files that implement
    SCD Type 2 logic for BigQuery dimensions.
    
    Attributes:
        config: SCD2 configuration object
        template_env: Jinja2 environment for rendering templates
    """
    
    def __init__(self, config: SCD2Config):
        """Initialize generator with configuration.
        
        Args:
            config: SCD2Config object with dimension specification
        """
        self.config = config
        self.template_env = self._setup_template_environment()
    
    def _setup_template_environment(self) -> Environment:
        """Set up Jinja2 template environment.
        
        Returns:
            Configured Jinja2 Environment
        """
        template_dir = Path(__file__).parent / "templates"
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env
    
    def generate_sqlx(self) -> str:
        """Generate SQLX content from configuration.
        
        Returns:
            Generated SQLX string
        """
        template = self.template_env.get_template("scd2_dimension.sqlx.j2")
        
        sqlx_content = template.render(
            dimension_name=self.config.dimension_name,
            source_table=self.config.source_table,
            business_keys=self.config.business_keys,
            tracked_columns=self.config.tracked_columns,
            meta_columns=self.config.meta_columns,
            hash_algorithm=self.config.hash_algorithm,
            surrogate_key_name=self.config.surrogate_key_name,
            effective_from_col=self.config.effective_from_col,
            effective_to_col=self.config.effective_to_col,
            is_current_col=self.config.is_current_col,
            hash_col=self.config.hash_col,
            handle_late_arrivals=self.config.handle_late_arrivals,
            soft_delete=self.config.soft_delete,
            partition_by=self.config.partition_by,
            cluster_by=self.config.cluster_by,
            project_id=self.config.project_id,
            dataset_id=self.config.dataset_id,
        )
        
        return sqlx_content
    
    def write_sqlx(self, output_path: str) -> None:
        """Generate and write SQLX file to disk.
        
        Args:
            output_path: Path to output SQLX file
        """
        sqlx_content = self.generate_sqlx()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(sqlx_content)
        
        print(f"✅ Generated SCD2 dimension: {output_file}")
    
    def validate_config(self) -> list:
        """Validate configuration and return any errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate business keys
        if not self.config.business_keys:
            errors.append("At least one business key is required")
        
        # Validate tracked columns
        if not self.config.tracked_columns:
            errors.append("At least one tracked column is required")
        
        # Validate hash algorithm
        if self.config.hash_algorithm.lower() not in ["md5", "sha256"]:
            errors.append(f"Invalid hash algorithm: {self.config.hash_algorithm}")
        
        # Check for duplicate columns
        all_columns = (
            self.config.business_keys +
            self.config.tracked_columns +
            self.config.meta_columns
        )
        if len(all_columns) != len(set(all_columns)):
            errors.append("Duplicate columns found in configuration")
        
        return errors
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "SCD2Generator":
        """Create generator from YAML configuration file.
        
        Args:
            yaml_path: Path to YAML configuration file
        
        Returns:
            SCD2Generator instance
        """
        import yaml
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        config = SCD2Config(**config_dict)
        return cls(config)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "SCD2Generator":
        """Create generator from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            SCD2Generator instance
        """
        config = SCD2Config(**config_dict)
        return cls(config)

