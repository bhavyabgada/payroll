"""
Payroll Analytics Main Pipeline DAG
Orchestrates the end-to-end data pipeline from landing to marts

Pipeline Flow:
1. Check for new data in GCS landing zone
2. Load raw data to BigQuery external tables
3. Run Dataform (staging → warehouse → marts)
4. Run data quality checks (Great Expectations)
5. Send notifications
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.google.cloud.operators.bigquery import BigQueryCheckOperator
from airflow.providers.google.cloud.sensors.gcs import GCSObjectExistenceSensor
from airflow.utils.task_group import TaskGroup


# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email': ['data-team@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(hours=2),
}

# DAG definition
dag = DAG(
    'payroll_main_pipeline',
    default_args=default_args,
    description='Main payroll analytics pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM UTC
    start_date=datetime(2025, 11, 1),
    catchup=False,
    tags=['payroll', 'dataform', 'production'],
    max_active_runs=1,
)

# Task 1: Check for new data in GCS
check_employees_data = GCSObjectExistenceSensor(
    task_id='check_employees_data',
    bucket='payroll-landing-dev',
    object='employees/*.csv',
    google_cloud_conn_id='google_cloud_default',
    timeout=600,
    poke_interval=60,
    mode='reschedule',
    dag=dag,
)

check_payroll_data = GCSObjectExistenceSensor(
    task_id='check_payroll_data',
    bucket='payroll-landing-dev',
    object='payroll_runs/*.csv',
    google_cloud_conn_id='google_cloud_default',
    timeout=600,
    poke_interval=60,
    mode='reschedule',
    dag=dag,
)

# Task 2: Run Dataform compilation
compile_dataform = BashOperator(
    task_id='compile_dataform',
    bash_command='cd {{ var.value.dataform_project_dir }} && dataform compile',
    dag=dag,
)

# Task Group: Run Dataform layers
with TaskGroup('run_dataform_layers', dag=dag) as run_dataform:
    
    run_staging = BashOperator(
        task_id='run_staging',
        bash_command='''
        cd {{ var.value.dataform_project_dir }} && \
        dataform run --tags=staging
        ''',
    )
    
    run_warehouse = BashOperator(
        task_id='run_warehouse',
        bash_command='''
        cd {{ var.value.dataform_project_dir }} && \
        dataform run --tags=warehouse
        ''',
    )
    
    run_marts = BashOperator(
        task_id='run_marts',
        bash_command='''
        cd {{ var.value.dataform_project_dir }} && \
        dataform run --tags=marts
        ''',
    )
    
    run_staging >> run_warehouse >> run_marts

# Task Group: Data Quality Checks
with TaskGroup('data_quality_checks', dag=dag) as data_quality:
    
    check_staging = BashOperator(
        task_id='check_staging',
        bash_command='''
        python {{ var.value.project_dir }}/scripts/run_data_quality_checks.py \
        --checkpoint staging_checkpoint
        ''',
    )
    
    check_warehouse = BashOperator(
        task_id='check_warehouse',
        bash_command='''
        python {{ var.value.project_dir }}/scripts/run_data_quality_checks.py \
        --checkpoint warehouse_checkpoint
        ''',
    )
    
    check_staging >> check_warehouse

# Task: Verify final row counts
verify_marts = BigQueryCheckOperator(
    task_id='verify_marts',
    sql='''
    SELECT COUNT(*) > 0 
    FROM `{{ var.value.gcp_project }}.payroll_marts.mart_payroll_summary_by_dept`
    ''',
    use_legacy_sql=False,
    dag=dag,
)

# Task: Archive processed files
archive_files = BashOperator(
    task_id='archive_files',
    bash_command='''
    gsutil -m mv \
    gs://payroll-landing-dev/employees/*.csv \
    gs://payroll-archive-dev/employees/{{ ds }}/
    ''',
    dag=dag,
)

# Task: Send success notification
def send_success_notification(**context):
    """Send success notification."""
    print(f"✅ Pipeline completed successfully for {context['ds']}")
    print(f"   Execution Time: {context['ti'].duration}")
    # TODO: Add Slack/email notification
    return "Success"

notify_success = PythonOperator(
    task_id='notify_success',
    python_callable=send_success_notification,
    provide_context=True,
    dag=dag,
)

# Define task dependencies
[check_employees_data, check_payroll_data] >> compile_dataform
compile_dataform >> run_dataform >> data_quality >> verify_marts
verify_marts >> archive_files >> notify_success

