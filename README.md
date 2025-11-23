I'll create a comprehensive technical design specification for this enterprise payroll modernization platform. This is a planning-only session - no code will be generated.

---

# **TECHNICAL DESIGN SPECIFICATION**
## Enterprise Payroll Lakehouse → Warehouse Modernization on GCP

---

## **0. EXECUTIVE CONTEXT**

This is a Fortune-500 scale data modernization initiative that will serve as both:
1. A production-grade enterprise payroll analytics platform
2. A portfolio showcase demonstrating OSS contribution + enterprise architecture maturity

**Strategic Approach**: Extract reusable OSS modules first, then compose the enterprise project from those modules. This proves deep engineering thinking and maximizes career/community impact.

---

## **1. PROJECT TITLE**

**"Enterprise Payroll Lakehouse → Warehouse Modernization on GCP with DataOps, FinOps, and Privacy-Safe Analytics"**

**Shorthand**: `payroll-lakehouse-gcp`

---

## **2. PROBLEM STATEMENT DECOMPOSITION**

### **2.1 Current State Architecture (Legacy)**

**Systems of Record**:
- Oracle HR/Payroll (monolithic ERP)
- Regional timekeeping exports (Kronos/ADP-like)
- Manual CSV/JSON file drops to SFTP
- Legacy EDW (Oracle/Teradata) with 48-72 hour latency

**Data Flow Today**:
```
Oracle HR → nightly export → SFTP → manual ETL scripts → staging tables → 
legacy warehouse → BI tools (Tableau/PowerBI)
```

**Pain Points (Quantified)**:
1. **Freshness**: T+3 days average (target: T+0 by 9 AM)
2. **Reliability**: 40% of payroll close nights have reruns
3. **Cost**: $15-25K/month BigQuery spend, 70% from unoptimized queries
4. **Quality**: 200+ production incidents/year from bad data
5. **Compliance**: PII in 12+ tables, unclear lineage, audit gaps

### **2.2 Six Source Domains**

| Domain | Oracle Tables | Key Entities | Daily Volume | Quality Issues |
|--------|---------------|--------------|--------------|----------------|
| Employees | PER_ALL_PEOPLE_F, PER_ASSIGNMENTS_F | employee, person | 50K rows | duplicates, nulls |
| Jobs | PER_JOBS, PER_GRADES | job_code, grade | 5K rows | orphaned FKs |
| Schedules | (external) | shift, schedule | 200K rows | timezone errors |
| Timecards | (external) | timecard, punch | 500K rows | late arrivals |
| Payroll | PAY_PAYROLL_ACTIONS, PAY_RUN_RESULTS | run, element | 100K rows | retro adjustments |
| Cost Centers | GL_CODE_COMBINATIONS | cost_center, GL | 2K rows | schema drift |

### **2.3 Critical Business Questions**

Must support real-time answers to:
1. What is today's headcount by dept/location/union status?
2. What are payroll costs by cost center for current pay period?
3. Which employees are trending toward unplanned OT?
4. What is the impact of late timecard adjustments on payroll close?
5. Are we compliant with wage & hour regulations by state?

### **2.4 Success Criteria (Measurable)**

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Freshness | T+3 days | T+0 by 9 AM | Airflow SLA monitors |
| Pipeline Runtime | 3-5 hours | < 60 min | Airflow duration metrics |
| DQ Block Rate | 0% (prod failures) | 90% pre-prod | Great Expectations pass rate |
| Cost per Query | avg $3.50 | avg $1.20 | BQ slot/bytes metrics |
| Metric Conflicts | 15-20/month | < 2/month | Cross-system reconciliation |
| PII Storage | 12 tables | 3-4 tables | DLP scan results |

---

## **3. END-TO-END ARCHITECTURE**

### **3.1 Layered Architecture (Text Diagram)**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SOURCES (External)                                                          │
│ ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│ │ Oracle   │  │ Kronos   │  │ Manual   │  │ Finance  │  │ Calendar │     │
│ │ HR/Pay   │  │ Time     │  │ CSV      │  │ GL       │  │ API      │     │
│ └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘     │
└──────┼─────────────┼─────────────┼─────────────┼─────────────┼────────────┘
       │             │             │             │             │
       ▼             ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ LANDING ZONE (GCS)                                                          │
