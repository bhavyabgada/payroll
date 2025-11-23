"""Blueprint SQLX generator."""

from pathlib import Path
from typing import Optional

from jinja2 import Environment, FileSystemLoader

from dataform_blueprints.config import TableConfig, TableType


class BlueprintGenerator:
    """Generate Dataform SQLX files from table configurations.
    
    This generator creates Dataform-compatible SQLX files for different
    warehouse layers and table patterns.
    
    Attributes:
        config: Table configuration object
        template_env: Jinja2 environment for rendering templates
    """
    
    def __init__(self, config: TableConfig):
        """Initialize generator with configuration.
        
        Args:
            config: TableConfig object with table specification
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
    
    def _get_template_name(self) -> str:
        """Determine template file based on table type.
        
        Returns:
            Template filename
        """
        template_map = {
            TableType.SOURCE: "staging_table.sqlx.j2",
            TableType.DIMENSION: "dimension_table.sqlx.j2",
            TableType.FACT: "fact_table.sqlx.j2",
            TableType.AGGREGATE: "aggregate_table.sqlx.j2",
            TableType.VIEW: "staging_table.sqlx.j2",  # Reuse staging template
        }
        return template_map.get(self.config.table_type, "staging_table.sqlx.j2")
    
    def generate_sqlx(self) -> str:
        """Generate SQLX content from configuration.
        
        Returns:
            Generated SQLX string
        """
        template_name = self._get_template_name()
        template = self.template_env.get_template(template_name)
        
        sqlx_content = template.render(
            table_name=self.config.table_name,
            layer=self.config.layer,
            table_type=self.config.table_type,
            source_table=self.config.source_table or "${ref('source')}",
            columns=self.config.columns,
            partition_by=self.config.partition_by,
            cluster_by=self.config.cluster_by,
            primary_keys=self.config.primary_keys or [],
            description=self.config.description,
            tags=self.config.tags,
            incremental=self.config.incremental,
            dependencies=self.config.dependencies,
            dataset_id=self.config.dataset_id,
            assertions=self.config.assertions,
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
        
        print(f"✅ Generated {self.config.table_type} table: {output_file}")
    
    def validate_config(self) -> list:
        """Validate configuration and return any errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Validate table name
        if not self.config.table_name:
            errors.append("Table name is required")
        
        # Validate source table for non-raw layers
        if self.config.layer != "raw" and not self.config.source_table:
            errors.append("Source table is required for non-raw layers")
        
        # Validate columns
        if not self.config.columns:
            errors.append("At least one column is required")
        
        # Validate primary keys for dimensions and facts
        if self.config.table_type in [TableType.DIMENSION, TableType.FACT]:
            if not self.config.primary_keys:
                errors.append(f"{self.config.table_type} tables require primary keys")
        
        return errors
    
    @classmethod
    def from_yaml(cls, yaml_path: str) -> "BlueprintGenerator":
        """Create generator from YAML configuration file.
        
        Args:
            yaml_path: Path to YAML configuration file
        
        Returns:
            BlueprintGenerator instance
        """
        import yaml
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        config = TableConfig(**config_dict)
        return cls(config)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "BlueprintGenerator":
        """Create generator from configuration dictionary.
        
        Args:
            config_dict: Configuration dictionary
        
        Returns:
            BlueprintGenerator instance
        """
        config = TableConfig(**config_dict)
        return cls(config)

