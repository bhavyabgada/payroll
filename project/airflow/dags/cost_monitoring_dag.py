"""
Cost Monitoring DAG
Uses bq-finops-cli (Module D) to monitor BigQuery costs

Schedule: Weekly on Monday mornings
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.task_group import TaskGroup


# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'cost_monitoring_weekly',
    default_args=default_args,
    description='Weekly BigQuery cost monitoring using bq-finops-cli',
    schedule_interval='0 8 * * MON',  # Every Monday at 8 AM
    start_date=datetime(2025, 11, 1),
    catchup=False,
    tags=['finops', 'monitoring', 'cost'],
)

# Task: Analyze costs for the past week
analyze_weekly_costs = BashOperator(
    task_id='analyze_weekly_costs',
    bash_command='''
    bq-finops analyze costs \
      -p {{ var.value.gcp_project }} \
      --start-date {{ macros.ds_add(ds, -7) }} \
      --end-date {{ ds }} \
      --format json > /tmp/weekly_costs_{{ ds }}.json
    ''',
    dag=dag,
)

# Task: Analyze each dataset
with TaskGroup('analyze_datasets', dag=dag) as analyze_datasets:
    
    analyze_staging = BashOperator(
        task_id='analyze_staging',
        bash_command='''
        bq-finops analyze costs \
          -p {{ var.value.gcp_project }} \
          -d payroll_staging \
          --format json > /tmp/staging_costs_{{ ds }}.json
        ''',
    )
    
    analyze_warehouse = BashOperator(
        task_id='analyze_warehouse',
        bash_command='''
        bq-finops analyze costs \
          -p {{ var.value.gcp_project }} \
          -d payroll_warehouse \
          --format json > /tmp/warehouse_costs_{{ ds }}.json
        ''',
    )
    
    analyze_marts = BashOperator(
        task_id='analyze_marts',
        bash_command='''
        bq-finops analyze costs \
          -p {{ var.value.gcp_project }} \
          -d payroll_marts \
          --format json > /tmp/marts_costs_{{ ds }}.json
        ''',
    )

# Task: Generate optimization reports for key tables
with TaskGroup('optimization_reports', dag=dag) as optimization_reports:
    
    optimize_dim_employee = BashOperator(
        task_id='optimize_dim_employee',
        bash_command='''
        bq-finops optimize report \
          -p {{ var.value.gcp_project }} \
          -d payroll_warehouse \
          -t dim_employee > /tmp/optimize_dim_employee_{{ ds }}.txt
        ''',
    )
    
    optimize_fact_payroll = BashOperator(
        task_id='optimize_fact_payroll',
        bash_command='''
        bq-finops optimize report \
          -p {{ var.value.gcp_project }} \
          -d payroll_warehouse \
          -t fact_payroll_run > /tmp/optimize_fact_payroll_{{ ds }}.txt
        ''',
    )

# Task: Process and send cost report
def process_cost_report(**context):
    """Process cost data and send report."""
    import json
    from pathlib import Path
    
    ds = context['ds']
    
    # Load cost data
    costs_file = Path(f"/tmp/weekly_costs_{ds}.json")
    if costs_file.exists():
        with open(costs_file) as f:
            costs = json.load(f)
        
        total_cost = costs.get('total_cost', 0)
        query_count = costs.get('query_count', 0)
        
        print(f"📊 Weekly Cost Report ({ds})")
        print(f"   Total Cost: ${total_cost:.2f}")
        print(f"   Queries: {query_count:,}")
        print(f"   Avg per Query: ${costs.get('avg_cost_per_query', 0):.4f}")
        
        # Check budget alert
        WEEKLY_BUDGET = 350.0  # $50/day * 7 days
        if total_cost > WEEKLY_BUDGET:
            print(f"   ⚠️  WARNING: Over budget by ${total_cost - WEEKLY_BUDGET:.2f}")
            # TODO: Send alert
        else:
            print(f"   ✅ Within budget (${WEEKLY_BUDGET - total_cost:.2f} remaining)")
    
    return "Report generated"

send_cost_report = PythonOperator(
    task_id='send_cost_report',
    python_callable=process_cost_report,
    provide_context=True,
    dag=dag,
)

# Task: Archive reports to GCS
archive_reports = BashOperator(
    task_id='archive_reports',
    bash_command='''
    gsutil cp /tmp/*_costs_{{ ds }}.json \
    gs://payroll-archive-dev/cost_reports/{{ ds }}/
    
    gsutil cp /tmp/optimize_*_{{ ds }}.txt \
    gs://payroll-archive-dev/optimization_reports/{{ ds }}/
    ''',
    dag=dag,
)

# Define task dependencies
analyze_weekly_costs >> analyze_datasets
analyze_datasets >> optimization_reports
optimization_reports >> send_cost_report >> archive_reports