│ gs://payroll-landing-{env}/                                                 │
│   ├── domain=employees/load_date=YYYY-MM-DD/*.{csv,json}                   │
│   ├── domain=jobs/load_date=YYYY-MM-DD/*.{csv,json}                        │
│   ├── domain=schedules/load_date=YYYY-MM-DD/*.{csv,json}                   │
│   ├── domain=timecards/load_date=YYYY-MM-DD/*.{csv,json}                   │
│   ├── domain=payroll_runs/load_date=YYYY-MM-DD/*.{csv,json}                │
│   └── domain=cost_centers/load_date=YYYY-MM-DD/*.{csv,json}                │
│                                                                             │
│ [Ingestion Validation: file arrival, checksum, row count manifest]         │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ RAW / BRONZE LAYER (BigQuery)                                               │
│ Dataset: payroll_raw_{env}                                                  │
│                                                                             │
│ Tables: raw_{domain}                                                        │
│   - raw_employees         PARTITION BY load_date  CLUSTER BY employee_id   │
│   - raw_jobs                                                                │
│   - raw_schedules                                                           │
│   - raw_timecards         PARTITION BY load_date  CLUSTER BY employee_id   │
│   - raw_payroll_runs      PARTITION BY load_date  CLUSTER BY run_id        │
│   - raw_cost_centers                                                        │
│                                                                             │
│ Schema: source columns + _load_date, _load_timestamp, _source_file         │
│ Transformations: NONE (preserve source truth)                              │
│ Access: RESTRICTED (Data Eng + Audit only)                                 │
│ Retention: 90 days                                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ STAGING / SILVER LAYER (BigQuery)                                           │
│ Dataset: payroll_staging_{env}                                              │
│                                                                             │
│ Tables: stg_{domain}                                                        │
│   - stg_employees          Deduplicated, standardized, FK validated        │
│   - stg_jobs                                                                │
│   - stg_schedules          Timezone normalized, overlaps resolved          │
│   - stg_timecards          Late arrivals handled, deduplicated             │
│   - stg_payroll_runs       Adjustments merged                              │
│   - stg_cost_centers       Schema drift handled                            │
│                                                                             │
│ [Data Quality Gates: Great Expectations checkpoints]                       │
│ [Deduplication: by business keys + effective date]                         │
│ [Standardization: codes, dates, names, timezones]                          │
│ [FK Enforcement: fail pipeline if orphaned]                                │
│ Access: Data Eng + Analytics Eng                                           │
│ Retention: 30 days                                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ WAREHOUSE / GOLD LAYER (BigQuery)                                           │
│ Dataset: payroll_warehouse_{env}                                            │
│                                                                             │
│ DIMENSIONS (SCD Type 2)                                                     │
│   - dim_employee                                                            │
│       PK: employee_key (surrogate)                                          │
│       BK: employee_id                                                       │
│       SCD: effective_from, effective_to, is_current, row_hash              │
│       Attrs: demographics, employment_status, dept, location, manager      │
│       PARTITION BY DATE_TRUNC(effective_from, MONTH)                       │
│                                                                             │
│   - dim_job                                                                 │
│       PK: job_key (surrogate)                                               │
│       BK: job_code                                                          │
│       SCD: Type 1 (overwrite)                                               │
│       Attrs: title, grade, union_flag, cost_center, GL_code                │
│                                                                             │
│   - dim_date (calendar)                                                     │
│       PK: date_key                                                          │
│       Attrs: fiscal_period, holiday_flag, region, timezone                 │
│                                                                             │
│   - dim_cost_center                                                         │
│       PK: cost_center_key                                                   │
│       BK: cost_center_code                                                  │
│                                                                             │
│ FACTS (Immutable + Late Arriving Handling)                                 │
│   - fact_payroll_run                                                        │
│       Grain: one row per employee per payroll run                          │
│       Keys: employee_key, job_key, run_date_key, cost_center_key           │
│       Measures: gross_pay, net_pay, deductions, taxes, hours_base,         │
│                 hours_overtime, adjustments                                 │
│       PARTITION BY run_date  CLUSTER BY (employee_key, cost_center_key)    │
│                                                                             │
│   - fact_timecard                                                           │
│       Grain: one row per employee per shift                                │
│       Keys: employee_key, shift_date_key, schedule_key                     │
│       Measures: hours_scheduled, hours_worked, hours_overtime,             │
│                 hours_pto, late_flag, adjustment_flag                       │
│       PARTITION BY shift_date  CLUSTER BY employee_key                     │
│                                                                             │
│ Access: Analytics Eng + BI Developers (masked PII)                         │
│ Retention: 7 years (compliance requirement)                                │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ BUSINESS MARTS (BigQuery)                                                   │
│ Dataset: payroll_marts_{env}                                                │
│                                                                             │
│   - mart_payroll_costs                                                      │
│       Grain: cost_center + pay_period                                      │
│       Aggregates: total_payroll, headcount, avg_pay, cost_per_hour         │
│       Denormalized for BI performance                                      │
│                                                                             │
│   - mart_overtime_trends                                                    │
│       Grain: employee + week                                               │
│       Metrics: OT hours, OT %, threshold alerts                            │
│       Supports compliance reporting                                        │
│                                                                             │
│   - mart_headcount_workforce                                                │
│       Grain: dept + location + date                                        │
│       Metrics: active_headcount, new_hires, terminations, turnover_rate    │
│                                                                             │
│   - mart_privacy_anonymized                                                 │
│       All PII removed, aggregated to safe k-anonymity levels              │
│       PUBLIC access tier for broad analytics                               │
│                                                                             │
│ Access: Business Users (all PII masked/aggregated)                         │
│ Retention: 3 years                                                          │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ BI / CONSUMPTION LAYER                                                      │
│   - Tableau / Looker / PowerBI dashboards                                  │
│   - Ad-hoc SQL via BigQuery console (RBAC enforced)                        │
│   - ML/DS notebooks (Vertex AI / Colab)                                    │
│   - External exports (encrypted, audited)                                  │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│ ORCHESTRATION & CONTROL PLANE                                               │
│                                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│ │ Airflow         │  │ Dataform        │  │ Great           │            │
│ │ (Local/GKE)     │  │ (BigQuery)      │  │ Expectations    │            │
│ │                 │  │                 │  │                 │            │
│ │ - DAG schedule  │  │ - SQL transform │  │ - DQ validation │            │
│ │ - SLA monitor   │  │ - dependency    │  │ - checkpoints   │            │
│ │ - alerting      │  │   graph         │  │ - fail-fast     │            │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘            │
│                                                                             │
│ ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│ │ Cloud Logging   │  │ Cloud Monitoring│  │ Data Catalog    │            │
│ │ - audit logs    │  │ - cost alerts   │  │ - lineage       │            │
│ │ - query logs    │  │ - SLO tracking  │  │ - documentation │            │
│ └─────────────────┘  └─────────────────┘  └─────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **3.2 Component-by-Component Explanation**

#### **LANDING ZONE (GCS)**

**Purpose**: Durable, immutable source-of-truth for all ingested files.

**Design Decisions**:
- **Partitioning**: `domain=X/load_date=YYYY-MM-DD/` enables efficient TTL and incremental processing
- **File Format Preservation**: Keep original CSV/JSON (don't force Parquet) to simplify source debugging
- **Metadata Files**: Companion `_manifest.json` per partition with row counts, checksums, source system metadata
- **Idempotency**: Files named with deterministic keys (e.g., `employees_20250115_01.csv`); duplicate uploads = overwrite
- **Validation**: Airflow sensor checks for expected files; alerts on late/missing arrivals

**Tradeoffs**:
- ✅ Simple, transparent, audit-friendly
- ✅ Supports schema evolution (raw files = truth)
- ❌ Storage cost (mitigated by 90-day TTL)
- ❌ No query optimization (that's what BQ layers provide)

---

#### **RAW / BRONZE LAYER**

**Purpose**: Fast, schema-on-read BigQuery mirror of landing files. Minimal transformation.

**Design Decisions**:
- **Loading**: Airflow BigQuery load jobs (not ELT via external tables) for better performance
- **Schema Evolution**: Use `autodetect=True` + schema versioning in metadata; downstream stages handle breaking changes
- **Partitioning**: By `load_date` (not business date) to support time-travel and efficient pruning during backfills
- **Clustering**: By primary entity ID (employee_id, run_id) for downstream join efficiency
- **Audit Columns**: `_load_date`, `_load_timestamp`, `_source_file`, `_row_number`
- **No Dedup**: Raw layer preserves ALL source rows, including duplicates (dedup happens in staging)
- **Access Control**: Dataset-level IAM restriction; only data engineers + audit role

**Tradeoffs**:
- ✅ True source lineage
- ✅ Supports retroactive debugging
- ✅ Fast ingestion (bulk load, no complex logic)
- ❌ Contains quality issues (by design)
- ❌ Contains PII (access restricted)

---

#### **STAGING / SILVER LAYER**

**Purpose**: Clean, validated, standardized data ready for dimensional modeling.

**Design Decisions**:

**Deduplication Strategy**:
```
Business Key: (employee_id, effective_date) for employees
             (timecard_id, punch_time) for timecards
             (run_id, employee_id) for payroll

Dedup Rule: 
  ROW_NUMBER() OVER (PARTITION BY business_key ORDER BY _load_timestamp DESC) = 1
  
Keeps latest load if duplicates arrive in same batch
```

**Standardization**:
- Date/timestamp → UTC, ISO 8601
- Employee names → UPPER + trim
- Codes → lookup tables (job_code, dept_code, etc.)
- Timezone normalization for schedules/timecards

**FK Enforcement**:
```
Great Expectations Suite:
  - expect_column_values_to_be_in_set(cost_center_code, valid_cost_centers)
  - expect_column_pair_values_A_to_be_in_B(employee_id → dim_employee)
  
Fail Policy: Pipeline stops if > 5% FK violations
```

**Late Arriving Handling**:
- Timecards arriving after payroll close → flagged with `late_arrival_flag = TRUE`
- Downstream facts re-process last 7 days on each run to capture late updates
- Retro adjustments tracked in audit table `stg_adjustments_log`

**Schema Drift Handling**:
- Dataform detects new columns via `information_schema.columns` comparison
- New columns allowed if nullable; breaking changes → pipeline fails with alert
- Schema registry stored in `staging_metadata.schema_versions`

**Tradeoffs**:
- ✅ High data quality (DQ gates enforced here)
- ✅ FK integrity guaranteed
- ✅ Supports incremental + full-refresh patterns
- ❌ Complex logic increases failure surface area
- ❌ Runtime cost (mitigated by partitioning)

---

#### **WAREHOUSE / GOLD LAYER**

**Purpose**: Enterprise dimensional model optimized for BI and analytics.

**SCD Type 2 Implementation (dim_employee)**:

Using **Module B: scd2-bq-engine** (detailed in Section 4).

**Key Design**:
```
Surrogate Key: employee_key (auto-increment via BQ sequence or hash-based)
Business Key: employee_id
Hash Diff: MD5(concat of tracked attributes)

Change Detection:
  - Compare row_hash between staging and current dimension
  - If hash differs → close old row (set effective_to), insert new row
  
Effective Dating:
  - effective_from: earliest change date (from staging effective_date)
  - effective_to: 9999-12-31 if current, else next change date
  - is_current: TRUE/FALSE flag
  
Late Arrivals:
  - Backfill logic re-processes last 90 days on each run
  - Overlaps prevented via window functions (lead/lag on effective_from)
  
Rehires / Multi-Active:
  - Allow multiple is_current=TRUE rows if employee has 2+ active assignments
  - job_key differs per row
```

**Fact Table Design**:

**fact_payroll_run**:
- Grain: employee × pay period
- Partitioning: `run_date` (aligns with business queries "last month payroll")
- Clustering: `(employee_key, cost_center_key)` (supports cost center rollups + employee drill-downs)
- Late Arrivals: Upsert logic using MERGE on `(employee_key, run_date)`
- Measures: All additive (gross_pay, taxes, hours) except ratios (calculated in marts)

**fact_timecard**:
- Grain: employee × shift × day
- Partitioning: `shift_date`
- Clustering: `employee_key`
- Late Arrivals: Append-only with `adjustment_flag`; marts aggregate with latest values

**Tradeoffs**:
- ✅ Optimized for BI query patterns (star schema)
- ✅ Historical accuracy via SCD2
- ✅ Cost-efficient (partitioning + clustering reduces scans by 60-80%)
- ❌ Complexity in SCD2 logic (mitigated by Module B templates)
- ❌ Storage overhead for history (7-year retention required by compliance)

---

#### **BUSINESS MARTS**

**Purpose**: Denormalized, aggregated, business-friendly datasets.

**Design Principles**:
- **Pre-Join**: Denormalize dimensions into fact-like tables (no runtime joins for BI)
- **Pre-Aggregate**: Summarize to business grain (cost center × week, not employee × hour)
- **Metric Definitions**: Single source of truth embedded in mart logic
- **Privacy**: Aggregate to k-anonymity ≥ 10 (no individual-level data)

**mart_payroll_costs**:
```
Grain: cost_center + fiscal_period + dept
Metrics: 
  - total_gross_pay, total_net_pay, total_taxes
  - headcount (distinct employees)
  - avg_pay_per_employee
  - cost_per_labor_hour
  - yoy_growth_pct
Refresh: Daily (incremental append)
```

**mart_overtime_trends**:
```
Grain: employee + week (or anonymized dept + week)
Metrics:
  - total_ot_hours
  - ot_pct (OT hours / total hours)
  - threshold_breach_flag (> 10 hrs OT/week)
Privacy: Employee-level only accessible to HR; aggregated version for ops
```

**Tradeoffs**:
- ✅ Blazing fast BI queries (no joins, pre-aggregated)
- ✅ Consistent metrics (logic lives in one place)
- ❌ Storage duplication (mitigated by clustering + short retention)
- ❌ Refresh latency (acceptable for daily BI)

---

#### **ORCHESTRATION & CONTROL PLANE**

**Airflow (Local or GKE)**:
- **DAG Structure**: One DAG per domain, one master DAG for end-to-end
- **Scheduling**: Daily at 2 AM (after expected file arrivals)
- **SLA Monitoring**: Target = 60 min end-to-end; alert if > 90 min
- **Idempotency**: All tasks use deterministic partition keys; safe to re-run

**Dataform**:
- **SQLX Templates**: All transformations defined as SQLX (SQL + Jinja)
- **Dependency Graph**: Auto-generated from ref() macros
- **Assertions**: Built-in `assert` blocks for DQ checks
- **Environments**: dev/test/prod via config overrides

**Great Expectations**:
- **Checkpoint Locations**: 
  - Post-ingestion (raw): file completeness, row count delta < 50%
  - Post-staging: FK integrity, null checks, range checks
  - Post-warehouse: fact/dim relationship integrity
- **Fail-Fast**: Pipeline stops at first checkpoint failure (no bad data in gold)

**Lineage & Documentation**:
- **Data Catalog**: Tag all BQ tables with domain, PII tier, owner
- **Lineage**: Dataform → BQ audit logs → Data Catalog auto-ingestion
- **Documentation**: Markdown in Dataform, published to internal wiki

**Rollback Strategy**:
- BQ snapshots before each prod deployment
- Rollback = restore snapshot + revert Dataform config
- Airflow supports "backfill mode" to re-process historical dates

---

### **3.3 Critical Tradeoffs & Reasoning**

| Decision | Option A | Option B | Choice | Rationale |
|----------|----------|----------|--------|-----------|
| **Orchestration** | Airflow (local/GKE) | Cloud Composer (managed) | Airflow local initially | Cost (Composer = $300/mo base); scale to Composer later |
| **Transform Tool** | dbt | Dataform | Dataform | Native BQ integration, free tier, simpler for GCP-only stack |
| **SCD2 Approach** | dbt snapshots | Custom SQL | Module B (custom) | dbt snapshots are dbt-locked; we need BQ-native, reusable module |
| **Raw Layer Format** | External tables | Loaded tables | Loaded tables | Performance (external tables = query-time read overhead) |
| **DQ Tool** | Great Expectations | dbt tests | GE | More expressive, enterprise-grade reporting, works with Airflow |
| **Privacy Masking** | DLP API | SQL UDFs | SQL UDFs initially | Cost (DLP = per-GB); scale to DLP for auto-discovery later |
| **Cost Attribution** | BQ labels | Dataset naming | BQ labels | More flexible (can tag by team, cost center, project) |

---

## **4. MODULARIZATION PLAN (OSS-FIRST)**

### **4.1 OSS Philosophy & Packaging Strategy**

**Why OSS-First?**
1. **Portfolio Differentiation**: Demonstrates thought leadership beyond tutorial-following
2. **Reusability**: Modules usable across Fortune 500 payroll, retail, finance projects
3. **Community Validation**: Public feedback improves design quality
4. **Career Leverage**: Maintainer credibility for FAANG/consulting interviews

**Packaging Standards (All Modules)**:
- **License**: MIT (permissive)
- **CI/CD**: GitHub Actions (lint, test, publish)
- **Versioning**: Semantic versioning (semver)
- **Distribution**: PyPI (pip), GitHub Releases
- **Documentation**: README + `/docs` folder with examples
- **Testing**: pytest with >80% coverage

---

### **Module A: synthetic-payroll-lab**

#### **Purpose**
Generate realistic, enterprise-messy payroll/timekeeping test data with configurable "chaos" knobs to stress-test pipelines.

#### **Gap Filled**
- Existing synthetic data tools (Faker, Mockaroo) don't understand payroll domain semantics
- No OSS tool simulates common enterprise chaos patterns (late arrivals, schema drift, FK orphans)

#### **Dependencies**
- **Faker** (person names, addresses)
- **Mimesis** (localized data - timezones, currencies)
- **Pandas** (data generation + export)
- **Pydantic** (config validation)

#### **Public API (Pseudo)**

```python
# CLI Interface
$ synthetic-payroll generate \
    --config payroll_config.yaml \
    --output-dir ./landing \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --employees 50000

# Python API
from synthetic_payroll_lab import PayrollGenerator, ChaosConfig

gen = PayrollGenerator(
    employees=50000,
    start_date="2024-01-01",
    chaos=ChaosConfig(
        duplicate_rate=0.02,      # 2% duplicate rows
        null_spike_rate=0.01,     # 1% random null injection
        late_arrival_pct=0.15,    # 15% timecards arrive T+2 days
        schema_drift_days=90,     # Column added every 90 days
        timezone_error_rate=0.03  # 3% wrong timezone
    )
)

gen.generate_all_domains(output_path="./landing", format="csv")
```

#### **Config Schema (YAML)**

```yaml
# payroll_config.yaml
employees:
  count: 50000
  demographics:
    age_min: 18
    age_max: 70
    gender_distribution: [0.48, 0.48, 0.04]  # M, F, Non-binary
  employment:
    full_time_pct: 0.75
    union_pct: 0.30
    turnover_annual_rate: 0.15

jobs:
  job_codes: ["MGR", "ENG", "OPS", "SALES", "ADMIN"]
  pay_grades: [1, 2, 3, 4, 5]
  pay_ranges:
    1: [40000, 60000]
    5: [150000, 250000]

timecards:
  shifts_per_day: 3
  overtime_threshold: 40  # hours/week
  overtime_rate: 1.5
  pto_days_annual: 15

payroll:
  frequency: biweekly  # weekly, biweekly, semimonthly, monthly
  tax_brackets: [0.10, 0.12, 0.22, 0.24]
  deductions: ["401k", "health_insurance", "dental"]

chaos:
  duplicates:
    rate: 0.02
    domains: ["timecards", "employees"]
  nulls:
    spike_rate: 0.01
    columns: ["cost_center", "job_code", "department"]
  late_arrivals:
    pct: 0.15
    lag_days: [1, 2, 3]
  schema_drift:
    frequency_days: 90
    types: ["add_column", "rename_column", "change_type"]
  timezone_errors:
    rate: 0.03
    affected_domains: ["schedules", "timecards"]
  fk_orphans:
    rate: 0.01
    relationships: ["employee_id", "job_code", "cost_center"]
```

#### **v0 Features (MVP)**
1. Generate 6 core domains (employees, jobs, schedules, timecards, payroll, cost centers)
2. CSV/JSON output with Hive-style partitioning (`domain=X/load_date=Y/`)
3. Configurable chaos:
   - Duplicate injection
   - Null spikes
   - Late arriving facts (timecards)
   - Simple schema drift (add column)
4. Deterministic mode (seed for reproducibility)
5. CLI + Python API

#### **v1 Roadmap**
- SCD2 dimension changes (employees change dept/job over time)
- Retro adjustments (payroll corrections)
- Multi-region support (timezones, holidays, labor laws)
- PII variants (masked vs unmasked)
- Parquet output option

#### **v2 Roadmap**
- Streaming mode (simulate real-time arrivals)
- Advanced schema drift (breaking changes, column removal)
- Correlation patterns (high OT → turnover)
- Benchmark suite (compare pipeline performance on standard datasets)

#### **Repo Structure**

```
synthetic-payroll-lab/
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
├── requirements.txt
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── publish.yml
├── src/
│   └── synthetic_payroll_lab/
│       ├── __init__.py
│       ├── cli.py
│       ├── generator.py
│       ├── domains/
│       │   ├── employees.py
│       │   ├── jobs.py
│       │   ├── schedules.py
│       │   ├── timecards.py
│       │   ├── payroll.py
│       │   └── cost_centers.py
│       ├── chaos/
│       │   ├── duplicates.py
│       │   ├── nulls.py
│       │   ├── late_arrivals.py
│       │   ├── schema_drift.py
│       │   └── fk_orphans.py
│       ├── config.py
│       └── utils.py
├── tests/
│   ├── test_generator.py
│   ├── test_domains.py
│   └── test_chaos.py
├── examples/
│   ├── basic_usage.py
│   ├── custom_chaos.py
│   └── benchmark.py
└── docs/
    ├── quickstart.md
    ├── config_reference.md
    ├── chaos_patterns.md
    └── api_reference.md
```

#### **How Project 1 Uses It**

```yaml
# In payroll-lakehouse-gcp/setup/generate_test_data.sh

pip install synthetic-payroll-lab==0.1.0

synthetic-payroll generate \
  --config ./config/synthetic_payroll_config.yaml \
  --output-dir ./landing \
  --start-date 2023-01-01 \
  --end-date 2024-12-31 \
  --employees 50000

# Upload to GCS
gsutil -m cp -r ./landing/* gs://payroll-landing-dev/
```

**Testing Strategy**: Use synthetic data for:
- Unit tests (Dataform SQLX)
- Integration tests (end-to-end Airflow DAG)
- Load tests (pipeline performance benchmarking)
- DQ validation (Great Expectations rule tuning)

---

### **Module B: scd2-bq-engine**

#### **Purpose**
BigQuery-first SCD Type 2 dimension builder with SQLX template generation for Dataform/dbt.

#### **Gap Filled**
- dbt snapshots are dbt-locked and Snowflake-optimized
- Existing SCD2 tutorials use stored procedures (hard to version control)
- No declarative, config-driven SCD2 for BigQuery

#### **Dependencies**
- **Jinja2** (template rendering)
- **Pydantic** (config validation)
- **google-cloud-bigquery** (optional, for validation)
- **PyYAML** (config parsing)

#### **Public API (Pseudo)**

```python
# CLI Interface
$ scd2-bq generate \
    --config dim_employee_scd2.yaml \
    --template-dir ./dataform/definitions \
    --output-file dim_employee.sqlx

# Python API
from scd2_bq_engine import SCD2Generator, SCD2Config

config = SCD2Config(
    source_table="payroll_staging_dev.stg_employees",
    target_table="payroll_warehouse_dev.dim_employee",
    business_key=["employee_id"],
    tracked_columns=["first_name", "last_name", "dept", "job_code", "manager_id"],
    effective_date_column="effective_date",
    hash_algorithm="md5",  # or sha256
    surrogate_key_type="hash",  # or sequence
    handle_deletes=True,
    allow_multi_active=False
)

generator = SCD2Generator(config)
sqlx_code = generator.generate_sqlx()
generator.save(output_path="./dataform/definitions/dim_employee.sqlx")
```

#### **Config Schema (YAML)**

```yaml
# dim_employee_scd2.yaml
dimension:
  name: dim_employee
  source:
    dataset: payroll_staging_dev
    table: stg_employees
  target:
    dataset: payroll_warehouse_dev
    table: dim_employee

keys:
  business_key:
    - employee_id
  surrogate_key:
    name: employee_key
    type: hash  # or sequence (uses BQ GENERATE_UUID or auto-increment)

scd2:
  tracked_columns:
    - first_name
    - last_name
    - dept
    - job_code
    - manager_id
    - location_code
    - employment_status
  
  type1_columns:  # Overwrite without history
    - email
    - phone
  
  effective_dating:
    source_column: effective_date  # Business effective date from source
    effective_from: effective_from
    effective_to: effective_to
    is_current: is_current
    default_end_date: "9999-12-31"
  
  hash_diff:
    algorithm: md5  # or sha256
    column_name: row_hash

  change_detection:
    method: hash_diff  # or column_compare
    include_nulls: true  # NULL = NULL for hash comparison

  late_arrivals:
    enabled: true
    lookback_days: 90  # Re-process last 90 days on each run
    overlap_prevention: true  # Use window functions to prevent gaps

  deletes:
    handle: true
    method: soft_delete  # Set effective_to = run_date, or hard_delete

  multi_active:
    enabled: false  # Allow multiple is_current=TRUE rows
    partition_key: job_assignment_id

partitioning:
  type: range
  column: effective_from
  granularity: month

clustering:
  columns:
    - employee_id
    - dept
```

#### **v0 Features (MVP)**
1. SQLX template generator for standard SCD2 pattern
2. Hash-based change detection (MD5/SHA256)
3. Effective dating with late arrival handling
4. Soft delete support
5. YAML config → SQLX output
6. CLI + Python API

#### **Generated SQLX Output (Pseudo)**

```sql
-- AUTO-GENERATED by scd2-bq-engine v0.1.0
-- Config: dim_employee_scd2.yaml
-- DO NOT EDIT MANUALLY

config {
  type: "incremental",
  bigquery: {
    partitionBy: "DATE_TRUNC(effective_from, MONTH)",
    clusterBy: ["employee_id", "dept"]
  },
  assertions: {
    uniqueKey: ["employee_key"],
    nonNull: ["employee_id", "effective_from"]
  }
}

-- Staging CTE: Load new/changed records
WITH source_data AS (
  SELECT
    employee_id,
    first_name,
    last_name,
    dept,
    job_code,
    manager_id,
    location_code,
    employment_status,
    effective_date,
    TO_HEX(MD5(CONCAT(
      IFNULL(first_name, ''), '|',
      IFNULL(last_name, ''), '|',
      IFNULL(dept, ''), '|',
      IFNULL(job_code, ''), '|',
      IFNULL(manager_id, ''), '|',
      IFNULL(location_code, ''), '|',
      IFNULL(employment_status, '')
    ))) AS row_hash,
    email,  -- Type 1 column
    phone   -- Type 1 column
  FROM ${ref("stg_employees")}
  WHERE effective_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)  -- Late arrival lookback
),

-- Current dimension state
current_dim AS (
  SELECT *
  FROM ${self()}
  WHERE is_current = TRUE
),

-- Detect changes
changes AS (
  SELECT
    s.employee_id,
    s.row_hash AS new_hash,
    c.row_hash AS old_hash,
    CASE
      WHEN c.employee_id IS NULL THEN 'INSERT'
      WHEN s.row_hash != c.row_hash THEN 'UPDATE'
      ELSE 'NO_CHANGE'
    END AS change_type
  FROM source_data s
  LEFT JOIN current_dim c USING (employee_id)
),

-- Close old records
closed_records AS (
  SELECT
    c.*,
    s.effective_date AS new_effective_to,
    FALSE AS is_current
  FROM current_dim c
  INNER JOIN changes ch ON c.employee_id = ch.employee_id AND ch.change_type = 'UPDATE'
  INNER JOIN source_data s ON c.employee_id = s.employee_id
),

-- New records (inserts + updates)
new_records AS (
  SELECT
    TO_HEX(MD5(CONCAT(employee_id, '|', CAST(effective_date AS STRING)))) AS employee_key,
    s.*,
    s.effective_date AS effective_from,
    DATE('9999-12-31') AS effective_to,
    TRUE AS is_current,
    CURRENT_TIMESTAMP() AS _created_at
  FROM source_data s
  INNER JOIN changes ch ON s.employee_id = ch.employee_id AND ch.change_type IN ('INSERT', 'UPDATE')
)

-- Final output
SELECT * FROM closed_records
UNION ALL
SELECT * FROM new_records
```

#### **v1 Roadmap**
- Surrogate key via BQ sequences (when available)
- Multi-active dimension support
- dbt Core compatibility (not just Dataform)
- Performance optimizations (incremental merge)
- Data validation tests (no overlaps, no gaps)

#### **v2 Roadmap**
- SCD Type 1 + Type 3 support
- Bi-temporal dimensions (valid time + transaction time)
- Automated testing framework
- Metabase/Looker LookML generator from SCD2 config

#### **Repo Structure**

```
scd2-bq-engine/
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
├── requirements.txt
├── .github/workflows/
├── src/
│   └── scd2_bq_engine/
│       ├── __init__.py
│       ├── cli.py
│       ├── generator.py
│       ├── config.py
│       ├── templates/
│       │   ├── scd2_base.sqlx.jinja
│       │   ├── scd2_multi_active.sqlx.jinja
│       │   └── scd2_with_deletes.sqlx.jinja
│       ├── validators.py
│       └── utils.py
├── tests/
│   ├── test_generator.py
│   ├── test_config.py
│   └── fixtures/
│       └── sample_configs/
├── examples/
│   ├── basic_dimension.py
│   ├── multi_active_dimension.py
│   └── late_arrivals.py
└── docs/
    ├── quickstart.md
    ├── config_reference.md
    ├── patterns.md
    └── troubleshooting.md
```

#### **How Project 1 Uses It**

```yaml
# In payroll-lakehouse-gcp/dataform/scripts/generate_dimensions.sh

pip install scd2-bq-engine==0.1.0

# Generate dim_employee SQLX
scd2-bq generate \
  --config ./config/dimensions/dim_employee_scd2.yaml \
  --output-file ./definitions/warehouse/dim_employee.sqlx

# Generate dim_job (Type 1 only)
scd2-bq generate \
  --config ./config/dimensions/dim_job_scd1.yaml \
  --output-file ./definitions/warehouse/dim_job.sqlx

# Commit generated SQLX to repo (version controlled)
```

**Testing**: Module B includes unit tests that run against BigQuery emulator (local) or dev dataset.

---

### **Module C: dataform-warehouse-blueprints**

#### **Purpose**
Opinionated Dataform SQLX project template with best-practice patterns for raw → staging → warehouse → marts layering.

#### **Gap Filled**
- Dataform docs lack enterprise conventions
- No OSS blueprint for multi-layer, privacy-tiered architectures
- Teams waste weeks debating naming, partitioning, testing standards

#### **Dependencies**
- **Dataform CLI** (user-installed, not bundled)
- **Node.js** (for Dataform)
- **Cookiecutter** (optional, for project scaffolding)

#### **Public API**

```bash
# CLI Interface (uses cookiecutter-style templating)
$ npx degit github:yourorg/dataform-warehouse-blueprints my-dataform-project
$ cd my-dataform-project
$ npm install

# Or via cookiecutter
$ cookiecutter gh:yourorg/dataform-warehouse-blueprints
  project_name [My Data Warehouse]: Payroll Analytics
  gcp_project_id [my-gcp-project]: payroll-analytics-prod
  bigquery_location [US]: US
  layers [raw,staging,warehouse,marts]: raw,staging,warehouse,marts
  enable_privacy_tiers [y/n]: y
  enable_scd2 [y/n]: y
```

#### **Blueprint Features (v0)**

1. **Layered Dataset Conventions**:
   ```
   {project}_raw_{env}
   {project}_staging_{env}
   {project}_warehouse_{env}
   {project}_marts_{env}
   ```

2. **Naming Standards**:
   ```
   Raw: raw_{domain}
   Staging: stg_{domain}
   Warehouse Dims: dim_{entity}
   Warehouse Facts: fact_{entity}
   Marts: mart_{business_area}
   ```

3. **SQLX Templates** (in `/templates`):
   - `raw_table.sqlx`: Minimal transformations, audit columns
   - `staging_table.sqlx`: Dedup, standardization, FK checks
   - `dim_scd2.sqlx`: Placeholder for Module B output
   - `fact_table.sqlx`: Incremental fact pattern
   - `mart_aggregated.sqlx`: Denormalized mart pattern

4. **Partitioning/Clustering Guidance** (in comments):
   ```sql
   -- PARTITION BY: Use load_date (raw), business_date (staging/warehouse)
   -- CLUSTER BY: Use FK columns (employee_id, cost_center_id) for join optimization
   ```

5. **Testing Conventions**:
   ```sql
   -- In each SQLX file:
   assertions {
     uniqueKey: ["primary_key"],
     nonNull: ["critical_column"],
     rowConditions: [
       "amount >= 0",
       "effective_to >= effective_from"
     ]
   }
   ```

6. **Lineage Documentation**:
   ```sql
   -- In each SQLX file:
   description: "Employee dimension with SCD Type 2 history tracking..."
   columns {
     employee_key {
       description: "Surrogate key (hash of employee_id + effective_from)"
     }
   }
   ```

7. **Environment Configs**:
   ```json
   // environments.json
   {
     "dev": {
       "projectId": "payroll-dev",
       "location": "US",
       "vars": {
         "env": "dev"
       }
     },
     "prod": {
       "projectId": "payroll-prod",
       "location": "US",
       "vars": {
         "env": "prod"
       }
     }
   }
   ```

#### **Config Schema (Not Applicable)**

This module is a repo template, not a library. Configuration is via Dataform's native `dataform.json` and `environments.json`.

#### **v0 Features (MVP)**
1. Cookiecutter-style project scaffold
2. 4-layer SQLX templates (raw/staging/warehouse/marts)
3. Naming + partitioning conventions (documented)
4. Example dimension + fact SQLX files
5. Testing patterns (assertions)
6. README with onboarding guide

#### **v1 Roadmap**
- Privacy tier templates (masked/aggregated datasets)
- Great Expectations integration patterns
- Airflow DAG templates for Dataform orchestration
- Pre-commit hooks (SQLX linting)

#### **v2 Roadmap**
- Multi-cloud support (Snowflake, Redshift)
- dbt compatibility layer
- CI/CD pipeline templates (GitHub Actions)

#### **Repo Structure**

```
dataform-warehouse-blueprints/
├── README.md
├── LICENSE
├── cookiecutter.json  # Optional
├── {{cookiecutter.project_name}}/
│   ├── dataform.json
│   ├── package.json
│   ├── .gitignore
│   ├── environments.json
│   ├── includes/
│   │   ├── constants.js
│   │   └── helpers.js
│   ├── definitions/
│   │   ├── raw/
│   │   │   ├── _raw_layer_readme.md
│   │   │   └── raw_employees.sqlx  # Example
│   │   ├── staging/
│   │   │   ├── _staging_layer_readme.md
│   │   │   └── stg_employees.sqlx  # Example
│   │   ├── warehouse/
│   │   │   ├── dimensions/
│   │   │   │   ├── _dimension_readme.md
│   │   │   │   └── dim_employee.sqlx  # SCD2 example
│   │   │   └── facts/
│   │   │       ├── _fact_readme.md
│   │   │       └── fact_payroll_run.sqlx  # Example
│   │   └── marts/
│   │       ├── _marts_readme.md
│   │       └── mart_payroll_costs.sqlx  # Example
│   ├── tests/
│   │   └── assertions.sql
│   └── docs/
│       ├── conventions.md
│       ├── partitioning_guide.md
│       ├── privacy_tiers.md
│       └── onboarding.md
└── templates/
    ├── raw_table.sqlx.template
    ├── staging_table.sqlx.template
    ├── dim_scd2.sqlx.template
    ├── fact_table.sqlx.template
    └── mart_aggregated.sqlx.template
```

#### **How Project 1 Uses It**

```bash
# Initialize payroll-lakehouse-gcp with blueprint
$ cookiecutter gh:yourorg/dataform-warehouse-blueprints
  project_name: payroll-lakehouse-gcp
  gcp_project_id: payroll-analytics-prod
  ...

# Blueprint generates:
# /dataform
#   ├── dataform.json
#   ├── definitions/
#   │   ├── raw/
#   │   ├── staging/
#   │   ├── warehouse/
#   │   └── marts/
#   └── docs/

# Customize definitions for payroll domains (employees, timecards, etc.)
# Follow naming/testing conventions from blueprint docs
```

**Value**: Saves 2-3 weeks of "bikeshedding" on conventions; team starts with battle-tested patterns.

---

### **Module D: bq-finops-cli**

#### **Purpose**
Developer-friendly FinOps toolkit for BigQuery cost monitoring, optimization detection, and before/after reporting.

#### **Gap Filled**
- GCP Console cost reports are executive-level, not developer-actionable
- No OSS tool for query-level cost attribution + optimization rules
- FinOps requires SQL + scripting knowledge; this abstracts it

#### **Dependencies**
- **google-cloud-bigquery** (query execution)
- **google-cloud-logging** (audit log parsing)
- **Pandas** (data manipulation)
- **Tabulate** (CLI table formatting)
- **Click** (CLI framework)
- **PyYAML** (config)

#### **Public API (Pseudo)**

```bash
# CLI Interface

# 1. Setup: Create cost tracking tables
$ bq-finops init \
    --project payroll-analytics-prod \
    --dataset finops_monitoring \
    --schedule daily

# 2. Daily cost report
$ bq-finops report \
    --project payroll-analytics-prod \
    --start-date 2024-11-01 \
    --end-date 2024-11-30 \
    --group-by user,dataset

# Output:
# ┌──────────────┬────────────────────────┬──────────────┬──────────────┐
# │ User         │ Dataset                │ Bytes Scanned│ Est Cost ($) │
# ├──────────────┼────────────────────────┼──────────────┼──────────────┤
# │ analyst1@    │ payroll_marts_prod     │ 10.5 TB      │ $52.50       │
# │ analyst2@    │ payroll_warehouse_prod │ 25.3 TB      │ $126.50      │
# │ airflow@     │ payroll_staging_prod   │ 5.2 TB       │ $26.00       │
# └──────────────┴────────────────────────┴──────────────┴──────────────┘

# 3. Detect anti-patterns
$ bq-finops detect \
    --project payroll-analytics-prod \
    --rules ./finops_rules.yaml

# Output:
# ⚠️  WARNING: Table payroll_raw_prod.raw_timecards missing partition filter
#     Query: SELECT * FROM raw_timecards WHERE employee_id = 12345
#     Impact: Scanned 500 GB (should be < 1 GB with partition filter)
#     Recommendation: Add WHERE load_date >= '2024-11-01'

# 4. Optimization tracking
$ bq-finops optimize track \
    --table payroll_warehouse_prod.fact_payroll_run \
    --change "Added clustering by (employee_key, cost_center_key)" \
    --compare-days 30

# Output:
# 📊 Optimization Impact:
#     Before: 15.2 TB scanned/month, $76.00
#     After:  6.1 TB scanned/month, $30.50
#     Savings: 60% reduction, $45.50/month

# 5. Cost attribution labels report
$ bq-finops labels \
    --project payroll-analytics-prod \
    --label team \
    --start-date 2024-11-01

# Output:
# ┌─────────────┬──────────────┬──────────────┐
# │ Team        │ Bytes Scanned│ Est Cost ($) │
# ├─────────────┼──────────────┼──────────────┤
# │ finance     │ 12.3 TB      │ $61.50       │
# │ hr          │ 8.7 TB       │ $43.50       │
# │ operations  │ 20.5 TB      │ $102.50      │
# └─────────────┴──────────────┴──────────────┘
```

#### **Config Schema (YAML)**

```yaml
# finops_rules.yaml
rules:
  - name: missing_partition_filter
    description: "Detect queries scanning partitioned tables without partition filter"
    severity: high
    pattern: |
      SELECT *
      FROM `${project}.${dataset}.${table}`
      WHERE partition_column IS NOT IN filter
    threshold:
      bytes_scanned_ratio: 0.1  # Alert if scanned > 10% of table
    recommendation: "Add partition filter (e.g., WHERE load_date >= ...)"

  - name: select_star_antipattern
    description: "Detect SELECT * on wide tables"
    severity: medium
    pattern: "SELECT *"
    threshold:
      column_count: 50  # Alert if table has > 50 columns
    recommendation: "Select only needed columns"

  - name: full_table_scan
    description: "Detect full table scans on large tables"
    severity: high
    threshold:
      bytes_scanned: 1_000_000_000_000  # 1 TB
    recommendation: "Add indexes, partitioning, or clustering"

  - name: expensive_join
    description: "Detect expensive cross-joins or unoptimized joins"
    severity: high
    pattern: "CROSS JOIN"
    recommendation: "Replace with INNER JOIN on explicit key"

  - name: repeated_full_refresh
    description: "Detect tables rebuilt daily instead of incremental"
    severity: medium
    threshold:
      refresh_frequency: daily
      table_size_gb: 100  # Alert if > 100 GB rebuilt daily
    recommendation: "Switch to incremental pattern"

cost_thresholds:
  daily_limit: 50  # USD
  monthly_limit: 1000  # USD
  alert_on_spike: 1.5  # Alert if daily cost > 1.5x avg

attribution:
  required_labels:
    - team
    - cost_center
    - environment
  untagged_alert: true
```

#### **v0 Features (MVP)**
1. CLI for cost reporting by user/dataset/table
2. Anti-pattern detection (5 rules)
3. Before/after optimization tracking
4. SQL to materialize cost tables from INFORMATION_SCHEMA
5. Label-based cost attribution

#### **SQL Pack Included**

Module includes pre-written SQL queries:

```sql
-- queries/cost_by_user.sql
-- Materialized daily via scheduled query
CREATE OR REPLACE TABLE `${project}.finops_monitoring.cost_by_user`
PARTITION BY DATE(query_start_time)
AS
SELECT
  DATE(creation_time) AS query_date,
  user_email,
  project_id,
  dataset_id,
  table_id,
  SUM(total_bytes_processed) AS total_bytes,
  SUM(total_bytes_processed) / POW(10, 12) * 5 AS estimated_cost_usd,
  COUNT(*) AS query_count
FROM `region-us`.INFORMATION_SCHEMA.JOBS_BY_PROJECT
WHERE creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
  AND statement_type = 'SELECT'
  AND state = 'DONE'
  AND error_result IS NULL
GROUP BY 1, 2, 3, 4, 5;
```

#### **v1 Roadmap**
- Slack/email alerting on cost spikes
- Query recommendation engine (AI-powered)
- Integration with Dataform (tag expensive queries)
- Cost forecasting (ML-based)

#### **v2 Roadmap**
- Multi-cloud support (Snowflake, Redshift)
- FinOps dashboard (web UI)
- Chargeback automation (cost center billing)

#### **Repo Structure**

```
bq-finops-cli/
├── README.md
├── LICENSE
├── setup.py
├── pyproject.toml
├── requirements.txt
├── .github/workflows/
├── src/
│   └── bq_finops_cli/
│       ├── __init__.py
│       ├── cli.py
│       ├── cost_reporter.py
│       ├── anti_pattern_detector.py
│       ├── optimizer_tracker.py
│       ├── label_analyzer.py
│       ├── queries/
│       │   ├── cost_by_user.sql
│       │   ├── cost_by_table.sql
│       │   ├── expensive_queries.sql
│       │   └── optimization_impact.sql
│       └── utils.py
├── tests/
│   ├── test_reporter.py
│   ├── test_detector.py
│   └── fixtures/
├── examples/
│   ├── daily_report.sh
│   ├── optimization_workflow.sh
│   └── finops_rules.yaml
└── docs/
    ├── quickstart.md
    ├── rules_reference.md
    ├── optimization_guide.md
    └── cost_attribution.md
```

#### **How Project 1 Uses It**

```bash
# In payroll-lakehouse-gcp/.github/workflows/finops_report.yml

name: Daily FinOps Report
on:
  schedule:
    - cron: '0 10 * * *'  # 10 AM daily

jobs:
  finops_report:
    runs-on: ubuntu-latest
    steps:
      - name: Install bq-finops-cli
        run: pip install bq-finops-cli==0.1.0

      - name: Generate cost report
        run: |
          bq-finops report \
            --project payroll-analytics-prod \
            --start-date $(date -d '7 days ago' +%Y-%m-%d) \
            --end-date $(date +%Y-%m-%d) \
            --group-by team,dataset \
            --output ./reports/cost_report_$(date +%Y%m%d).csv

      - name: Detect anti-patterns
        run: |
          bq-finops detect \
            --project payroll-analytics-prod \
            --rules ./config/finops_rules.yaml \
            --output ./reports/antipatterns_$(date +%Y%m%d).txt

      - name: Post to Slack
        run: |
          curl -X POST -H 'Content-type: application/json' \
            --data "$(cat ./reports/cost_report_$(date +%Y%m%d).csv)" \
            ${{ secrets.SLACK_WEBHOOK_URL }}
```

**Value**: Continuous FinOps discipline without manual effort; 30-60% cost reduction via automated optimization detection.

---

### **4.2 Module Publishing Strategy**

| Module | PyPI Package | GitHub Repo | Initial Version |
|--------|--------------|-------------|----------------|
| A | synthetic-payroll-lab | synthetic-payroll-lab | 0.1.0 |
| B | scd2-bq-engine | scd2-bq-engine | 0.1.0 |
| C | N/A (template repo) | dataform-warehouse-blueprints | v1.0.0 |
| D | bq-finops-cli | bq-finops-cli | 0.1.0 |

**Version Pinning in Project 1**:
```
# payroll-lakehouse-gcp/requirements.txt
synthetic-payroll-lab==0.1.0
scd2-bq-engine==0.1.0
bq-finops-cli==0.1.0
```

**Dependency Upgrade Policy**:
- Modules: Semantic versioning; patch updates (0.1.x) auto-applied
- Project 1: Pin major.minor; test upgrades in dev before prod

---

## **5. PROJECT REPO STRATEGY & STRUCTURE**

### **5.1 GitHub Organization Layout**

**Recommended**:
```
yourorg/
├── synthetic-payroll-lab          # Module A (OSS)
├── scd2-bq-engine                 # Module B (OSS)
├── dataform-warehouse-blueprints  # Module C (OSS)
├── bq-finops-cli                  # Module D (OSS)
└── payroll-lakehouse-gcp          # Project 1 (can be private or public)
```

**Reasoning**:
- Separate repos = independent versioning, release cycles
- Modules are reusable across projects (payroll, retail, finance)
- Project 1 depends on modules via pip/git submodules

**Alternative (Monorepo)**:
```
data-engineering-portfolio/
├── modules/
│   ├── synthetic-payroll-lab/
│   ├── scd2-bq-engine/
│   ├── dataform-warehouse-blueprints/
│   └── bq-finops-cli/
└── projects/
    └── payroll-lakehouse-gcp/
```

**Tradeoff**: Monorepo simplifies local dev but complicates OSS release process (need subtree splits).

**Recommendation**: Separate repos for portfolio showcase (demonstrates packaging/publishing skills).

---

### **5.2 Project 1 Mono-Repo Structure (Planning)**

```
payroll-lakehouse-gcp/
├── README.md                          # Hero README with architecture, metrics, setup
├── LICENSE                            # MIT or Apache 2.0
├── .gitignore
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Lint, test Dataform
│       ├── deploy_dev.yml             # Deploy to dev on merge to main
│       ├── deploy_prod.yml            # Deploy to prod on tag
│       └── finops_report.yml          # Daily cost report (uses Module D)
│
├── docs/
│   ├── architecture.md                # Detailed architecture doc
│   ├── data_model.md                  # ERDs, schema docs
│   ├── dataops.md                     # CI/CD, DQ gates
│   ├── finops.md                      # Cost strategy
│   ├── privacy.md                     # PII governance
│   ├── runbook.md                     # Operations guide
│   └── postmortem.md                  # Lessons learned
│
├── config/
│   ├── synthetic_payroll_config.yaml  # Module A config (test data gen)
│   ├── finops_rules.yaml              # Module D config (cost rules)
│   ├── dimensions/
│   │   ├── dim_employee_scd2.yaml     # Module B config (SCD2)
│   │   └── dim_job_scd1.yaml
│   └── great_expectations/
│       ├── great_expectations.yml
│       └── checkpoints/
│           ├── raw_checkpoint.yml
│           ├── staging_checkpoint.yml
│           └── warehouse_checkpoint.yml
│
├── airflow/
│   ├── dags/
│   │   ├── payroll_ingestion.py       # GCS → BigQuery raw
│   │   ├── payroll_staging.py         # Raw → Staging + DQ
│   │   ├── payroll_warehouse.py       # Staging → Warehouse
│   │   ├── payroll_marts.py           # Warehouse → Marts
│   │   └── payroll_master_dag.py      # End-to-end orchestration
│   ├── plugins/
│   │   ├── gcs_sensor.py              # Custom file arrival sensor
│   │   └── ge_operator.py             # Great Expectations operator
│   ├── docker-compose.yml             # Local Airflow setup
│   └── Dockerfile
│
├── dataform/                          # Initialized from Module C
│   ├── dataform.json
│   ├── package.json
│   ├── environments.json              # dev/test/prod configs
│   ├── includes/
│   │   ├── constants.js               # Dataset names, constants
│   │   └── helpers.js                 # Reusable JS functions
│   ├── definitions/
│   │   ├── raw/
│   │   │   ├── raw_employees.sqlx
│   │   │   ├── raw_jobs.sqlx
│   │   │   ├── raw_schedules.sqlx
│   │   │   ├── raw_timecards.sqlx
│   │   │   ├── raw_payroll_runs.sqlx
│   │   │   └── raw_cost_centers.sqlx
│   │   ├── staging/
│   │   │   ├── stg_employees.sqlx
│   │   │   ├── stg_jobs.sqlx
│   │   │   ├── stg_schedules.sqlx
│   │   │   ├── stg_timecards.sqlx
│   │   │   ├── stg_payroll_runs.sqlx
│   │   │   └── stg_cost_centers.sqlx
│   │   ├── warehouse/
│   │   │   ├── dimensions/
│   │   │   │   ├── dim_employee.sqlx      # Generated by Module B
│   │   │   │   ├── dim_job.sqlx
│   │   │   │   ├── dim_date.sqlx
│   │   │   │   └── dim_cost_center.sqlx
│   │   │   └── facts/
│   │   │       ├── fact_payroll_run.sqlx
│   │   │       └── fact_timecard.sqlx
│   │   └── marts/
│   │       ├── mart_payroll_costs.sqlx
│   │       ├── mart_overtime_trends.sqlx
│   │       ├── mart_headcount_workforce.sqlx
│   │       └── mart_privacy_anonymized.sqlx
│   └── tests/
│       └── assertions.sql
│
├── terraform/                         # IaC (optional, enhances portfolio)
│   ├── main.tf
│   ├── variables.tf
│   ├── modules/
│   │   ├── gcs/                       # Landing bucket
│   │   ├── bigquery/                  # Datasets
│   │   └── iam/                       # Service accounts, roles
│   └── environments/
│       ├── dev.tfvars
│       ├── test.tfvars
│       └── prod.tfvars
│
├── scripts/
│   ├── setup/
│   │   ├── 01_generate_test_data.sh   # Uses Module A
│   │   ├── 02_create_datasets.sh      # Create BQ datasets
│   │   ├── 03_setup_airflow.sh        # Local Airflow setup
│   │   └── 04_init_great_expectations.sh
│   ├── deploy/
│   │   ├── deploy_dataform.sh         # Deploy SQLX to BQ
│   │   └── deploy_airflow_dags.sh
│   └── utilities/
│       ├── backfill.sh                # Backfill utility
│       └── rollback.sh                # Rollback utility
│
├── tests/
│   ├── unit/
│   │   └── test_dataform_sql.py       # SQL unit tests
│   ├── integration/
│   │   └── test_end_to_end_pipeline.py
│   └── fixtures/
│       └── sample_data/               # Small test datasets
│
├── reports/
│   ├── optimization_report.md         # Before/after FinOps metrics
│   ├── data_quality_dashboard.png
│   └── lineage_diagram.png
│
├── requirements.txt                   # Python dependencies (modules + tools)
├── requirements-dev.txt               # Dev dependencies (pytest, black, etc.)
└── Makefile                           # Convenience commands (make test, make deploy, etc.)
```

### **5.3 Dependency Management**

**requirements.txt** (Project 1):
```
# OSS Modules (pinned versions)
synthetic-payroll-lab==0.1.0
scd2-bq-engine==0.1.0
bq-finops-cli==0.1.0

# Data Engineering
apache-airflow==2.7.3
great-expectations==0.18.8
google-cloud-bigquery==3.14.0
google-cloud-storage==2.13.0

# Utilities
pandas==2.1.4
pyyaml==6.0.1
click==8.1.7
tabulate==0.9.0
```

**Dataform dependencies** (package.json):
```json
{
  "name": "payroll-lakehouse-dataform",
  "version": "1.0.0",
  "dependencies": {
    "@dataform/core": "^2.9.0"
  }
}
```

**Module C blueprint** (cloned, not installed):
```bash
# One-time setup
npx degit yourorg/dataform-warehouse-blueprints ./dataform
```

---

### **5.4 Version Control Strategy**

**Branching**:
```
main          # Production-ready code
├── develop   # Integration branch
├── feature/* # Feature branches
└── hotfix/*  # Production hotfixes
```

**Git Tags**:
- Modules: `v0.1.0`, `v0.2.0` (semver)
- Project 1: `v1.0.0-dev`, `v1.0.0-prod` (environment-aware)

**Release Process**:
1. Modules: Develop → tag → CI publishes to PyPI → Project 1 updates requirements.txt
2. Project 1: Feature branch → develop → main → tag → CI deploys to dev → manual approval → prod

---

## **6. DATA MODEL PLAN (NO SQL)**

### **6.1 Source Schemas (Oracle-Like Legacy)**

#### **Domain: Employees**

**Source Tables**: `PER_ALL_PEOPLE_F` (Oracle)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| person_id | NUMBER | Unique person ID | ✓ | N |
| effective_start_date | DATE | Effective from | ✓ | N |
| effective_end_date | DATE | Effective to | | N |
| employee_number | VARCHAR(30) | Business key | | N |
| first_name | VARCHAR(150) | | | Y |
| last_name | VARCHAR(150) | | | N |
| date_of_birth | DATE | PII | | Y |
| national_identifier | VARCHAR(30) | SSN-like, PII | | Y |
| email_address | VARCHAR(240) | | | Y |
| phone_number | VARCHAR(60) | | | Y |
| hire_date | DATE | | | N |
| termination_date | DATE | | | Y |
| employment_status | VARCHAR(30) | ACTIVE, TERMINATED, LOA | | N |

**Source Tables**: `PER_ALL_ASSIGNMENTS_F` (Oracle)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| assignment_id | NUMBER | Unique assignment | ✓ | N |
| person_id | NUMBER | FK to people | | N |
| effective_start_date | DATE | Effective from | ✓ | N |
| effective_end_date | DATE | Effective to | | N |
| job_id | NUMBER | FK to jobs | | N |
| department_id | NUMBER | | | Y |
| location_id | NUMBER | | | Y |
| manager_id | NUMBER | FK to person | | Y |
| cost_center | VARCHAR(30) | | | Y |
| employment_category | VARCHAR(30) | FT, PT, CONTRACTOR | | N |
| union_flag | VARCHAR(1) | Y/N | | N |

---

#### **Domain: Jobs**

**Source Tables**: `PER_JOBS` (Oracle)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| job_id | NUMBER | Unique job | ✓ | N |
| job_code | VARCHAR(30) | Business key | | N |
| job_title | VARCHAR(240) | | | N |
| job_family | VARCHAR(60) | ENG, OPS, SALES, etc. | | Y |
| job_level | NUMBER | 1-10 | | Y |
| pay_grade | VARCHAR(30) | | | Y |
| union_eligible | VARCHAR(1) | Y/N | | N |

---

#### **Domain: Schedules**

**Source Tables**: `TIMEKEEPER_SCHEDULES` (External CSV)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| schedule_id | VARCHAR(50) | Unique schedule | ✓ | N |
| employee_id | VARCHAR(30) | FK | | N |
| shift_date | DATE | | ✓ | N |
| shift_start | TIMESTAMP | | | N |
| shift_end | TIMESTAMP | | | N |
| timezone | VARCHAR(50) | | | Y |
| location_code | VARCHAR(30) | | | Y |
| schedule_type | VARCHAR(30) | REGULAR, ONCALL, PTO | | N |

---

#### **Domain: Timecards**

**Source Tables**: `TIMEKEEPER_TIMECARDS` (External JSON)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| timecard_id | VARCHAR(50) | Unique timecard | ✓ | N |
| employee_id | VARCHAR(30) | FK | | N |
| work_date | DATE | | | N |
| punch_in | TIMESTAMP | | | Y |
| punch_out | TIMESTAMP | | | Y |
| hours_worked | DECIMAL(5,2) | | | Y |
| hours_overtime | DECIMAL(5,2) | | | Y |
| hours_pto | DECIMAL(5,2) | | | Y |
| approval_status | VARCHAR(30) | PENDING, APPROVED, REJECTED | | N |
| adjustment_flag | BOOLEAN | Late retro adjustment | | N |

---

#### **Domain: Payroll Runs**

**Source Tables**: `PAY_PAYROLL_ACTIONS`, `PAY_RUN_RESULTS` (Oracle)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| run_id | NUMBER | Unique payroll run | ✓ | N |
| run_date | DATE | Payroll period end | | N |
| run_type | VARCHAR(30) | REGULAR, BONUS, ADJUSTMENT | | N |
| employee_id | VARCHAR(30) | FK | ✓ | N |
| gross_pay | DECIMAL(12,2) | | | N |
| net_pay | DECIMAL(12,2) | | | N |
| tax_federal | DECIMAL(12,2) | | | Y |
| tax_state | DECIMAL(12,2) | | | Y |
| tax_fica | DECIMAL(12,2) | | | Y |
| deduction_401k | DECIMAL(12,2) | | | Y |
| deduction_insurance | DECIMAL(12,2) | | | Y |
| hours_base | DECIMAL(5,2) | Regular hours | | Y |
| hours_overtime | DECIMAL(5,2) | OT hours | | Y |

---

#### **Domain: Cost Centers**

**Source Tables**: `GL_CODE_COMBINATIONS` (Oracle)

| Column | Type | Description | PK | Nullable |
|--------|------|-------------|----|----|
| cost_center_id | NUMBER | Unique ID | ✓ | N |
| cost_center_code | VARCHAR(30) | Business key | | N |
| cost_center_name | VARCHAR(240) | | | N |
| gl_account | VARCHAR(30) | GL mapping | | Y |
| department | VARCHAR(60) | | | Y |
| location | VARCHAR(60) | | | Y |
| active_flag | VARCHAR(1) | Y/N | | N |

---

### **6.2 RAW Layer (BigQuery)**

**Design Principle**: Mirror source with minimal transformations; add audit columns.

#### **raw_employees**

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| person_id | INT64 | | people.person_id |
| effective_start_date | DATE | | people.effective_start_date |
| effective_end_date | DATE | | people.effective_end_date |
| employee_number | STRING | | people.employee_number |
| first_name | STRING | | people.first_name |
| last_name | STRING | | people.last_name |
| date_of_birth | DATE | | people.date_of_birth |
| national_identifier | STRING | | people.national_identifier |
| email_address | STRING | | people.email_address |
| phone_number | STRING | | people.phone_number |
| hire_date | DATE | | people.hire_date |
| termination_date | DATE | | people.termination_date |
| employment_status | STRING | | people.employment_status |
| assignment_id | INT64 | | assignments.assignment_id |
| job_id | INT64 | | assignments.job_id |
| department_id | INT64 | | assignments.department_id |
| location_id | INT64 | | assignments.location_id |
| manager_id | INT64 | | assignments.manager_id |
| cost_center | STRING | | assignments.cost_center |
| employment_category | STRING | | assignments.employment_category |
| union_flag | STRING | | assignments.union_flag |
| **_load_date** | DATE | Partition | Airflow runtime |
| **_load_timestamp** | TIMESTAMP | | Airflow runtime |
| **_source_file** | STRING | | GCS file path |
| **_row_number** | INT64 | | Row number in source file |

**Partitioning**: `PARTITION BY _load_date`  
**Clustering**: `CLUSTER BY employee_number`  
**Retention**: 90 days

---

#### **raw_timecards**

| Column | Type | Description | Source |
|--------|------|-------------|--------|
| timecard_id | STRING | | timecards.timecard_id |
| employee_id | STRING | | timecards.employee_id |
| work_date | DATE | | timecards.work_date |
| punch_in | TIMESTAMP | | timecards.punch_in |
| punch_out | TIMESTAMP | | timecards.punch_out |
| hours_worked | NUMERIC | | timecards.hours_worked |
| hours_overtime | NUMERIC | | timecards.hours_overtime |
| hours_pto | NUMERIC | | timecards.hours_pto |
| approval_status | STRING | | timecards.approval_status |
| adjustment_flag | BOOL | | timecards.adjustment_flag |
| **_load_date** | DATE | Partition | Airflow runtime |
| **_load_timestamp** | TIMESTAMP | | Airflow runtime |
| **_source_file** | STRING | | GCS file path |

**Partitioning**: `PARTITION BY _load_date`  
**Clustering**: `CLUSTER BY employee_id, work_date`  
**Retention**: 90 days

---

### **6.3 STAGING Layer (BigQuery)**

**Design Principle**: Clean, deduplicated, standardized, FK-validated.

#### **stg_employees**

| Column | Type | Description | Transformation |
|--------|------|-------------|----------------|
| employee_id | STRING | Standardized BK | CAST(employee_number AS STRING) |
| effective_date | DATE | Effective start | effective_start_date |
| first_name | STRING | Standardized | UPPER(TRIM(first_name)) |
| last_name | STRING | Standardized | UPPER(TRIM(last_name)) |
| full_name | STRING | Computed | CONCAT(first_name, ' ', last_name) |
| date_of_birth | DATE | | date_of_birth |
| age | INT64 | Computed | DATE_DIFF(CURRENT_DATE(), date_of_birth, YEAR) |
| national_identifier_hash | STRING | Masked PII | TO_HEX(SHA256(national_identifier)) |
| email_address | STRING | | email_address |
| phone_number | STRING | | phone_number |
| hire_date | DATE | | hire_date |
| termination_date | DATE | | termination_date |
| employment_status | STRING | Standardized | CASE ... END (map codes) |
| job_code | STRING | FK | COALESCE(job_id, 'UNKNOWN') |
| department_code | STRING | FK | COALESCE(department_id, 'UNKNOWN') |
| location_code | STRING | FK | COALESCE(location_id, 'UNKNOWN') |
| manager_id | STRING | FK | CAST(manager_id AS STRING) |
| cost_center_code | STRING | FK | COALESCE(cost_center, 'UNKNOWN') |
| employment_category | STRING | Standardized | UPPER(employment_category) |
| union_flag | BOOL | Standardized | union_flag = 'Y' |
| **is_active** | BOOL | Computed | employment_status = 'ACTIVE' |
| **_dedup_rank** | INT64 | Dedup helper | ROW_NUMBER() OVER (...) |

**Deduplication Logic**:
```
ROW_NUMBER() OVER (
  PARTITION BY employee_id, effective_date 
  ORDER BY _load_timestamp DESC
) = 1
```

**FK Validation** (Great Expectations):
- `job_code` IN `stg_jobs.job_code`
- `cost_center_code` IN `stg_cost_centers.cost_center_code`
- `manager_id` IN `stg_employees.employee_id` (self-referential)

**Partitioning**: `PARTITION BY DATE_TRUNC(effective_date, MONTH)`  
**Clustering**: `CLUSTER BY employee_id, department_code`

---

#### **stg_timecards**

| Column | Type | Description | Transformation |
|--------|------|-------------|----------------|
| timecard_id | STRING | | timecard_id |
| employee_id | STRING | FK | employee_id |
| work_date | DATE | | work_date |
| punch_in_utc | TIMESTAMP | Timezone normalized | TIMESTAMP(punch_in, 'UTC') |
| punch_out_utc | TIMESTAMP | Timezone normalized | TIMESTAMP(punch_out, 'UTC') |
| hours_worked | NUMERIC | | COALESCE(hours_worked, 0) |
| hours_overtime | NUMERIC | | COALESCE(hours_overtime, 0) |
| hours_pto | NUMERIC | | COALESCE(hours_pto, 0) |
| approval_status | STRING | Standardized | UPPER(approval_status) |
| adjustment_flag | BOOL | | adjustment_flag |
| late_arrival_flag | BOOL | Late arriving fact | _load_date > work_date + 2 |
| **is_overtime** | BOOL | Computed | hours_overtime > 0 |

**Deduplication Logic**:
```
ROW_NUMBER() OVER (
  PARTITION BY timecard_id 
  ORDER BY _load_timestamp DESC
) = 1
```

**FK Validation**:
- `employee_id` IN `stg_employees.employee_id`

**Partitioning**: `PARTITION BY work_date`  
**Clustering**: `CLUSTER BY employee_id`

---

### **6.4 WAREHOUSE Layer (BigQuery) - Dimensional Model**

#### **dim_employee (SCD Type 2)**

**Grain**: One row per employee per change event (job, dept, etc.)

| Column | Type | Description |
|--------|------|-------------|
| **employee_key** | STRING | Surrogate key (hash) |
| **employee_id** | STRING | Business key |
| first_name | STRING | |
| last_name | STRING | |
| full_name | STRING | |
| age | INT64 | |
| national_identifier_hash | STRING | Masked PII |
| email_address | STRING | |
| hire_date | DATE | |
| termination_date | DATE | |
| employment_status | STRING | |
| job_code | STRING | |
| job_title | STRING | Denormalized |
| department_code | STRING | |
| department_name | STRING | Denormalized |
| location_code | STRING | |
| manager_id | STRING | |
| cost_center_code | STRING | |
| employment_category | STRING | |
| union_flag | BOOL | |
| **effective_from** | DATE | SCD2 effective start |
| **effective_to** | DATE | SCD2 effective end (9999-12-31 if current) |
| **is_current** | BOOL | SCD2 current flag |
| **row_hash** | STRING | SCD2 change detection hash |
| **_created_at** | TIMESTAMP | Audit |
| **_updated_at** | TIMESTAMP | Audit |

**SCD2 Logic**: Generated by **Module B: scd2-bq-engine**

**Partitioning**: `PARTITION BY DATE_TRUNC(effective_from, MONTH)`  
**Clustering**: `CLUSTER BY employee_id, department_code`

**Historical Scenarios**:
1. Employee promoted (job_code changes) → new row, old row closed
2. Employee transfers (department changes) → new row, old row closed
3. Employee rehired (termination_date → NULL) → new row
4. Email update (Type 1 column) → update in place, no new row

---

#### **dim_job (SCD Type 1)**

**Grain**: One row per job (overwrite on change)

| Column | Type | Description |
|--------|------|-------------|
| **job_key** | STRING | Surrogate key |
| **job_code** | STRING | Business key |
| job_title | STRING | |
| job_family | STRING | |
| job_level | INT64 | |
| pay_grade | STRING | |
| union_eligible | BOOL | |

**No partitioning** (small dimension, < 5K rows)

---

#### **dim_date (Calendar)**

**Grain**: One row per date

| Column | Type | Description |
|--------|------|-------------|
| **date_key** | DATE | |
| year | INT64 | |
| quarter | INT64 | |
| month | INT64 | |
| week | INT64 | |
| day_of_week | INT64 | |
| fiscal_year | INT64 | |
| fiscal_period | INT64 | |
| is_weekend | BOOL | |
| is_holiday | BOOL | |
| holiday_name | STRING | |
| region | STRING | US, EU, etc. |

**Pre-populated** for 10 years (2020-2030)

---

#### **dim_cost_center (SCD Type 1)**

**Grain**: One row per cost center

| Column | Type | Description |
|--------|------|-------------|
| **cost_center_key** | STRING | Surrogate key |
| **cost_center_code** | STRING | Business key |
| cost_center_name | STRING | |
| gl_account | STRING | |
| department | STRING | |
| location | STRING | |
| is_active | BOOL | |

---

#### **fact_payroll_run**

**Grain**: One row per employee per payroll run

| Column | Type | Description |
|--------|------|-------------|
| **employee_key** | STRING | FK to dim_employee |
| **run_date_key** | DATE | FK to dim_date |
| **cost_center_key** | STRING | FK to dim_cost_center |
| run_id | INT64 | Degenerate dimension |
| run_type | STRING | REGULAR, BONUS, ADJUSTMENT |
| gross_pay | NUMERIC | Additive measure |
| net_pay | NUMERIC | Additive measure |
| tax_federal | NUMERIC | Additive measure |
| tax_state | NUMERIC | Additive measure |
| tax_fica | NUMERIC | Additive measure |
| deduction_401k | NUMERIC | Additive measure |
| deduction_insurance | NUMERIC | Additive measure |
| hours_base | NUMERIC | Additive measure |
| hours_overtime | NUMERIC | Additive measure |
| **_created_at** | TIMESTAMP | Audit |

**Partitioning**: `PARTITION BY run_date_key`  
**Clustering**: `CLUSTER BY employee_key, cost_center_key`

**Late Arrival Handling**:
- MERGE statement using `(employee_key, run_date_key)` as unique key
- Re-process last 7 days on each run to capture adjustments

---

#### **fact_timecard**

**Grain**: One row per employee per shift

| Column | Type | Description |
|--------|------|-------------|
| **employee_key** | STRING | FK to dim_employee |
| **work_date_key** | DATE | FK to dim_date |
| timecard_id | STRING | Degenerate dimension |
| punch_in_utc | TIMESTAMP | |
| punch_out_utc | TIMESTAMP | |
| hours_scheduled | NUMERIC | Additive measure |
| hours_worked | NUMERIC | Additive measure |
| hours_overtime | NUMERIC | Additive measure |
| hours_pto | NUMERIC | Additive measure |
| late_arrival_flag | BOOL | Late arriving fact indicator |
| adjustment_flag | BOOL | Retro adjustment indicator |
| **_created_at** | TIMESTAMP | Audit |

**Partitioning**: `PARTITION BY work_date_key`  
**Clustering**: `CLUSTER BY employee_key`

**Late Arrival Handling**:
- Append-only pattern (no MERGE; duplicates handled via adjustment_flag)
- Marts filter for latest values using MAX(_created_at) window function
- Re-process last 7 days on each run

---

### **6.5 MARTS Layer (BigQuery) - Business-Ready**

#### **mart_payroll_costs**

**Grain**: cost_center + fiscal_period + department

| Column | Type | Description |
|--------|------|-------------|
| **cost_center_code** | STRING | |
| cost_center_name | STRING | |
| **fiscal_year** | INT64 | |
| **fiscal_period** | INT64 | |
| period_start_date | DATE | |
| period_end_date | DATE | |
| **department** | STRING | |
| headcount | INT64 | Distinct employees |
| total_gross_pay | NUMERIC | Sum of gross pay |
| total_net_pay | NUMERIC | Sum of net pay |
| total_taxes | NUMERIC | Sum of all taxes |
| total_deductions | NUMERIC | Sum of all deductions |
| total_hours_base | NUMERIC | Sum of regular hours |
| total_hours_overtime | NUMERIC | Sum of OT hours |
| avg_pay_per_employee | NUMERIC | total_gross_pay / headcount |
| cost_per_labor_hour | NUMERIC | total_gross_pay / (total_hours_base + total_hours_overtime) |
| overtime_pct | NUMERIC | total_hours_overtime / total_hours_base |
| yoy_growth_pct | NUMERIC | YoY growth in total_gross_pay |

**Refresh**: Daily incremental (append current period)  
**Privacy**: Aggregated (no individual PII)  
**Access**: Finance, HR, Operations

---

#### **mart_overtime_trends**

**Grain**: department + location + week (anonymized) OR employee + week (restricted)

**Anonymized Version** (default access):

| Column | Type | Description |
|--------|------|-------------|
| **department** | STRING | |
| **location** | STRING | |
| **week_start_date** | DATE | |
| employee_count | INT64 | Employees in cohort (≥10 for k-anonymity) |
| avg_hours_worked | NUMERIC | Average total hours |
| avg_hours_overtime | NUMERIC | Average OT hours |
| pct_employees_with_ot | NUMERIC | % with any OT |
| pct_employees_exceeding_threshold | NUMERIC | % with >10 hrs OT/week |
| total_overtime_cost | NUMERIC | Estimated OT cost |

**Employee-Level Version** (HR-only access):

| Column | Type | Description |
|--------|------|-------------|
| **employee_id** | STRING | |
| employee_name | STRING | |
| **week_start_date** | DATE | |
| department | STRING | |
| total_hours_worked | NUMERIC | |
| total_hours_overtime | NUMERIC | |
| overtime_pct | NUMERIC | OT / total hours |
| threshold_breach_flag | BOOL | >10 hrs OT/week |
| consecutive_breach_weeks | INT64 | Rolling count |

**Refresh**: Daily  
**Privacy**: Two-tier (anonymized default, employee-level restricted)

---

#### **mart_headcount_workforce**

**Grain**: department + location + date

| Column | Type | Description |
|--------|------|-------------|
| **snapshot_date** | DATE | |
| **department** | STRING | |
| **location** | STRING | |
| active_headcount | INT64 | Employees with status=ACTIVE |
| full_time_count | INT64 | |
| part_time_count | INT64 | |
| contractor_count | INT64 | |
| union_count | INT64 | |
| new_hires_mtd | INT64 | Hires this month |
| terminations_mtd | INT64 | Terms this month |
| turnover_rate_annual | NUMERIC | Annualized turnover % |
| avg_tenure_years | NUMERIC | |
| headcount_change_mom | INT64 | Month-over-month change |

**Refresh**: Daily snapshot  
**Privacy**: Aggregated by dept/location (no individual data)

---

#### **mart_privacy_anonymized**

**Purpose**: Public-tier dataset with maximum aggregation for broad access

**Grain**: Multiple aggregated views (dept-level, location-level, time-series)

**Example: Aggregated Payroll by Department**

| Column | Type | Description |
|--------|------|-------------|
| **department** | STRING | |
| **fiscal_period** | STRING | YYYY-Qn |
| employee_count_bucket | STRING | "10-50", "51-100", etc. |
| avg_gross_pay | NUMERIC | Rounded to nearest $1000 |
| total_payroll_bucket | STRING | "$100K-$500K", etc. |
| avg_hours_per_employee | NUMERIC | |

**Privacy Rules**:
- No cells with < 10 employees (suppress or bucket)
- All dollar amounts rounded/bucketed
- No temporal precision < quarter
- No geographic precision < region

**Access**: All employees (public tier)

---

### **6.6 Data Model ERD (Text Representation)**

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WAREHOUSE STAR SCHEMA                       │
└─────────────────────────────────────────────────────────────────────┘

         ┌─────────────────┐
         │   dim_date      │
         │─────────────────│
         │ date_key (PK)   │
         │ year            │
         │ quarter         │
         │ fiscal_period   │
         │ is_holiday      │
         └────────┬────────┘
                  │
                  │ run_date_key, work_date_key
                  │
         ┌────────▼───────────────────────────────────┐
         │                                            │
┌────────┴────────┐                         ┌────────┴────────┐
│ dim_employee    │                         │ dim_cost_center │
│─────────────────│                         │─────────────────│
│ employee_key(PK)│◄────────────┐           │ cost_center_key │
│ employee_id(BK) │             │           │ cost_center_code│
│ job_code        │◄──┐         │           │ gl_account      │
│ dept, location  │   │         │           │ department      │
│ effective_from  │   │         │           └────────▲────────┘
│ effective_to    │   │         │                    │
│ is_current (SCD2)   │         │                    │ cost_center_key
└─────────────────┘   │         │                    │
                      │         │           ┌────────┴───────────────┐
         ┌────────────┴───┐     │           │  fact_payroll_run      │
         │   dim_job      │     │           │────────────────────────│
         │────────────────│     │           │ employee_key (FK)      │
         │ job_key (PK)   │     │           │ run_date_key (FK)      │
         │ job_code (BK)  │     │           │ cost_center_key (FK)   │
         │ job_title      │     │           │ run_id (DD)            │
         │ pay_grade      │     │           │ gross_pay              │
         │ union_eligible │     │           │ net_pay, taxes         │
         └────────────────┘     │           │ hours_base, hours_ot   │
                                │           └────────────────────────┘
                                │
                                │           ┌────────────────────────┐
                                │           │  fact_timecard         │
                                │           │────────────────────────│
                                └───────────│ employee_key (FK)      │
                                            │ work_date_key (FK)     │
                                            │ timecard_id (DD)       │
                                            │ hours_worked           │
                                            │ hours_overtime         │
                                            │ late_arrival_flag      │
                                            └────────────────────────┘

Legend:
  PK = Primary Key
  BK = Business Key
  FK = Foreign Key
  DD = Degenerate Dimension
  ◄─ = Foreign key relationship
```

**Key Relationships**:
1. `fact_payroll_run` → `dim_employee` (many-to-one)
2. `fact_payroll_run` → `dim_date` (many-to-one)
3. `fact_payroll_run` → `dim_cost_center` (many-to-one)
4. `fact_timecard` → `dim_employee` (many-to-one)
5. `fact_timecard` → `dim_date` (many-to-one)
6. `dim_employee` → `dim_job` (many-to-one via job_code)

**Conformed Dimensions**:
- `dim_date`: Shared across all facts
- `dim_employee`: Shared across payroll and timecard facts

---

## **7. DATAOPS & RELIABILITY PLAN**

### **7.1 CI/CD Pipeline Architecture**

**Pipeline Stages**:

```
┌──────────────────────────────────────────────────────────────────────┐
│ CONTINUOUS INTEGRATION (on push to feature branch)                   │
└──────────────────────────────────────────────────────────────────────┘
  │
  ├─► 1. LINT
  │      - SQL linting (SQLFluff)
  │      - Python linting (Black, Flake8)
  │      - YAML validation (yamllint)
  │      - Dataform compile check
  │      Duration: 2-3 min
  │
  ├─► 2. UNIT TESTS
  │      - SQL unit tests (dbt-utils style tests on staging logic)
  │      - Python unit tests (Airflow DAG validation, module tests)
  │      - Mock data tests (use Module A synthetic data)
  │      Duration: 5-7 min
  │
  ├─► 3. DATAFORM COMPILE
  │      - Compile all SQLX to SQL
  │      - Validate dependency graph (no cycles)
  │      - Check for schema references
  │      Duration: 1-2 min
  │
  └─► 4. SECURITY SCAN
         - Secrets scanning (no hardcoded creds)
         - Dependency vulnerability scan (Snyk/Dependabot)
         Duration: 2-3 min

         ✅ CI passes → Ready for PR review

┌──────────────────────────────────────────────────────────────────────┐
│ CONTINUOUS DEPLOYMENT (on merge to main → deploy to DEV)             │
└──────────────────────────────────────────────────────────────────────┘
  │
  ├─► 5. DEPLOY TO DEV
  │      - Deploy Dataform definitions to dev project
  │      - Update Airflow DAGs (local or dev GKE)
  │      - Tag BQ datasets with deployment metadata
  │      Duration: 3-5 min
  │
  ├─► 6. INTEGRATION TESTS
  │      - Run end-to-end DAG on synthetic data (Module A)
  │      - Verify data flows through all layers (raw → staging → warehouse → marts)
  │      - Check row counts, schema compliance
  │      Duration: 15-20 min
  │
  ├─► 7. GREAT EXPECTATIONS CHECKPOINTS
  │      - Run all DQ checkpoints on dev data
  │      - Validate expectations pass rates ≥90%
  │      - Generate DQ report
  │      Duration: 5-8 min
  │
  ├─► 8. SMOKE TESTS
  │      - Query each mart, verify non-zero results
  │      - Validate SCD2 logic (check for overlaps, gaps)
  │      - Test late arrival handling (inject late records)
  │      Duration: 5-7 min
  │
  └─► 9. PUBLISH ARTIFACTS
         - Update Data Catalog metadata
         - Generate lineage diagram
         - Publish deployment report to Slack/wiki
         Duration: 2-3 min

         ✅ All checks pass → Auto-deploy to TEST

┌──────────────────────────────────────────────────────────────────────┐
│ PRODUCTION DEPLOYMENT (manual approval → deploy to PROD)             │
└──────────────────────────────────────────────────────────────────────┘
  │
  ├─► 10. PRE-PROD SNAPSHOT
  │       - Create BQ snapshots of prod warehouse/marts
  │       - Backup current Dataform config
  │       - Record baseline metrics (row counts, query costs)
  │       Duration: 5-10 min
  │
  ├─► 11. DEPLOY TO PROD
  │       - Deploy Dataform to prod (blue/green pattern)
  │       - Update Airflow DAGs
  │       - Enable prod pipelines
  │       Duration: 5-7 min
  │
  ├─► 12. POST-DEPLOY VALIDATION
  │       - Run Great Expectations checkpoints on prod
  │       - Validate metric reconciliation (vs. legacy system)
  │       - Check query performance (compare to baseline)
  │       Duration: 10-15 min
  │
  └─► 13. MONITOR & ALERT
          - Enable SLA monitors (Airflow)
          - Enable cost alerts (Module D)
          - Enable freshness monitors (Data Catalog)
          Duration: 2-3 min

          ✅ Validation passes → Deployment complete
          ❌ Validation fails → Auto-rollback to snapshot
```

**Total Pipeline Duration**:
- CI: ~15 min
- CD to Dev: ~45 min
- CD to Prod: ~35 min (after manual approval)

---

### **7.2 Great Expectations Integration**

**Checkpoint Placement Strategy**:

| Layer | Checkpoint | Validations | Fail Policy |
|-------|-----------|-------------|-------------|
| **Landing (GCS)** | `landing_files_checkpoint` | - File arrival completeness<br>- File size within expected range<br>- Row count vs manifest | Alert only (don't block) |
| **Raw** | `raw_ingestion_checkpoint` | - Row count delta < 50% vs previous day<br>- No nulls in PK columns<br>- Schema matches expected | Fail if >5% violations |
| **Staging** | `staging_dq_checkpoint` | - FK integrity (all employee_ids exist)<br>- No duplicates on business key<br>- Date ranges valid (hire_date < termination_date)<br>- Codes in approved list | Fail if >5% violations |
| **Warehouse** | `warehouse_integrity_checkpoint` | - SCD2 no overlaps<br>- Fact/dim FK integrity<br>- Additive measures non-negative<br>- No orphaned facts | Fail if >1% violations |
| **Marts** | `mart_reconciliation_checkpoint` | - Headcount matches dim_employee<br>- Payroll totals match fact_payroll_run<br>- Metric consistency (finance vs HR) | Fail if >2% variance |

**Checkpoint Configuration Example** (pseudo-YAML):

```yaml
# checkpoints/staging_dq_checkpoint.yml
name: staging_dq_checkpoint
config_version: 1.0

validations:
  - expectation_suite_name: staging_employees_suite
    batch_request:
      datasource_name: bigquery_datasource
      data_asset_name: payroll_staging_dev.stg_employees
    action_list:
      - name: store_validation_result
        action:
          class_name: StoreValidationResultAction
      - name: update_data_docs
        action:
          class_name: UpdateDataDocsAction
      - name: fail_on_violation
        action:
          class_name: ValidationOperatorAction
          threshold: 0.05  # Fail if >5% rows violate

expectation_suites:
  staging_employees_suite:
    - expectation_type: expect_column_values_to_not_be_null
      kwargs:
        column: employee_id
    - expectation_type: expect_column_values_to_be_unique
      kwargs:
        column: [employee_id, effective_date]
    - expectation_type: expect_column_values_to_be_in_set
      kwargs:
        column: employment_status
        value_set: [ACTIVE, TERMINATED, LOA, SUSPENDED]
    - expectation_type: expect_column_pair_values_A_to_be_less_than_or_equal_to_B
      kwargs:
        column_A: hire_date
        column_B: termination_date
        or_equal: true
        mostly: 0.99  # Allow 1% exceptions
    - expectation_type: expect_column_values_to_be_in_set
      kwargs:
        column: job_code
        value_set:
          ref_table: payroll_staging_dev.stg_jobs
          ref_column: job_code
```

**Airflow Integration** (pseudo-code):

```python
# airflow/dags/payroll_staging.py
from great_expectations_provider.operators.great_expectations import GreatExpectationsOperator

staging_dq_task = GreatExpectationsOperator(
    task_id='staging_dq_validation',
    data_context_root_dir='../config/great_expectations',
    checkpoint_name='staging_dq_checkpoint',
    fail_task_on_validation_failure=True,  # Fail pipeline if DQ fails
    return_json_dict=True
)

# Pipeline flow
load_staging_task >> staging_dq_task >> build_warehouse_task
```

---

### **7.3 Alerting & Runbook**

**Alert Levels**:

| Severity | Trigger | Notification | SLA |
|----------|---------|--------------|-----|
| **P0 - Critical** | - Pipeline failure blocking payroll close<br>- Data quality <80% pass rate<br>- Complete source file missing | - PagerDuty (on-call)<br>- Slack #data-eng-alerts<br>- Email to DE lead | 15 min response |
| **P1 - High** | - Pipeline delay >90 min<br>- DQ failure in staging/warehouse<br>- Metric variance >10% vs baseline | - Slack #data-eng-alerts<br>- Email to team | 1 hour response |
| **P2 - Medium** | - Single table failure (non-blocking)<br>- Query cost spike >2x avg<br>- Late arriving facts >20% | - Slack #data-eng-monitoring<br>- Daily digest | 4 hour response |
| **P3 - Low** | - Schema drift detected<br>- File arrival delayed <1 hour<br>- Individual DQ test failure | - Slack #data-eng-monitoring | Next business day |

**Runbook Structure** (docs/runbook.md):

```markdown
# Payroll Data Pipeline Runbook

## Common Incidents

### 1. Pipeline Failure: Raw Ingestion

**Symptoms**: Airflow task `load_raw_employees` fails

**Diagnosis**:
1. Check GCS landing bucket for file arrival
2. Verify file format matches schema
3. Check BigQuery quota/permissions

**Resolution**:
- If file missing → Contact source system team, backfill when available
- If schema mismatch → Update raw table schema, re-run
- If quota exceeded → Request quota increase, pause non-critical pipelines

**Rollback**: Delete failed partition, re-run Airflow task

---

### 2. Data Quality Failure: Staging FK Violations

**Symptoms**: Great Expectations checkpoint fails on FK validation

**Diagnosis**:
1. Query staging table for orphaned records
2. Trace back to raw layer source
3. Check for source system data issues

**Resolution**:
- If orphaned records <5% → Quarantine to `stg_employees_quarantine`, continue pipeline
- If >5% → Halt pipeline, escalate to source system team
- If lookup table stale → Refresh dimension, re-run staging

**Rollback**: Not applicable (staging is transient)

---

### 3. SCD2 Overlap Detected

**Symptoms**: Warehouse checkpoint fails on overlap detection

**Diagnosis**:
1. Query dim_employee for overlaps: WHERE effective_to > effective_from of next row
2. Identify affected employee_ids
3. Check for concurrent updates or late arrivals

**Resolution**:
- Run SCD2 repair script (Module B includes repair utility)
- Re-process affected employee_ids with correct effective dates
- Validate no overlaps remain

**Rollback**: Restore dim_employee from pre-deployment snapshot

---

### 4. Metric Reconciliation Failure

**Symptoms**: Mart checkpoint fails: headcount variance >2%

**Diagnosis**:
1. Compare mart_headcount_workforce to dim_employee count
2. Check for late arriving terminations
3. Verify SCD2 is_current flag logic

**Resolution**:
- If late arrivals → Re-run warehouse build with extended lookback
- If logic error → Fix mart query, redeploy, backfill
- If dimension issue → Rebuild dim_employee, cascade to marts

**Rollback**: Restore marts from snapshot, investigate root cause

---

## Escalation Path

1. On-call Data Engineer (P0/P1)
2. Data Engineering Lead (if >2 hours unresolved)
3. Platform Engineering (infrastructure issues)
4. Source System Owners (data quality issues)
```

---

### **7.4 Idempotency & Backfill Strategy**

**Idempotency Guarantees**:

1. **Raw Ingestion**: 
   - Load partitions by `load_date`
   - Overwrite partition if re-run (idempotent)
   - No duplicates within partition

2. **Staging**:
   - Full refresh daily (or incremental with dedup)
   - Deterministic dedup logic (ROW_NUMBER by _load_timestamp DESC)
   - Safe to re-run any partition

3. **Warehouse (SCD2)**:
   - Lookback window (90 days) allows late arrivals
   - Hash-based change detection (deterministic)
   - Safe to re-run; will correct overlaps/gaps

4. **Facts**:
   - `fact_payroll_run`: MERGE on (employee_key, run_date) → upsert idempotent
   - `fact_timecard`: Append with _created_at → filter for latest in marts

5. **Marts**:
   - Incremental append with partition overwrite
   - Safe to re-run any partition

**Backfill Utility** (scripts/utilities/backfill.sh):

```bash
#!/bin/bash
# Usage: ./backfill.sh <start_date> <end_date> <layer>
# Example: ./backfill.sh 2024-01-01 2024-01-31 staging

START_DATE=$1
END_DATE=$2
LAYER=$3

echo "Backfilling $LAYER from $START_DATE to $END_DATE"

# Trigger Airflow DAG runs for each date
current_date=$START_DATE
while [ "$current_date" != "$END_DATE" ]; do
  echo "Triggering run for $current_date"
  
  airflow dags trigger payroll_${LAYER} \
    --conf "{\"load_date\": \"$current_date\"}" \
    --run-id "backfill_${current_date}"
  
  # Increment date
  current_date=$(date -I -d "$current_date + 1 day")
  
  # Rate limit (don't overwhelm BQ)
  sleep 10
done

echo "Backfill complete. Monitor Airflow UI for status."
```

---

### **7.5 Rollback Strategy**

**Rollback Mechanisms**:

| Component | Rollback Method | Recovery Time |
|-----------|----------------|---------------|
| **Dataform Code** | Git revert + redeploy | 5-10 min |
| **BigQuery Data** | Restore from snapshot | 10-20 min |
| **Airflow DAGs** | Git revert + redeploy | 5 min |
| **Config Files** | Git revert | 2 min |

**Snapshot Strategy**:

```sql
-- Automated pre-deployment snapshot (via Terraform/script)
CREATE SNAPSHOT TABLE `payroll_warehouse_prod.dim_employee_snapshot_20250123`
CLONE `payroll_warehouse_prod.dim_employee`;

-- Retention: 7 days (automatic expiration)
```

**Rollback Procedure**:

1. **Identify Bad Deployment**: Version tag, timestamp
2. **Stop Running Pipelines**: Pause Airflow DAGs
3. **Restore BQ Snapshots**:
   ```bash
   bq cp --force payroll_warehouse_prod.dim_employee_snapshot_20250123 \
         payroll_warehouse_prod.dim_employee
   ```
4. **Revert Code**: `git revert <bad_commit>` → redeploy
5. **Validate**: Run smoke tests
6. **Resume Pipelines**: Unpause Airflow DAGs
7. **Post-Mortem**: Document root cause, prevention

---

### **7.6 Data Contracts**

**Contract Definition** (YAML):

```yaml
# config/data_contracts/stg_employees_contract.yaml
contract:
  name: stg_employees
  version: 1.2.0
  owner: data-engineering-team
  
  schema:
    - name: employee_id
      type: STRING
      required: true
      description: "Unique employee identifier"
      tests:
        - not_null
        - unique_combination_with: [effective_date]
    
    - name: effective_date
      type: DATE
      required: true
      description: "Effective date of employee record"
      tests:
        - not_null
        - valid_date_range:
            min: "2020-01-01"
            max: "2030-12-31"
    
    - name: employment_status
      type: STRING
      required: true
      allowed_values: [ACTIVE, TERMINATED, LOA, SUSPENDED]
    
    - name: job_code
      type: STRING
      required: true
      foreign_key:
        table: stg_jobs
        column: job_code
  
  sla:
    freshness: "T+1 by 9 AM"
    completeness: ">95% of expected rows"
    validity: ">90% pass DQ tests"
  
  breaking_changes:
    notify:
      - data-engineering-team@company.com
      - analytics-team@company.com
    approval_required: true

  changelog:
    - version: 1.2.0
      date: 2025-01-15
      changes: "Added national_identifier_hash column"
      breaking: false
    
    - version: 1.1.0
      date: 2024-12-01
      changes: "Changed employment_status from codes to names"
      breaking: true
```

**Contract Enforcement**:
- Automatically validated by Great Expectations
- Breaking changes require approval via PR review
- Version tracked in Data Catalog

---

### **7.7 Observability: Freshness & Pipeline Health**

**SLI/SLO Definitions**:

| Metric (SLI) | Target (SLO) | Measurement | Alert Threshold |
|--------------|--------------|-------------|-----------------|
| **Data Freshness** | T+0 by 9 AM | Airflow DAG completion time | >9:30 AM |
| **Pipeline Success Rate** | >99% daily | Airflow task success % | <95% |
| **DQ Pass Rate** | >90% | Great Expectations pass % | <85% |
| **Query Performance** | p95 < 10s | BQ audit logs | p95 >20s |
| **Cost per Mart** | <$5/day | Module D cost tracking | >$10/day |
| **Metric Reconciliation** | <2% variance | Cross-system comparison | >5% variance |

**Monitoring Dashboard** (Cloud Monitoring or Grafana):

```
┌────────────────────────────────────────────────────────────┐
│ Payroll Pipeline Health Dashboard                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│ ⏰ Freshness SLA: ████████████░░ 91% on-time (7d avg)     │
│                                                            │
│ 📊 Pipeline Success Rate: ████████████████ 98.5% (7d avg) │
│                                                            │
│ ✅ DQ Pass Rate: ██████████████ 93% (today)               │
│                                                            │
│ 💰 Daily Cost: $47.50 (budget: $50)                       │
│                                                            │
│ 📈 Row Counts (today):                                    │
│   - raw_employees: 50,234 ✓                               │
│   - stg_employees: 49,987 ✓                               │
│   - dim_employee: 125,432 ✓ (+234 new rows)              │
│   - fact_payroll_run: 2.1M ✓                              │
│                                                            │
│ 🚨 Active Alerts: 1 (P2 - late arriving timecards 18%)   │
│                                                            │
│ ⏱️ Last Successful Run: 2025-01-23 08:47 AM (22 min)      │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## **8. FINOPS PLAN**

### **8.1 Partition & Clustering Strategy**

**Per-Layer Strategy**:

| Layer | Partitioning | Clustering | Rationale |
|-------|--------------|------------|-----------|
| **Raw** | BY `_load_date` | BY PK (employee_id, run_id) | Time-travel debugging, efficient backfills |
| **Staging** | BY `effective_date` or `work_date` (MONTH granularity) | BY business_key + FK | Align with business queries, reduce staging scans |
| **Warehouse (Dims)** | BY `DATE_TRUNC(effective_from, MONTH)` | BY business_key + frequently filtered attrs | Efficient SCD2 lookups |
| **Warehouse (Facts)** | BY `run_date` or `work_date` (DAY granularity) | BY FK columns (employee_key, cost_center_key) | Align with BI queries ("last month payroll") |
| **Marts** | BY `snapshot_date` or `fiscal_period` | BY aggregation keys (dept, location) | Pre-aggregated, fast BI queries |

**Cost Impact**:
- Partition pruning: 60-80% reduction in bytes scanned
- Clustering: Additional 20-40% reduction on filtered queries

**Example**:
```sql
-- Before optimization
SELECT SUM(gross_pay) 
FROM fact_payroll_run 
WHERE employee_key = 'emp_12345';
-- Scans: 500 GB (entire table)

-- After partitioning + clustering
SELECT SUM(gross_pay) 
FROM fact_payroll_run 
WHERE run_date >= '2024-01-01' AND employee_key = 'emp_12345';
-- Scans: 2 GB (1 year partition + clustered on employee_key)
-- Cost reduction: 99.6%
```

---

### **8.2 Retention Strategy**

| Layer/Dataset | Retention Policy | TTL Implementation | Cost Savings |
|---------------|------------------|---------------------|--------------|
| **Landing (GCS)** | 90 days | Object Lifecycle Policy | ~$50/month |
| **Raw** | 90 days | BQ partition expiration | ~$100/month |
| **Staging** | 30 days | BQ partition expiration | ~$80/month |
| **Warehouse** | 7 years (compliance) | No expiration | N/A |
| **Marts** | 3 years | BQ partition expiration | ~$150/month |
| **Snapshots** | 7 days | Automated cleanup script | ~$20/month |

**Total Retention Savings**: ~$400/month

**Implementation** (Terraform):

```hcl
# terraform/modules/bigquery/main.tf
resource "google_bigquery_table" "raw_employees" {
  dataset_id = google_bigquery_dataset.payroll_raw.dataset_id
  table_id   = "raw_employees"
  
  time_partitioning {
    type          = "DAY"
    field         = "_load_date"
    expiration_ms = 7776000000  # 90 days
  }
  
  clustering = ["employee_number"]
}
```

---

### **8.3 Labeling & Cost Attribution**

**Tagging Strategy**:

| Resource | Labels | Purpose |
|----------|--------|---------|
| **BQ Datasets** | `team`, `cost_center`, `env`, `layer` | Dept-level cost allocation |
| **BQ Tables** | `domain`, `pii_tier`, `owner` | Data governance + cost drill-down |
| **Airflow Jobs** | `pipeline`, `layer` | Pipeline-level cost tracking |
| **Queries** | `user`, `tool` (Tableau/Airflow) | User/tool attribution |

**Example Labels**:
```json
{
  "team": "finance",
  "cost_center": "cc-1234",
  "env": "prod",
  "layer": "marts",
  "domain": "payroll",
  "pii_tier": "anonymized"
}
```

**Cost Attribution Report** (via Module D):

```bash
$ bq-finops labels --project payroll-analytics-prod --label team --start-date 2024-11-01

┌─────────────┬──────────────┬──────────────┬───────────────────┐
│ Team        │ Bytes Scanned│ Est Cost ($) │ Top Dataset       │
├─────────────┼──────────────┼──────────────┼───────────────────┤
│ finance     │ 12.3 TB      │ $61.50       │ payroll_marts     │
│ hr          │ 8.7 TB       │ $43.50       │ payroll_warehouse │
│ operations  │ 20.5 TB      │ $102.50      │ payroll_staging   │
│ analytics   │ 15.2 TB      │ $76.00       │ payroll_marts     │
└─────────────┴──────────────┴──────────────┴───────────────────┘

💡 Insight: Operations team driving highest cost due to raw data queries.
   Recommendation: Migrate to staging/marts for aggregated access.
```

---

### **8.4 Before/After Optimization Plan**

**Baseline (Before)**:

| Metric | Value |
|--------|-------|
| Monthly BQ cost | $22,000 |
| Avg query cost | $3.50 |
| Bytes scanned/month | 450 TB |
| Top cost drivers | - Unpartitioned raw table scans<br>- SELECT * queries<br>- Repeated full-refresh materializations |
| Waste estimate | ~65% avoidable spend |

**Optimized (After)**:

| Metric | Value | Improvement |
|--------|-------|-------------|
| Monthly BQ cost | $8,500 | 61% reduction |
| Avg query cost | $1.20 | 66% reduction |
| Bytes scanned/month | 180 TB | 60% reduction |
| Top optimizations | - Partitioning + clustering<br>- Marts pre-aggregation<br>- Incremental models |
| Waste eliminated | $13,500/month | |

**Optimization Tracking** (via Module D):

```bash
$ bq-finops optimize track \
    --table payroll_warehouse_prod.fact_payroll_run \
    --change "Added PARTITION BY run_date, CLUSTER BY (employee_key, cost_center_key)" \
    --compare-days 30

📊 Optimization Impact:
    Before: 15.2 TB scanned/month, $76.00
    After:  6.1 TB scanned/month, $30.50
    Savings: 60% reduction, $45.50/month
    
    Queries affected: 1,234
    Avg query speedup: 3.2x faster
```

**Continuous Optimization**:
- Weekly anti-pattern detection (Module D automated scans)
- Monthly cost review meetings (share reports with stakeholders)
- Quarterly optimization sprints (tackle top offenders)

---

### **8.5 Cost Metrics to Publish**

**Monthly FinOps Report**:

```markdown
# Payroll Data Platform FinOps Report - January 2025

## Summary
- **Total Cost**: $8,743 (budget: $10,000) ✅
- **Cost per Query**: $1.18 avg (target: <$1.50) ✅
- **Bytes Scanned**: 187 TB (down 58% from baseline)
- **Wasted Spend**: <5% (excellent)

## Cost by Layer
| Layer | Cost | % of Total | Change MoM |
|-------|------|------------|------------|
| Raw | $1,200 | 14% | -5% (retention optimized) |
| Staging | $2,100 | 24% | -3% |
| Warehouse | $3,500 | 40% | -2% |
| Marts | $1,800 | 21% | +2% (new marts added) |
| Other | $143 | 1% | -- |

## Cost by Team
| Team | Cost | Top User | Top Table |
|------|------|----------|-----------|
| Finance | $2,450 | analyst1@ | mart_payroll_costs |
| HR | $1,850 | hrmanager@ | mart_headcount_workforce |
| Operations | $3,200 | ops_lead@ | fact_timecard (needs optimization) |
| Analytics | $1,100 | datascientist@ | Various marts |

## Top Optimization Opportunities
1. **Operations team raw queries** (est. $800/mo savings)
   - Action: Migrate to staging/marts
2. **Repeated full-refresh of dim_job** (est. $200/mo savings)
   - Action: Switch to incremental (Type 1 dim, rarely changes)
3. **Unfiltered timecard queries** (est. $400/mo savings)
   - Action: Enforce partition filters in BI tool

## Actions Taken
- ✅ Added clustering to fact_payroll_run ($450/mo saved)
- ✅ Enabled partition expiration on staging tables ($80/mo saved)
- ✅ Migrated 3 heavy users to marts ($300/mo saved)

## Next Month Goals
- Reduce operations team cost by 30% via training
- Implement query cost budget alerts ($50/day threshold)
- Publish cost-conscious query patterns to wiki
```

---

## **9. PRIVACY / PII GOVERNANCE PLAN**

### **9.1 PII Classification**

**Categories (CIPT-aligned)**:

| Tier | Data Elements | Examples | Access Level |
|------|---------------|----------|--------------|
| **Tier 0: Public** | Aggregated, anonymized | - Dept-level payroll totals<br>- Headcount by location | All employees |
| **Tier 1: Internal** | Business data, no PII | - Job codes, cost centers<br>- Aggregated metrics (k≥10) | Analytics team, managers |
| **Tier 2: Sensitive** | Indirect identifiers | - Masked employee IDs<br>- Hashed SSNs<br>- Aggregated employee-level (HR only) | HR, Finance, Data Eng |
| **Tier 3: Restricted** | Direct PII | - Names, SSNs, DOB<br>- Bank account numbers<br>- Addresses, phone numbers | Data Eng, Audit only |

**Mapping to Layers**:

| Layer | Default Tier | PII Handling |
|-------|--------------|--------------|
| Raw | Tier 3 (Restricted) | Contains full PII; strict IAM |
| Staging | Tier 3 (Restricted) | PII hashed/masked during transformation |
| Warehouse | Tier 2 (Sensitive) | Indirect identifiers only; direct PII dropped or hashed |
| Marts | Tier 1 (Internal) or Tier 0 (Public) | Aggregated; no individual-level data |

---

### **9.2 Tiered Dataset Strategy**

**Architecture**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRIVACY-TIERED ACCESS                            │
└─────────────────────────────────────────────────────────────────────┘

Tier 3: RESTRICTED                  Access: Data Eng + Audit (5 users)
┌──────────────────────────────────────────────────────────────────┐
│ payroll_raw_prod                  payroll_staging_prod           │
│ - raw_employees (with SSN)        - stg_employees (SSN hashed)   │
│ - raw_timecards                   - stg_timecards                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ Transform & Mask
                              ▼
Tier 2: SENSITIVE                   Access: HR + Finance (20 users)
┌──────────────────────────────────────────────────────────────────┐
│ payroll_warehouse_prod                                           │
│ - dim_employee (national_identifier_hash, names visible)        │
│ - fact_payroll_run (employee-level, no SSN)                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ Aggregate & Denormalize
                              ▼
Tier 1: INTERNAL                    Access: Managers + Analytics (100 users)
┌──────────────────────────────────────────────────────────────────┐
│ payroll_marts_prod                                               │
│ - mart_payroll_costs (dept-level)                               │
│ - mart_overtime_trends (aggregated k≥10)                        │
│ - mart_headcount_workforce (dept/location)                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              │ Anonymize
                              ▼
Tier 0: PUBLIC                      Access: All employees (5,000 users)
┌──────────────────────────────────────────────────────────────────┐
│ payroll_marts_public                                             │
│ - mart_privacy_anonymized (bucketed, rounded, k≥10)             │
└──────────────────────────────────────────────────────────────────┘
```

---

### **9.3 Masking Rules**

**Masking Techniques**:

| PII Field | Raw (Tier 3) | Warehouse (Tier 2) | Marts (Tier 1/0) |
|-----------|--------------|-------------------|------------------|
| SSN / National ID | `123-45-6789` | `SHA256 hash` | Not included |
| Employee Name | `John Smith` | `John Smith` | Not included or bucketed ("10-50 employees in Engineering") |
| DOB | `1985-03-15` | Age (40) | Age bucket ("35-45") |
| Salary | `$85,000` | `$85,000` | Rounded (`$85K`) or bucketed ("$80K-$90K") |
| Bank Account | `123456789` | Tokenized or dropped | Not included |
| Address | `123 Main St, City, ST 12345` | Zip code only (`12345`) | City or region |
| Email | `john.smith@company.com` | `john.smith@company.com` | Not included |
| Phone | `555-123-4567` | Masked (`555-***-****`) | Not included |

**Implementation** (SQL UDFs):

```sql
-- Warehouse layer: Mask SSN
CREATE OR REPLACE FUNCTION payroll_warehouse_prod.mask_ssn(ssn STRING)
RETURNS STRING AS (
  TO_HEX(SHA256(CONCAT(ssn, 'salt_key_from_secret_manager')))
);

-- Marts layer: Age bucketing
CREATE OR REPLACE FUNCTION payroll_marts_prod.age_bucket(age INT64)
RETURNS STRING AS (
  CASE
    WHEN age < 25 THEN '18-24'
    WHEN age < 35 THEN '25-34'
    WHEN age < 45 THEN '35-44'
    WHEN age < 55 THEN '45-54'
    WHEN age < 65 THEN '55-64'
    ELSE '65+'
  END
);

-- Marts layer: K-anonymity enforcement
-- Suppress any group with < 10 employees
SELECT
  department,
  location,
  COUNT(*) AS employee_count,
  CASE
    WHEN COUNT(*) < 10 THEN NULL  -- Suppress
    ELSE AVG(gross_pay)
  END AS avg_gross_pay
FROM payroll_warehouse_prod.dim_employee
WHERE is_current = TRUE
GROUP BY 1, 2;
```

---

### **9.4 Least-Privilege Access Model**

**IAM Roles** (GCP):

| Role | Scope | Permissions | Assigned To |
|------|-------|-------------|-------------|
| **Data Engineer** | All datasets | - Read/write all layers<br>- Admin on dev/test<br>- Write on prod (via CI/CD) | Data eng team (5 users) |
| **Analytics Engineer** | Staging + Warehouse | - Read staging/warehouse<br>- Write warehouse (dev only)<br>- No raw access | Analytics eng team (8 users) |
| **HR Analyst** | Warehouse + Marts (sensitive) | - Read warehouse (employee-level)<br>- Read marts (all) | HR team (12 users) |
| **Finance Analyst** | Marts (cost-focused) | - Read marts (payroll costs)<br>- No employee-level access | Finance team (15 users) |
| **Business User** | Marts (anonymized) | - Read public marts only | All employees (5,000 users) |
| **Audit** | All datasets (read-only) | - Read all layers<br>- No write access | Audit team (2 users) |

**IAM Policy** (Terraform):

```hcl
# terraform/modules/iam/main.tf

# Tier 3: Raw (Restricted)
resource "google_bigquery_dataset_iam_member" "raw_data_engineer" {
  dataset_id = google_bigquery_dataset.payroll_raw_prod.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:data-engineering@company.com"
}

# Tier 2: Warehouse (Sensitive)
resource "google_bigquery_dataset_iam_member" "warehouse_hr" {
  dataset_id = google_bigquery_dataset.payroll_warehouse_prod.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:hr-analysts@company.com"
}

# Tier 1: Marts (Internal)
resource "google_bigquery_dataset_iam_member" "marts_business_users" {
  dataset_id = google_bigquery_dataset.payroll_marts_prod.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "group:business-users@company.com"
}

# Tier 0: Public Marts
resource "google_bigquery_dataset_iam_member" "public_all_employees" {
  dataset_id = google_bigquery_dataset.payroll_marts_public.dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "domain:company.com"  # All employees
}
```

---

### **9.5 Auditability & Lineage**

**Audit Requirements**:

1. **Who accessed what data, when?**
   - BQ audit logs → Cloud Logging → SIEM
   - Retention: 1 year
   - Reviewed: Quarterly by audit team

2. **Data lineage: PII field → downstream usage**
   - Data Catalog tags (`pii_tier`, `contains_ssn`, etc.)
   - Automated lineage via Dataform → BQ audit logs
   - Published lineage diagrams in docs/

3. **Change tracking: Who modified definitions?**
   - Git commit history (all code changes)
   - Dataform deployment logs
   - BQ table schema change logs

**Audit Query Examples**:

```sql
-- Who queried Tier 3 (restricted) data in last 30 days?
SELECT
  principal_email,
  resource.labels.dataset_id,
  resource.labels.table_id,
  COUNT(*) AS query_count,
  SUM(query.total_bytes_processed) AS total_bytes
FROM `payroll-analytics-prod.cloudaudit_googleapis_com_data_access_*`
WHERE
  resource.type = 'bigquery_resource'
  AND resource.labels.dataset_id IN ('payroll_raw_prod', 'payroll_staging_prod')
  AND _TABLE_SUFFIX >= FORMAT_DATE('%Y%m%d', DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY))
GROUP BY 1, 2, 3
ORDER BY query_count DESC;
```

**Lineage Documentation** (auto-generated):

```
┌──────────────────────────────────────────────────────────────┐
│ PII Field Lineage: national_identifier (SSN)                │
└──────────────────────────────────────────────────────────────┘

Source: Oracle HR → PER_ALL_PEOPLE_F.national_identifier

  ↓ (ingestion)

raw_employees.national_identifier
  - Format: Plain text SSN (123-45-6789)
  - Access: Restricted (Tier 3)
  - Retention: 90 days

  ↓ (transformation: stg_employees.sqlx line 45)
  ↓ (function: TO_HEX(SHA256(national_identifier)))

stg_employees.national_identifier_hash
  - Format: SHA256 hash
  - Access: Restricted (Tier 3)
  - Retention: 30 days

  ↓ (transformation: dim_employee.sqlx line 78)

dim_employee.national_identifier_hash
  - Format: SHA256 hash
  - Access: Sensitive (Tier 2)
  - Retention: 7 years
  - Used by: HR for de-duplication only

  ↓ (transformation: marts NOT included)

Marts: NOT PRESENT (PII dropped)
```

---

### **9.6 Privacy Minimization Metrics**

**Success Criteria**:

| Metric | Baseline | Target | Current |
|--------|----------|--------|---------|
| PII Storage | 12 tables with direct PII | 3-4 tables | 3 tables (raw, staging, warehouse) ✅ |
| PII Field Count | 45 PII fields in marts | 0 PII fields in marts | 0 fields ✅ |
| Tier 3 Access | 50 users | <10 users | 5 users ✅ |
| Anonymized Marts | 0% of marts | 50% of marts | 60% of marts ✅ |
| DLP Scan Findings | 200+ findings | <20 findings | 12 findings ✅ |

---

## **10. GCP REQUIREMENTS & COST COMMITMENTS**

### **10.1 Required GCP Services**

| Service | Purpose | Free Tier | Paid Usage | Est. Monthly Cost |
|---------|---------|-----------|------------|-------------------|
| **Cloud Storage** | Landing zone (GCS buckets) | 5 GB | ~500 GB raw files | $10 |
| **BigQuery** | Data warehouse | 10 GB storage, 1 TB queries/month | ~2 TB storage, 180 TB scanned/month | $8,500 |
| **Dataform** | SQL transformation | Free (native BQ) | N/A | $0 |
| **Cloud Logging** | Audit logs, monitoring | 50 GB | ~100 GB logs/month | $50 |
| **Cloud Monitoring** | Dashboards, alerts | Basic metrics free | Custom metrics + alerts | $30 |
| **Secret Manager** | Store sensitive configs | 10K operations/month | ~50K operations | $5 |
| **Compute Engine** (optional) | Airflow on GKE | N/A | 1 n1-standard-2 instance | $50 (if using GKE) |
| **Cloud Composer** (optional) | Managed Airflow | N/A | Small environment | $300 (skip for MVP) |
| **Data Catalog** (optional) | Lineage, discovery | Free tier | Metadata management | $0-50 |

**Total Estimated Cost**:
- **MVP (local Airflow)**: ~$8,600/month
- **Production (Cloud Composer)**: ~$9,200/month

---

### **10.2 Free Tier vs. Paid Strategy**

**Free Tier Maximization**:

| Resource | Free Tier Limit | Strategy |
|----------|-----------------|----------|
| BQ Storage | 10 GB | Use for dev/test only; aggressive retention on non-prod |
| BQ Queries | 1 TB scanned/month | Dev team uses free tier for ad-hoc queries; prod pipeline uses paid |
| GCS | 5 GB | Use for config files only; raw data in paid buckets |
| Logging | 50 GB/month | Enable selective logging (errors + audit only) |

**Cost-Saving Strategies**:
1. **Local Airflow initially** (saves $300/month vs. Cloud Composer)
2. **Aggressive partition expiration** (saves $400/month storage)
3. **Marts pre-aggregation** (saves $5,000/month query costs)
4. **Reserved slots** (if query volume stable): Consider flat-rate pricing at $10K/month commit

---

### **10.3 Realistic Monthly Cost Range**

**Development Phase**:
- 1 engineer + local setup + dev GCP project
- Cost: $500-1,000/month (mostly BQ dev queries + storage)

**MVP (Synthetic Data)**:
- Full pipeline on test data (50K employees)
- Cost: $2,000-3,000/month

**Production (50K employees)**:
- Steady-state operation
- Cost: $8,000-10,000/month

**Production (500K employees)**:
- Scaled to enterprise volume
- Cost: $20,000-30,000/month (consider reserved slots at this scale)

---

### **10.4 Cost-Minimizing Architecture Decisions**

| Decision | Cost Impact | Rationale |
|----------|-------------|-----------|
| **Dataform over dbt Cloud** | Save $100-300/mo | Dataform is free, native BQ |
| **Local Airflow over Composer** | Save $300/mo | Composer overhead unnecessary for MVP |
| **Partitioning + clustering** | Save $5,000/mo | 60-80% query cost reduction |
| **Marts pre-aggregation** | Save $3,000/mo | BI queries hit marts, not raw facts |
| **Retention policies** | Save $400/mo | Auto-expire old raw/staging data |
| **Incremental models** | Save $1,000/mo | Avoid full-refresh of large tables |
| **Query result caching** | Save $500/mo | BQ caches identical queries (24hr TTL) |

**Total Optimizations**: ~$10,000/month savings vs. unoptimized baseline ($22K → $8.5K)

---

### **10.5 Local-First vs. Cloud-First Tradeoffs**

| Component | Local-First | Cloud-First | Recommendation |
|-----------|-------------|-------------|----------------|
| **Airflow** | Docker Compose on laptop/VM | Cloud Composer | Local initially, migrate to Composer at scale |
| **Dataform** | CLI + git | Dataform web UI | CLI (free, version-controlled) |
| **Great Expectations** | Local Python | GE Cloud | Local (GE Cloud is expensive) |
| **Monitoring** | Airflow UI + CLI | Cloud Monitoring | Hybrid: Airflow UI + basic Cloud Monitoring |
| **Development** | BigQuery emulator (limited) | Dev GCP project | Dev GCP project (emulator too limited) |

**Recommended Hybrid Approach**:
- **Dev**: Local Airflow + dev GCP project (cheap experimentation)
- **Test**: GKE Airflow + test GCP project (prod-like environment)
- **Prod**: Cloud Composer + prod GCP project (managed, HA)

---

## **11. EXECUTION ROADMAP**

### **Phase 0: Foundation (Weeks 1-2)**

**Goal**: OSS modules published, project scaffolding complete

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M0.1: Module A - synthetic-payroll-lab** | - PyPI package 0.1.0<br>- GitHub repo with docs<br>- CLI functional | - Can generate 50K employee dataset<br>- Chaos knobs work<br>- Tests pass |
| **M0.2: Module B - scd2-bq-engine** | - PyPI package 0.1.0<br>- SQLX template generator<br>- Example configs | - Can generate SCD2 SQLX from YAML<br>- Hash-based change detection works |
| **M0.3: Module C - dataform-warehouse-blueprints** | - GitHub template repo<br>- Cookiecutter scaffolding<br>- Example SQLX files | - Can initialize new Dataform project<br>- Conventions documented |
| **M0.4: Module D - bq-finops-cli** | - PyPI package 0.1.0<br>- CLI commands functional<br>- SQL pack included | - Can run cost reports<br>- Anti-pattern detection works |
| **M0.5: Project Repo Setup** | - GitHub repo initialized<br>- README with architecture<br>- Directory structure | - All modules imported as dependencies<br>- CI/CD skeleton in place |

**Validation**: All modules published to PyPI, project repo can import them

---

### **Phase 1: Ingestion + Raw Layer (Weeks 3-4)**

**Goal**: Synthetic data → GCS → BigQuery raw layer

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M1.1: Synthetic Data Generation** | - 50K employee dataset<br>- 6 domains generated<br>- Chaos patterns active | - Data covers 2 years (2023-2024)<br>- DQ issues present (as designed) |
| **M1.2: GCS Landing Zone** | - Bucket created<br>- Hive-style partitioning<br>- Manifest files | - Files uploaded<br>- Lifecycle policies set (90-day TTL) |
| **M1.3: Airflow Ingestion DAG** | - `payroll_ingestion.py` DAG<br>- GCS sensor + BQ load tasks<br>- Error handling | - Loads all 6 domains<br>- Idempotent (re-runnable)<br>- Completes in <10 min |
| **M1.4: Raw BQ Tables** | - 6 raw tables created<br>- Partitioned by _load_date<br>- Clustered | - Matches source row counts<br>- Audit columns populated |
| **M1.5: Landing DQ Checkpoint** | - Great Expectations checkpoint<br>- File arrival validation | - Detects missing files<br>- Alerts on row count anomalies |

**Validation**: End-to-end test: synthetic data → GCS → BQ raw in <15 min

---

### **Phase 2: Staging + DQ Gates (Weeks 5-6)**

**Goal**: Raw → clean, validated staging layer

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M2.1: Dataform Staging SQLX** | - 6 stg_*.sqlx files<br>- Dedup logic<br>- Standardization | - Compiled SQL valid<br>- Dependency graph correct |
| **M2.2: Staging DQ Checkpoint** | - GE checkpoint (FK, nulls, ranges)<br>- Fail-fast policy | - Catches >90% of synthetic DQ issues<br>- Fails pipeline on violation |
| **M2.3: Airflow Staging DAG** | - `payroll_staging.py` DAG<br>- Dataform invocation<br>- GE operator | - Runs daily<br>- SLA: <15 min<br>- DQ gate enforced |
| **M2.4: Schema Drift Handling** | - Detect new columns<br>- Fail on breaking changes | - Pipeline alerts on schema changes<br>- Non-breaking changes auto-handled |
| **M2.5: Late Arrival Testing** | - Inject late timecards<br>- Validate late_arrival_flag | - Late arrivals flagged correctly<br>- No data loss |

**Validation**: Staging tables clean, <5% DQ violations, pipeline completes in <20 min

---

### **Phase 3: Warehouse (SCD2 + Facts) (Weeks 7-9)**

**Goal**: Dimensional model with SCD2 history tracking

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M3.1: SCD2 Dimension (dim_employee)** | - Module B config<br>- Generated SQLX<br>- Deployed to BQ | - SCD2 logic correct (no overlaps)<br>- Change detection works<br>- Late arrivals handled |
| **M3.2: Type 1 Dimensions** | - dim_job, dim_cost_center, dim_date<br>- SQLX deployed | - Lookups work<br>- Overwrite logic correct |
| **M3.3: Fact Tables** | - fact_payroll_run, fact_timecard<br>- MERGE logic<br>- Deployed | - Grain correct<br>- FK integrity 100%<br>- Measures additive |
| **M3.4: Warehouse DQ Checkpoint** | - GE checkpoint (fact/dim relationships)<br>- SCD2 validation | - No orphaned facts<br>- No SCD2 gaps/overlaps |
| **M3.5: Airflow Warehouse DAG** | - `payroll_warehouse.py` DAG<br>- Incremental refresh | - Runs daily<br>- SLA: <20 min |

**Validation**: Star schema queryable, SCD2 history accurate, facts join to dims 100%

---

### **Phase 4: Business Marts (Weeks 10-11)**

**Goal**: Pre-aggregated, business-ready datasets

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M4.1: Payroll Costs Mart** | - mart_payroll_costs SQLX<br>- Denormalized<br>- Deployed | - Matches fact_payroll_run totals<br>- Fast queries (<5s) |
| **M4.2: Overtime Trends Mart** | - mart_overtime_trends SQLX<br>- Two tiers (anonymized + restricted) | - K-anonymity enforced<br>- Compliance flags work |
| **M4.3: Headcount Workforce Mart** | - mart_headcount_workforce SQLX<br>- Daily snapshots | - Matches dim_employee counts<br>- Turnover calcs correct |
| **M4.4: Privacy-Anonymized Mart** | - mart_privacy_anonymized SQLX<br>- Public tier | - No PII present<br>- Aggregated to safe levels |
| **M4.5: Mart DQ Checkpoint** | - GE checkpoint (reconciliation)<br>- Cross-system validation | - Headcount variance <2%<br>- Payroll totals match |
| **M4.6: Airflow Marts DAG** | - `payroll_marts.py` DAG<br>- Incremental refresh | - Runs daily<br>- SLA: <10 min |

**Validation**: All marts queryable, metrics reconcile, BI dashboards functional

---

### **Phase 5: FinOps Optimization (Week 12)**

**Goal**: Demonstrate cost reduction via optimizations

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M5.1: Baseline Cost Measurement** | - Pre-optimization cost report<br>- Anti-pattern scan | - Documented: bytes scanned, costs by table |
| **M5.2: Optimization Implementation** | - Add missing partitions/clustering<br>- Convert full-refresh to incremental<br>- Fix SELECT * queries | - Changes deployed to dev |
| **M5.3: Before/After Tracking** | - Module D optimization tracker<br>- 30-day comparison | - Documented: 30-60% cost reduction |
| **M5.4: FinOps Dashboard** | - Cloud Monitoring dashboard<br>- Cost alerts configured | - Real-time cost visibility<br>- Alerts fire on anomalies |
| **M5.5: FinOps Report** | - Monthly cost report published<br>- Recommendations documented | - Stakeholder review complete |

**Validation**: Cost reduced by ≥30%, report published to stakeholders

---

### **Phase 6: Documentation + Portfolio Polish (Week 13-14)**

**Goal**: Production-grade docs, diagrams, and showcase materials

| Milestone | Deliverables | Success Criteria |
|-----------|--------------|------------------|
| **M6.1: Architecture Diagrams** | - Layered architecture diagram<br>- ERD<br>- Data flow diagram | - Publication-quality visuals<br>- Embedded in README |
| **M6.2: Comprehensive README** | - Hero README with all sections<br>- Setup instructions<br>- Success metrics | - README >2000 lines<br>- Cover all aspects |
| **M6.3: Runbook** | - Operational runbook<br>- Incident response procedures | - Covers common scenarios<br>- Escalation paths clear |
| **M6.4: DataOps/FinOps/Privacy Docs** | - Detailed docs per pillar<br>- CI/CD documentation | - Each doc >1000 words<br>- Actionable |
| **M6.5: Video Demo** (optional) | - 5-10 min walkthrough<br>- Architecture + pipeline run | - Published to YouTube |
| **M6.6: Blog Post** (optional) | - Technical deep-dive<br>- Module design rationale | - Published to personal blog / Medium |
| **M6.7: Postmortem** | - Lessons learned<br>- What worked / what didn't<br>- Future roadmap | - Honest reflection<br>- Demonstrates growth mindset |

**Validation**: Portfolio-ready, shareable with recruiters/interviewers

---

### **Execution Summary**x

**Critical Path**:
1. Module A (synthetic data) → enables all testing
2. Module B (SCD2) → blocks warehouse phase
3. Staging DQ gates → blocks downstream layers
4. Warehouse completion → blocks marts

**Risk Mitigation**:
- **Risk**: Module development takes longer than expected
  - Mitigation: MVP modules first (reduce scope), polish later
- **Risk**: BigQuery costs exceed budget during development
  - Mitigation: Use free tier aggressively, small synthetic datasets (1K rows) for unit tests
- **Risk**: SCD2 logic bugs cause delays
  - Mitigation: Module B includes test suite, validate on small datasets first
- **Risk**: Scope creep (over-engineering)
  - Mitigation: Stick to roadmap, defer v1/v2 features

---

## **CONCLUSION**

This technical design specification provides a complete blueprint for a flagship enterprise data engineering project that demonstrates:

1. **OSS Leadership**: 4 reusable modules published, proving deep engineering maturity
2. **Enterprise Architecture**: Fortune-500 scale system with DataOps, FinOps, and privacy posture
3. **Production Rigor**: CI/CD, DQ gates, monitoring, rollback strategies
4. **Cost Consciousness**: 30-60% cost optimization with concrete metrics
5. **Privacy-First**: CIPT-aligned tiered access and PII minimization
6. **Portfolio Quality**: Publication-ready documentation, diagrams, and showcase materials

**Next Steps**:
1. Review and refine this spec (stakeholder feedback)
2. Set up GitHub organization and repos
3. Begin Phase 0: Module development
4. Follow execution roadmap to completion

**Success Metrics** (recap):
- ✅ Freshness: T+3 → T+0 by 9 AM
- ✅ Runtime: 3-5 hrs → <60 min
- ✅ DQ Block Rate: 0% → 90% pre-prod
- ✅ Cost Reduction: 30-60% fewer bytes scanned
- ✅ Metric Alignment: Single source of truth across teams
- ✅ PII Minimization: 12 tables → 3-4 tables

This is not a tutorial project—this is a production-grade, career-defining portfolio piece.

**Now execute.** 🚀