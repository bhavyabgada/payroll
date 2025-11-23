"""
Test Data Generation DAG
Uses synthetic-payroll-lab (Module A) to generate test data

Purpose: Generate realistic synthetic data for testing and development
Schedule: On-demand or daily for dev environment
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator


# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['data-team@company.com'],
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
}

# DAG definition
dag = DAG(
    'generate_test_data',
    default_args=default_args,
    description='Generate synthetic payroll test data using synthetic-payroll-lab',
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2025, 11, 1),
    catchup=False,
    tags=['testing', 'synthetic-data', 'development'],
)

# Task: Generate synthetic data
def generate_synthetic_data(**context):
    """Generate synthetic payroll data using Module A."""
    from synthetic_payroll_lab import PayrollGenerator
    from synthetic_payroll_lab.config import PayrollConfig, ChaosConfig
    from pathlib import Path
    import pandas as pd
    
    ds = context['ds']
    
    print("🏭 Generating synthetic payroll data...")
    
    # Configure generator
    payroll_config = PayrollConfig(
        num_employees=500,
        num_pay_periods=12,
        start_date="2025-01-01",
        end_date="2025-12-31"
    )
    
    chaos_config = ChaosConfig(
        duplicate_rate=0.02,
        null_rate=0.01,
        late_arrival_rate=0.05,
        schema_drift_rate=0.01,
        orphan_rate=0.01
    )
    
    # Generate data
    generator = PayrollGenerator(payroll_config, chaos_config)
    datasets = generator.generate_all()
    
    # Save to temporary location
    output_dir = Path(f"/tmp/synthetic_data_{ds}")
    output_dir.mkdir(exist_ok=True)
    
    for domain_name, df in datasets.items():
        output_file = output_dir / f"{domain_name}.csv"
        df.to_csv(output_file, index=False)
        print(f"   ✅ Generated {domain_name}: {len(df)} rows")
    
    print(f"📦 Data saved to: {output_dir}")
    
    return str(output_dir)

generate_data = PythonOperator(
    task_id='generate_data',
    python_callable=generate_synthetic_data,
    provide_context=True,
    dag=dag,
)

# Task: Upload to GCS landing zone
upload_to_gcs = BashOperator(
    task_id='upload_to_gcs',
    bash_command='''
    gsutil -m cp /tmp/synthetic_data_{{ ds }}/*.csv \
    gs://payroll-landing-dev/synthetic/{{ ds }}/
    
    echo "✅ Uploaded synthetic data to GCS"
    ''',
    dag=dag,
)

# Task: Load to BigQuery raw tables
load_to_bigquery = BashOperator(
    task_id='load_to_bigquery',
    bash_command='''
    # Load employees
    bq load --autodetect --replace \
    payroll_raw.raw_employees \
    gs://payroll-landing-dev/synthetic/{{ ds }}/employees.csv
    
    # Load jobs
    bq load --autodetect --replace \
    payroll_raw.raw_jobs \
    gs://payroll-landing-dev/synthetic/{{ ds }}/jobs.csv
    
    # Load payroll_runs
    bq load --autodetect --replace \
    payroll_raw.raw_payroll_runs \
    gs://payroll-landing-dev/synthetic/{{ ds }}/payroll_runs.csv
    
    echo "✅ Loaded data to BigQuery raw tables"
    ''',
    dag=dag,
)

# Task: Cleanup temp files
cleanup = BashOperator(
    task_id='cleanup',
    bash_command='rm -rf /tmp/synthetic_data_{{ ds }}',
    dag=dag,
)

# Task: Trigger main pipeline
trigger_pipeline = BashOperator(
    task_id='trigger_pipeline',
    bash_command='''
    airflow dags trigger payroll_main_pipeline \
    --exec-date {{ ds }}
    
    echo "✅ Triggered main pipeline"
    ''',
    dag=dag,
)

# Define task dependencies
generate_data >> upload_to_gcs >> load_to_bigquery >> cleanup >> trigger_pipeline

