# Airflow Orchestration

This directory contains Airflow DAGs for orchestrating the payroll data pipeline.

## Structure

```
airflow/
├── dags/
│   ├── payroll_ingestion.py      # GCS → BigQuery raw
│   ├── payroll_staging.py        # Raw → Staging + DQ gates
│   ├── payroll_warehouse.py      # Staging → Warehouse (SCD2 + facts)
│   ├── payroll_marts.py          # Warehouse → Marts
│   └── payroll_master_dag.py     # End-to-end orchestration
├── plugins/
│   ├── gcs_sensor.py             # Custom file arrival sensor
│   └── ge_operator.py            # Great Expectations operator
├── docker-compose.yml            # Local Airflow setup
└── Dockerfile                    # Custom Airflow image
```

## DAG Architecture

```
payroll_master_dag
├── ingestion_dag (external trigger)
│   └── GCS → raw_* tables
├── staging_dag (external trigger)
│   ├── raw → stg_* tables
│   └── GE checkpoints
├── warehouse_dag (external trigger)
│   ├── stg → dim_* + fact_* tables
│   └── SCD2 processing
└── marts_dag (external trigger)
    ├── warehouse → mart_* tables
    └── Reconciliation checks
```

## Local Development

```bash
# Start local Airflow
cd airflow
docker-compose up -d

# Access UI
open http://localhost:8080
# user: airflow, password: airflow
```

## Deployment

See `/project/docs/deployment.md` for production deployment guide.

