"""Command-line interface for synthetic-payroll-lab."""

import sys
from pathlib import Path

import click
import yaml

from synthetic_payroll_lab import PayrollGenerator, ChaosConfig, __version__


@click.group()
@click.version_option(version=__version__)
def main():
    """Synthetic Payroll Lab - Generate realistic payroll test data."""
    pass


@main.command()
@click.option(
    '--config',
    type=click.Path(exists=True),
    help='Path to YAML configuration file'
)
@click.option(
    '--employees',
    type=int,
    default=50000,
    help='Number of employees to generate (default: 50000)'
)
@click.option(
    '--start-date',
    default='2024-01-01',
    help='Start date for data generation (YYYY-MM-DD)'
)
@click.option(
    '--end-date',
    default='2024-12-31',
    help='End date for data generation (YYYY-MM-DD)'
)
@click.option(
    '--output-dir',
    default='./landing',
    help='Output directory for generated files'
)
@click.option(
    '--format',
    type=click.Choice(['csv', 'json'], case_sensitive=False),
    default='csv',
    help='Output format (default: csv)'
)
@click.option(
    '--seed',
    type=int,
    help='Random seed for reproducibility'
)
@click.option(
    '--no-chaos',
    is_flag=True,
    help='Disable chaos pattern injection'
)
@click.option(
    '--duplicate-rate',
    type=float,
    default=0.02,
    help='Duplicate row injection rate (default: 0.02)'
)
@click.option(
    '--null-rate',
    type=float,
    default=0.01,
    help='Null value injection rate (default: 0.01)'
)
@click.option(
    '--late-arrival-pct',
    type=float,
    default=0.15,
    help='Late arrival percentage for timecards (default: 0.15)'
)
def generate(
    config,
    employees,
    start_date,
    end_date,
    output_dir,
    format,
    seed,
    no_chaos,
    duplicate_rate,
    null_rate,
    late_arrival_pct
):
    """Generate synthetic payroll data.
    
    Example:
        synthetic-payroll generate --employees 1000 --output-dir ./data
    """
    click.echo("=" * 60)
    click.echo("Synthetic Payroll Lab")
    click.echo(f"Version: {__version__}")
    click.echo("=" * 60)
    click.echo()
    
    # Load config file if provided
    if config:
        click.echo(f"📄 Loading configuration from: {config}")
        with open(config, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Override with config values
        employees = config_data.get('employees', {}).get('count', employees)
        start_date = config_data.get('start_date', start_date)
        end_date = config_data.get('end_date', end_date)
        output_format = config_data.get('output_format', format)
        
        # Chaos config from file
        chaos_config = config_data.get('chaos', {})
        duplicate_rate = chaos_config.get('duplicates', {}).get('rate', duplicate_rate)
        null_rate = chaos_config.get('nulls', {}).get('spike_rate', null_rate)
        late_arrival_pct = chaos_config.get('late_arrivals', {}).get('pct', late_arrival_pct)
    
    # Create chaos config
    chaos = None if no_chaos else ChaosConfig(
        duplicate_rate=duplicate_rate,
        null_spike_rate=null_rate,
        late_arrival_pct=late_arrival_pct
    )
    
    # Create generator
    try:
        generator = PayrollGenerator(
            employees=employees,
            start_date=start_date,
            end_date=end_date,
            chaos=chaos,
            seed=seed
        )
        
        # Generate data
        domains = generator.generate_all_domains(
            output_path=output_dir,
            format=format
        )
        
        # Summary
        click.echo()
        click.echo("=" * 60)
        click.echo("✅ Generation Complete!")
        click.echo("=" * 60)
        click.echo()
        click.echo(f"📊 Generated {len(domains)} domains:")
        total_rows = 0
        for domain_name, df in domains.items():
            click.echo(f"   • {domain_name}: {len(df):,} rows")
            total_rows += len(df)
        click.echo()
        click.echo(f"📁 Output: {output_dir}/")
        click.echo(f"📝 Total rows: {total_rows:,}")
        click.echo()
        
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@main.command()
def version():
    """Show version information."""
    click.echo(f"synthetic-payroll-lab version {__version__}")


if __name__ == '__main__':
    main()

