"""Command-line interface for scd2-bq-engine."""

import sys
from pathlib import Path

import click
import yaml

from scd2_bq_engine import SCD2Generator, __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """SCD2 BigQuery Engine - Generate SCD Type 2 dimensions for BigQuery."""
    pass


@main.command()
@click.option(
    '--config',
    type=click.Path(exists=True),
    required=True,
    help='Path to YAML configuration file'
)
@click.option(
    '--output-file',
    type=click.Path(),
    required=True,
    help='Output SQLX file path'
)
@click.option(
    '--validate-only',
    is_flag=True,
    help='Only validate configuration without generating'
)
def generate(config, output_file, validate_only):
    """Generate SCD Type 2 dimension SQLX file.
    
    Example:
        scd2-bq generate --config dim_employee.yaml --output-file dim_employee.sqlx
    """
    click.echo("=" * 60)
    click.echo("SCD2 BigQuery Engine")
    click.echo(f"Version: {__version__}")
    click.echo("=" * 60)
    click.echo()
    
    try:
        # Load configuration
        click.echo(f"📄 Loading configuration: {config}")
        generator = SCD2Generator.from_yaml(config)
        
        # Validate configuration
        click.echo("🔍 Validating configuration...")
        errors = generator.validate_config()
        
        if errors:
            click.echo("❌ Configuration validation failed:", err=True)
            for error in errors:
                click.echo(f"   • {error}", err=True)
            sys.exit(1)
        
        click.echo("✅ Configuration valid")
        
        if validate_only:
            click.echo()
            click.echo("✅ Validation complete (--validate-only mode)")
            return
        
        # Generate SQLX
        click.echo()
        click.echo(f"🔧 Generating SCD2 dimension...")
        click.echo(f"   Dimension: {generator.config.dimension_name}")
        click.echo(f"   Source: {generator.config.source_table}")
        click.echo(f"   Business Keys: {', '.join(generator.config.business_keys)}")
        click.echo(f"   Tracked Columns: {len(generator.config.tracked_columns)} columns")
        click.echo(f"   Hash Algorithm: {generator.config.hash_algorithm.upper()}")
        
        generator.write_sqlx(output_file)
        
        # Success summary
        click.echo()
        click.echo("=" * 60)
        click.echo("✅ Generation Complete!")
        click.echo("=" * 60)
        click.echo()
        click.echo(f"📁 Output: {output_file}")
        click.echo(f"📊 Dimension: {generator.config.dimension_name}")
        click.echo()
        click.echo("💡 Next steps:")
        click.echo("   1. Review generated SQLX file")
        click.echo("   2. Copy to your Dataform project's definitions/ folder")
        click.echo("   3. Run: dataform compile")
        click.echo()
        
    except FileNotFoundError as e:
        click.echo(f"❌ Error: File not found - {e}", err=True)
        sys.exit(1)
    except yaml.YAMLError as e:
        click.echo(f"❌ Error: Invalid YAML - {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument('dimension_name')
@click.option(
    '--source-table',
    required=True,
    help='Fully qualified source table name'
)
@click.option(
    '--business-keys',
    required=True,
    help='Comma-separated list of business key columns'
)
@click.option(
    '--tracked-columns',
    required=True,
    help='Comma-separated list of columns to track'
)
@click.option(
    '--output-file',
    type=click.Path(),
    help='Output YAML config file path (default: <dimension_name>_config.yaml)'
)
def init(dimension_name, source_table, business_keys, tracked_columns, output_file):
    """Initialize a new SCD2 configuration file.
    
    Example:
        scd2-bq init dim_employee \\
            --source-table project.dataset.stg_employees \\
            --business-keys employee_number \\
            --tracked-columns first_name,last_name,job_code
    """
    click.echo("=" * 60)
    click.echo("Initialize SCD2 Configuration")
    click.echo("=" * 60)
    click.echo()
    
    # Parse comma-separated lists
    business_keys_list = [k.strip() for k in business_keys.split(',')]
    tracked_columns_list = [c.strip() for c in tracked_columns.split(',')]
    
    # Create configuration dictionary
    config = {
        "dimension_name": dimension_name,
        "source_table": source_table,
        "business_keys": business_keys_list,
        "tracked_columns": tracked_columns_list,
        "meta_columns": [],
        "hash_algorithm": "md5",
        "surrogate_key_name": "dimension_key",
        "effective_from_col": "effective_from",
        "effective_to_col": "effective_to",
        "is_current_col": "is_current",
        "hash_col": "row_hash",
        "handle_late_arrivals": True,
        "soft_delete": True,
        "partition_by": "effective_from",
        "cluster_by": business_keys_list + ["is_current"]
    }
    
    # Determine output file
    if not output_file:
        output_file = f"{dimension_name}_config.yaml"
    
    # Write configuration
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Created configuration: {output_file}")
    click.echo()
    click.echo("📝 Configuration summary:")
    click.echo(f"   Dimension: {dimension_name}")
    click.echo(f"   Source: {source_table}")
    click.echo(f"   Business Keys: {', '.join(business_keys_list)}")
    click.echo(f"   Tracked Columns: {', '.join(tracked_columns_list)}")
    click.echo()
    click.echo("💡 Next steps:")
    click.echo(f"   1. Review and edit {output_file}")
    click.echo("   2. Run: scd2-bq generate --config <file> --output-file <output>.sqlx")
    click.echo()


@main.command()
def version():
    """Show version information."""
    click.echo(f"scd2-bq-engine version {__version__}")


if __name__ == '__main__':
    main()

