#!/usr/bin/env python3
"""
FinOps Monitoring Script
Uses bq-finops-cli (Module D) for cost monitoring and optimization

Usage:
    python finops_monitoring.py --analyze
    python finops_monitoring.py --optimize
    python finops_monitoring.py --report
"""

import argparse
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

from bq_finops import CostAnalyzer, QueryOptimizer


def analyze_costs(project_id: str, days: int = 7) -> dict:
    """Analyze BigQuery costs for the past N days.
    
    Args:
        project_id: GCP project ID
        days: Number of days to analyze
    
    Returns:
        Cost analysis report
    """
    print(f"💰 Analyzing costs for past {days} days...")
    
    analyzer = CostAnalyzer(project_id=project_id)
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    report = analyzer.analyze_period(
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"\n{'='*60}")
    print(f"💰 COST ANALYSIS REPORT")
    print(f"{'='*60}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Total Cost: ${report.total_cost:,.2f}")
    print(f"Queries: {report.query_count:,}")
    print(f"Avg Cost per Query: ${report.avg_cost_per_query:.4f}")
    print(f"Bytes Processed: {report.bytes_processed:,}")
    
    # Cost by dataset
    if report.cost_by_dataset:
        print(f"\n📊 Cost by Dataset:")
        for dataset, cost in sorted(
            report.cost_by_dataset.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"   {dataset}: ${cost:.2f}")
    
    # Top expensive queries
    if report.top_cost_queries:
        print(f"\n🔥 Top 5 Expensive Queries:")
        for i, query in enumerate(report.top_cost_queries[:5], 1):
            print(f"   {i}. ${query['cost_usd']:.2f} - {query['user']}")
    
    return report.to_dict()


def optimize_tables(project_id: str) -> dict:
    """Generate optimization recommendations for tables.
    
    Args:
        project_id: GCP project ID
    
    Returns:
        Optimization recommendations
    """
    print(f"🔧 Generating optimization recommendations...")
    
    optimizer = QueryOptimizer(project_id=project_id)
    
    tables_to_check = [
        ("payroll_staging", "stg_employees"),
        ("payroll_staging", "stg_payroll_runs"),
        ("payroll_warehouse", "dim_employee"),
        ("payroll_warehouse", "fact_payroll_run"),
        ("payroll_marts", "mart_payroll_summary_by_dept"),
    ]
    
    all_recommendations = {}
    
    for dataset_id, table_id in tables_to_check:
        print(f"\n📋 Checking {dataset_id}.{table_id}...")
        
        try:
            report = optimizer.generate_optimization_report(dataset_id, table_id)
            
            if report.get("recommendations"):
                print(f"   ⚠️  {len(report['recommendations'])} recommendation(s)")
                all_recommendations[f"{dataset_id}.{table_id}"] = report["recommendations"]
                
                for rec in report["recommendations"]:
                    print(f"      - [{rec['priority'].upper()}] {rec['action']}")
                    print(f"        Benefit: {rec['benefit']}")
            else:
                print(f"   ✅ Already optimized")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return all_recommendations


def generate_finops_report(project_id: str, output_dir: str = "reports"):
    """Generate comprehensive FinOps report.
    
    Args:
        project_id: GCP project ID
        output_dir: Output directory for reports
    """
    print(f"📊 Generating FinOps Report...")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Analyze costs
    cost_report = analyze_costs(project_id, days=7)
    
    # Save cost report
    cost_file = output_path / f"cost_report_{timestamp}.json"
    with open(cost_file, "w") as f:
        json.dump(cost_report, f, indent=2)
    print(f"\n✅ Cost report saved: {cost_file}")
    
    # 2. Optimization recommendations
    optimization_report = optimize_tables(project_id)
    
    # Save optimization report
    opt_file = output_path / f"optimization_report_{timestamp}.json"
    with open(opt_file, "w") as f:
        json.dump(optimization_report, f, indent=2)
    print(f"✅ Optimization report saved: {opt_file}")
    
    # 3. Generate summary
    summary = {
        "generated_at": timestamp,
        "project_id": project_id,
        "cost_analysis": {
            "total_cost": cost_report["total_cost"],
            "query_count": cost_report["query_count"],
            "avg_cost_per_query": cost_report["avg_cost_per_query"]
        },
        "optimization": {
            "tables_checked": len(optimization_report),
            "tables_needing_optimization": sum(
                1 for recs in optimization_report.values() if recs
            )
        }
    }
    
    summary_file = output_path / f"finops_summary_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"✅ Summary saved: {summary_file}")
    
    # 4. Check budget
    WEEKLY_BUDGET = 350.0
    if cost_report["total_cost"] > WEEKLY_BUDGET:
        print(f"\n⚠️  WARNING: Over budget!")
        print(f"   Budget: ${WEEKLY_BUDGET:.2f}")
        print(f"   Actual: ${cost_report['total_cost']:.2f}")
        print(f"   Overage: ${cost_report['total_cost'] - WEEKLY_BUDGET:.2f}")
    else:
        print(f"\n✅ Within budget")
        print(f"   Budget: ${WEEKLY_BUDGET:.2f}")
        print(f"   Actual: ${cost_report['total_cost']:.2f}")
        print(f"   Remaining: ${WEEKLY_BUDGET - cost_report['total_cost']:.2f}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="FinOps monitoring for Payroll Analytics")
    parser.add_argument(
        "--project-id",
        default="payroll-analytics-dev",
        help="GCP project ID"
    )
    parser.add_argument(
        "--analyze",
        action="store_true",
        help="Analyze costs"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Generate optimization recommendations"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate full FinOps report"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to analyze (default: 7)"
    )
    
    args = parser.parse_args()
    
    if args.report or (not args.analyze and not args.optimize):
        # Default: generate full report
        generate_finops_report(args.project_id)
    else:
        if args.analyze:
            analyze_costs(args.project_id, args.days)
        
        if args.optimize:
            optimize_tables(args.project_id)


if __name__ == "__main__":
    main()

