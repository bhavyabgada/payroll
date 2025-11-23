"""Command-line interface for Dataform Blueprints."""

import sys
from pathlib import Path
from typing import Optional

import click
import yaml

from dataform_blueprints import __version__
from dataform_blueprints.config import TableConfig, LayerType, TableType
from dataform_blueprints.generator import BlueprintGenerator


@click.group()
@click.version_option(version=__version__, prog_name="dataform-blueprints")
def cli():
    """Dataform Warehouse Blueprints - SQLX templates for warehouse patterns.
    
    Generate production-ready Dataform SQLX files from simple YAML configurations.
    """
    pass


@cli.command()
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="table_config.yaml",
    help="Output YAML file path"
)
@click.option(
    "--table-name",
    "-t",
    required=True,
    help="Table name (e.g., dim_employee)"
)
@click.option(
    "--layer",
    "-l",
    type=click.Choice(["raw", "staging", "warehouse", "marts"]),
    required=True,
    help="Warehouse layer"
)
@click.option(
    "--table-type",
    type=click.Choice(["source", "dimension", "fact", "aggregate", "view"]),
    required=True,
    help="Table pattern type"
)
def init(output: str, table_name: str, layer: str, table_type: str):
    """Initialize a new table configuration YAML file.
    
    Example:
        dataform-blueprints init -t dim_employee -l warehouse --table-type dimension
    """
    # Create a sample configuration
    config_data = {
        "table_name": table_name,
        "layer": layer,
        "table_type": table_type,
        "source_table": "${ref('stg_source')}",
        "columns": [
            "column_1",
            "column_2",
            "column_3"
        ],
        "partition_by": "updated_at",
        "cluster_by": ["id"],
        "primary_keys": ["id"],
        "description": f"{table_name} table",
        "tags": [layer, table_type],
        "incremental": True,
        "dataset_id": layer,
        "dependencies": []
    }
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Created configuration file: {output_path}")
    click.echo(f"📝 Edit this file and run: dataform-blueprints generate -c {output_path}")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="YAML configuration file"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output SQLX file path (defaults to definitions/<table_name>.sqlx)"
)
@click.option(
    "--validate-only",
    is_flag=True,
    help="Only validate configuration without generating"
)
def generate(config: str, output: Optional[str], validate_only: bool):
    """Generate SQLX file from configuration.
    
    Example:
        dataform-blueprints generate -c dim_employee.yaml -o definitions/dim_employee.sqlx
    """
    try:
        # Load configuration
        with open(config, "r", encoding="utf-8") as f:
            config_dict = yaml.safe_load(f)
        
        # Create generator
        table_config = TableConfig(**config_dict)
        generator = BlueprintGenerator(table_config)
        
        # Validate configuration
        errors = generator.validate_config()
        if errors:
            click.echo("❌ Configuration validation failed:", err=True)
            for error in errors:
                click.echo(f"   - {error}", err=True)
            sys.exit(1)
        
        click.echo("✅ Configuration validated successfully")
        
        if validate_only:
            click.echo("📋 Configuration summary:")
            click.echo(f"   Table: {table_config.table_name}")
            click.echo(f"   Layer: {table_config.layer}")
            click.echo(f"   Type: {table_config.table_type}")
            click.echo(f"   Columns: {len(table_config.columns)}")
            return
        
        # Generate SQLX
        sqlx_content = generator.generate_sqlx()
        
        # Determine output path
        if not output:
            output = f"definitions/{table_config.table_name}.sqlx"
        
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write SQLX file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(sqlx_content)
        
        click.echo(f"✅ Generated SQLX file: {output_path}")
        click.echo(f"📊 Table: {table_config.table_name}")
        click.echo(f"🏗️  Type: {table_config.table_type}")
        click.echo(f"📦 Layer: {table_config.layer}")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--directory",
    "-d",
    type=click.Path(exists=True),
    required=True,
    help="Directory containing YAML config files"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="definitions",
    help="Output directory for SQLX files"
)
def batch(directory: str, output_dir: str):
    """Generate SQLX files from multiple configuration files.
    
    Example:
        dataform-blueprints batch -d configs/ -o definitions/
    """
    config_dir = Path(directory)
    output_path = Path(output_dir)
    
    # Find all YAML files
    yaml_files = list(config_dir.glob("*.yaml")) + list(config_dir.glob("*.yml"))
    
    if not yaml_files:
        click.echo(f"⚠️  No YAML files found in {config_dir}")
        return
    
    click.echo(f"📂 Found {len(yaml_files)} configuration file(s)")
    
    success_count = 0
    error_count = 0
    
    for yaml_file in yaml_files:
        try:
            click.echo(f"\n🔄 Processing: {yaml_file.name}")
            
            # Load and generate
            with open(yaml_file, "r", encoding="utf-8") as f:
                config_dict = yaml.safe_load(f)
            
            table_config = TableConfig(**config_dict)
            generator = BlueprintGenerator(table_config)
            
            # Validate
            errors = generator.validate_config()
            if errors:
                click.echo(f"   ❌ Validation failed:")
                for error in errors:
                    click.echo(f"      - {error}")
                error_count += 1
                continue
            
            # Generate
            sqlx_file = output_path / f"{table_config.table_name}.sqlx"
            generator.write_sqlx(str(sqlx_file))
            
            success_count += 1
            
        except Exception as e:
            click.echo(f"   ❌ Error: {str(e)}")
            error_count += 1
    
    # Summary
    click.echo(f"\n{'='*50}")
    click.echo(f"✅ Successfully generated: {success_count}")
    click.echo(f"❌ Failed: {error_count}")
    click.echo(f"📊 Total: {len(yaml_files)}")


@cli.command()
def examples():
    """Show example configurations for different table types."""
    
    examples_text = """
🔷 DIMENSION TABLE (SCD Type 1)
─────────────────────────────────────
table_name: dim_employee
layer: warehouse
table_type: dimension
source_table: ${ref('stg_employees')}
columns:
  - employee_id
  - first_name
  - last_name
  - email
  - hire_date
partition_by: updated_at
cluster_by: [employee_id]
primary_keys: [employee_id]
incremental: true
tags: [dimension, hr]

🔶 FACT TABLE
─────────────────────────────────────
table_name: fact_payroll_run
layer: warehouse
table_type: fact
source_table: ${ref('stg_payroll')}
columns:
  - payroll_id
  - employee_id
  - pay_period_id
  - gross_pay
  - net_pay
  - tax_amount
partition_by: pay_date
cluster_by: [employee_id, pay_date]
primary_keys: [payroll_id]
incremental: true
tags: [fact, payroll]

🔸 AGGREGATE/MART TABLE
─────────────────────────────────────
table_name: mart_payroll_summary
layer: marts
table_type: aggregate
source_table: ${ref('fact_payroll_run')}
columns:
  - pay_period
  - department
  - SUM(gross_pay) as total_gross_pay
  - COUNT(DISTINCT employee_id) as employee_count
primary_keys: [pay_period, department]
tags: [mart, summary]

📝 Generate with:
   dataform-blueprints init -t <table_name> -l <layer> --table-type <type>
   dataform-blueprints generate -c <config.yaml>
"""
    
    click.echo(examples_text)


if __name__ == "__main__":
    cli()

