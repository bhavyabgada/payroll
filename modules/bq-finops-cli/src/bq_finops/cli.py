"""Command-line interface for BQ FinOps."""

import sys
import json
from typing import Optional

import click
from tabulate import tabulate

from bq_finops import __version__
from bq_finops.analyzer import CostAnalyzer
from bq_finops.optimizer import QueryOptimizer
from bq_finops.config import AnalysisConfig, OptimizationConfig


@click.group()
@click.version_option(version=__version__, prog_name="bq-finops")
def cli():
    """BQ FinOps CLI - BigQuery cost monitoring and optimization toolkit.
    
    Monitor costs, analyze usage, and optimize BigQuery resources.
    """
    pass


@cli.group()
def analyze():
    """Analyze BigQuery costs and usage patterns."""
    pass


@cli.group()
def optimize():
    """Optimize BigQuery tables and queries."""
    pass


@analyze.command()
@click.option(
    "--project-id",
    "-p",
    required=True,
    help="GCP project ID"
)
@click.option(
    "--start-date",
    "-s",
    help="Start date (YYYY-MM-DD), default: 30 days ago"
)
@click.option(
    "--end-date",
    "-e",
    help="End date (YYYY-MM-DD), default: today"
)
@click.option(
    "--datasets",
    "-d",
    multiple=True,
    help="Datasets to analyze (can specify multiple)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format"
)
def costs(project_id: str, start_date: Optional[str], end_date: Optional[str], 
          datasets: tuple, format: str):
    """Analyze costs for a time period.
    
    Example:
        bq-finops analyze costs -p my-project --start-date 2025-01-01
    """
    try:
        analyzer = CostAnalyzer(project_id=project_id)
        
        dataset_list = list(datasets) if datasets else None
        
        click.echo(f"🔍 Analyzing costs for {project_id}...")
        if start_date:
            click.echo(f"   Period: {start_date} to {end_date or 'today'}")
        if dataset_list:
            click.echo(f"   Datasets: {', '.join(dataset_list)}")
        
        report = analyzer.analyze_period(
            start_date=start_date,
            end_date=end_date,
            datasets=dataset_list
        )
        
        if format == "json":
            click.echo(json.dumps(report.to_dict(), indent=2))
        else:
            # Table format
            click.echo("\n" + "=" * 60)
            click.echo("💰 COST SUMMARY")
            click.echo("=" * 60)
            
            summary = [
                ["Total Cost (USD)", f"${report.total_cost:,.2f}"],
                ["Query Count", f"{report.query_count:,}"],
                ["Avg Cost per Query", f"${report.avg_cost_per_query:.4f}"],
                ["Total Bytes Processed", f"{report.bytes_processed:,}"],
            ]
            click.echo(tabulate(summary, tablefmt="simple"))
            
            # Top cost queries
            if report.top_cost_queries:
                click.echo("\n" + "=" * 60)
                click.echo("🔥 TOP EXPENSIVE QUERIES")
                click.echo("=" * 60)
                
                query_table = [
                    [
                        q["job_id"][:20] + "...",
                        q["user"][:30],
                        f"${q['cost_usd']:.4f}",
                        f"{q['bytes_processed']:,}"
                    ]
                    for q in report.top_cost_queries[:5]
                ]
                click.echo(tabulate(
                    query_table,
                    headers=["Job ID", "User", "Cost", "Bytes"],
                    tablefmt="grid"
                ))
            
            # Cost by dataset
            if report.cost_by_dataset:
                click.echo("\n" + "=" * 60)
                click.echo("📊 COST BY DATASET")
                click.echo("=" * 60)
                
                dataset_table = [
                    [dataset, f"${cost:.2f}"]
                    for dataset, cost in sorted(
                        report.cost_by_dataset.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ]
                click.echo(tabulate(
                    dataset_table,
                    headers=["Dataset", "Cost (USD)"],
                    tablefmt="grid"
                ))
            
            # Cost by user
            if report.cost_by_user:
                click.echo("\n" + "=" * 60)
                click.echo("👥 COST BY USER")
                click.echo("=" * 60)
                
                user_table = [
                    [user[:40], f"${cost:.2f}"]
                    for user, cost in sorted(
                        report.cost_by_user.items(),
                        key=lambda x: x[1],
                        reverse=True
                    )[:10]
                ]
                click.echo(tabulate(
                    user_table,
                    headers=["User", "Cost (USD)"],
                    tablefmt="grid"
                ))
        
        click.echo(f"\n✅ Analysis complete!")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@analyze.command()
@click.option(
    "--project-id",
    "-p",
    required=True,
    help="GCP project ID"
)
@click.option(
    "--dataset-id",
    "-d",
    required=True,
    help="Dataset ID"
)
@click.option(
    "--table-id",
    "-t",
    required=True,
    help="Table ID"
)
def table(project_id: str, dataset_id: str, table_id: str):
    """Analyze a specific table.
    
    Example:
        bq-finops analyze table -p my-project -d warehouse -t fact_sales
    """
    try:
        analyzer = CostAnalyzer(project_id=project_id)
        
        click.echo(f"🔍 Analyzing table {project_id}.{dataset_id}.{table_id}...")
        
        analysis = analyzer.analyze_table(dataset_id, table_id)
        
        # Display results
        click.echo("\n" + "=" * 60)
        click.echo("📋 TABLE INFORMATION")
        click.echo("=" * 60)
        
        info = [
            ["Table", analysis["table"]],
            ["Rows", f"{analysis['num_rows']:,}"],
            ["Size (GB)", f"{analysis['size_gb']:.2f}"],
            ["Created", analysis["created"]],
            ["Modified", analysis["modified"]],
        ]
        click.echo(tabulate(info, tablefmt="simple"))
        
        # Partitioning
        click.echo("\n" + "=" * 60)
        click.echo("🗂️  PARTITIONING")
        click.echo("=" * 60)
        
        if analysis["partitioning"]:
            part = analysis["partitioning"]
            part_info = [
                ["Status", "✅ Partitioned"],
                ["Type", part["type"]],
                ["Field", part["field"] or "N/A"],
            ]
            click.echo(tabulate(part_info, tablefmt="simple"))
        else:
            click.echo("❌ Not partitioned")
        
        # Clustering
        click.echo("\n" + "=" * 60)
        click.echo("🔗 CLUSTERING")
        click.echo("=" * 60)
        
        if analysis["clustering"]:
            click.echo(f"✅ Clustered by: {', '.join(analysis['clustering'])}")
        else:
            click.echo("❌ Not clustered")
        
        # Recommendations
        if analysis["recommendations"]:
            click.echo("\n" + "=" * 60)
            click.echo("💡 RECOMMENDATIONS")
            click.echo("=" * 60)
            
            for i, rec in enumerate(analysis["recommendations"], 1):
                click.echo(f"\n{i}. [{rec['priority'].upper()}] {rec['type']}")
                click.echo(f"   {rec['message']}")
        
        click.echo(f"\n✅ Analysis complete!")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@optimize.command()
@click.option(
    "--project-id",
    "-p",
    required=True,
    help="GCP project ID"
)
@click.option(
    "--dataset-id",
    "-d",
    required=True,
    help="Dataset ID"
)
@click.option(
    "--table-id",
    "-t",
    required=True,
    help="Table ID"
)
def report(project_id: str, dataset_id: str, table_id: str):
    """Generate optimization report for a table.
    
    Example:
        bq-finops optimize report -p my-project -d warehouse -t fact_sales
    """
    try:
        optimizer = QueryOptimizer(project_id=project_id)
        
        click.echo(f"🔍 Generating optimization report for {project_id}.{dataset_id}.{table_id}...")
        
        report = optimizer.generate_optimization_report(dataset_id, table_id)
        
        if "error" in report:
            click.echo(f"❌ Error: {report['error']}", err=True)
            sys.exit(1)
        
        # Display current state
        click.echo("\n" + "=" * 60)
        click.echo("📋 CURRENT STATE")
        click.echo("=" * 60)
        
        state = report["current_state"]
        state_info = [
            ["Table", report["table"]],
            ["Size (GB)", f"{state['size_gb']:.2f}"],
            ["Partitioned", "✅" if state.get("partitioned") else "❌"],
            ["Clustered", "✅" if state.get("clustered") else "❌"],
        ]
        
        if state.get("partitioned"):
            state_info.append(["Partition Field", state.get("partition_field", "N/A")])
        
        if state.get("clustered"):
            state_info.append(["Cluster Fields", ", ".join(state.get("cluster_fields", []))])
        
        click.echo(tabulate(state_info, tablefmt="simple"))
        
        # Display recommendations
        if report["recommendations"]:
            click.echo("\n" + "=" * 60)
            click.echo("💡 OPTIMIZATION RECOMMENDATIONS")
            click.echo("=" * 60)
            
            for i, rec in enumerate(report["recommendations"], 1):
                click.echo(f"\n{i}. [{rec['priority'].upper()}] {rec['action']}")
                click.echo(f"   Benefit: {rec['benefit']}")
                if "sql" in rec and rec["sql"]:
                    click.echo(f"\n   SQL:\n{rec['sql']}\n")
        else:
            click.echo("\n✅ Table is already optimized!")
        
        click.echo(f"\n✅ Report complete!")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@optimize.command()
@click.option(
    "--project-id",
    "-p",
    required=True,
    help="GCP project ID"
)
@click.option(
    "--dataset-id",
    "-d",
    required=True,
    help="Dataset ID"
)
@click.option(
    "--table-id",
    "-t",
    required=True,
    help="Table ID"
)
@click.option(
    "--partition-column",
    help="Column to partition by"
)
@click.option(
    "--cluster-columns",
    multiple=True,
    help="Columns to cluster by (can specify multiple)"
)
def generate_ddl(project_id: str, dataset_id: str, table_id: str,
                 partition_column: Optional[str], cluster_columns: tuple):
    """Generate optimization DDL for a table.
    
    Example:
        bq-finops optimize generate-ddl -p my-project -d warehouse -t fact_sales \\
            --partition-column sale_date --cluster-columns customer_id --cluster-columns product_id
    """
    try:
        optimizer = QueryOptimizer(project_id=project_id)
        
        if partition_column and cluster_columns:
            click.echo("📝 Generating DDL with partitioning AND clustering...")
            ddl = optimizer.generate_cluster_ddl(
                dataset_id,
                table_id,
                list(cluster_columns),
                partition_column
            )
        elif partition_column:
            click.echo("📝 Generating DDL with partitioning...")
            ddl = optimizer.generate_partition_ddl(
                dataset_id,
                table_id,
                partition_column
            )
        elif cluster_columns:
            click.echo("📝 Generating DDL with clustering...")
            ddl = optimizer.generate_cluster_ddl(
                dataset_id,
                table_id,
                list(cluster_columns)
            )
        else:
            click.echo("❌ Error: Must specify --partition-column or --cluster-columns", err=True)
            sys.exit(1)
        
        click.echo("\n" + "=" * 60)
        click.echo("📄 GENERATED DDL")
        click.echo("=" * 60)
        click.echo(ddl)
        click.echo("=" * 60)
        
        click.echo("\n✅ DDL generated successfully!")
        click.echo("⚠️  Review the DDL before executing in BigQuery")
        
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def examples():
    """Show example commands."""
    
    examples_text = """
🔷 ANALYZE COSTS
─────────────────────────────────────
# Analyze costs for the last 30 days
bq-finops analyze costs -p my-gcp-project

# Analyze specific date range
bq-finops analyze costs -p my-project \\
  --start-date 2025-01-01 \\
  --end-date 2025-01-31

# Analyze specific datasets
bq-finops analyze costs -p my-project \\
  -d warehouse -d marts

# Output as JSON
bq-finops analyze costs -p my-project --format json

🔶 ANALYZE TABLE
─────────────────────────────────────
# Analyze a specific table
bq-finops analyze table -p my-project \\
  -d warehouse -t fact_sales

🔸 OPTIMIZE TABLE
─────────────────────────────────────
# Generate optimization report
bq-finops optimize report -p my-project \\
  -d warehouse -t fact_sales

# Generate DDL with partitioning
bq-finops optimize generate-ddl -p my-project \\
  -d warehouse -t fact_sales \\
  --partition-column sale_date

# Generate DDL with clustering
bq-finops optimize generate-ddl -p my-project \\
  -d warehouse -t fact_sales \\
  --cluster-columns customer_id \\
  --cluster-columns product_id

# Generate DDL with both
bq-finops optimize generate-ddl -p my-project \\
  -d warehouse -t fact_sales \\
  --partition-column sale_date \\
  --cluster-columns customer_id \\
  --cluster-columns product_id
"""
    
    click.echo(examples_text)


if __name__ == "__main__":
    cli()

