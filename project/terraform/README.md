# Terraform Infrastructure

Infrastructure as Code for Payroll Analytics Platform on GCP

## 📦 Resources Created

### BigQuery
- **5 Datasets**: raw, staging, warehouse, marts, assertions
- **External Connection**: For GCS-backed external tables
- **Dataset-level IAM**: Service account access controls

### Cloud Storage
- **3 Buckets**:
  - `payroll-landing-{env}` - Data ingestion (30-day lifecycle)
  - `payroll-archive-{env}` - Long-term storage (2-year lifecycle)
  - `payroll-temp-{env}` - Temporary files (7-day lifecycle)
- **Versioning**: Enabled for landing & archive buckets
- **Lifecycle Management**: Auto-deletion based on age

### IAM
- **3 Service Accounts**:
  - `payroll-airflow-{env}` - For orchestration
  - `payroll-dataform-{env}` - For transformations
  - `payroll-dq-{env}` - For data quality checks
- **Service Account Keys**: Generated for local development
- **IAM Bindings**: Least-privilege access to resources

## 🚀 Usage

### Prerequisites

```bash
# Install Terraform
brew install terraform  # macOS
# or download from https://www.terraform.io/downloads

# Authenticate with GCP
gcloud auth application-default login

# Set your GCP project
export GOOGLE_CLOUD_PROJECT="payroll-analytics-dev"
```

### Deploy Infrastructure

```bash
# Navigate to terraform directory
cd project/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your values
vim terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Apply changes
terraform apply
```

### View Outputs

```bash
# View all outputs
terraform output

# View specific output
terraform output bigquery_datasets
terraform output gcs_buckets
terraform output service_accounts
```

### Destroy Infrastructure

```bash
# WARNING: This will delete all resources!
terraform destroy
```

## 📋 Configuration

### terraform.tfvars

```hcl
project_id  = "your-gcp-project-id"
region      = "us-central1"
location    = "US"
environment = "dev"
```

### Override Defaults

You can override dataset and bucket configurations in `terraform.tfvars`:

```hcl
bigquery_datasets = {
  raw = {
    description                 = "My custom description"
    default_table_expiration_ms = 7776000000  # 90 days
    delete_contents_on_destroy  = true
  }
}

gcs_buckets = {
  landing = {
    storage_class = "STANDARD"
    lifecycle_age = 60  # Keep for 60 days
  }
}
```

## 🔐 Service Account Keys

Service account keys are generated in the `keys/` directory:

```
terraform/keys/
├── airflow-sa-key.json
├── dataform-sa-key.json
└── data-quality-sa-key.json
```

**⚠️ SECURITY**: Never commit these keys to version control!

### Use Keys Locally

```bash
# Export for gcloud CLI
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/keys/airflow-sa-key.json"

# Or use in Python
from google.cloud import bigquery
client = bigquery.Client.from_service_account_json('keys/airflow-sa-key.json')
```

## 🏗️ Resource Structure

```
GCP Project: payroll-analytics-dev
│
├── BigQuery
│   ├── payroll_raw          (Bronze layer)
│   ├── payroll_staging      (Silver layer, 60-day expiration)
│   ├── payroll_warehouse    (Gold layer, 2-year expiration)
│   ├── payroll_marts        (Platinum layer, 1-year expiration)
│   └── payroll_assertions   (Data quality, 30-day expiration)
│
├── Cloud Storage
│   ├── payroll-landing-dev  (STANDARD, 30-day lifecycle)
│   ├── payroll-archive-dev  (NEARLINE, 2-year lifecycle)
│   └── payroll-temp-dev     (STANDARD, 7-day lifecycle)
│
└── IAM
    ├── payroll-airflow-dev@...      (BigQuery Admin, Storage Admin)
    ├── payroll-dataform-dev@...     (BigQuery Admin, Storage Viewer)
    └── payroll-dq-dev@...           (BigQuery Data Viewer, Job User)
```

## 💰 Cost Estimates

### Development Environment
- **BigQuery**: ~$0 (free tier: 10 GB storage, 1 TB queries/month)
- **Cloud Storage**: ~$2-5/month (depends on data volume)
- **Total**: **~$5/month or less**

### Production Environment
- **BigQuery**: ~$50-200/month (depends on queries & data)
- **Cloud Storage**: ~$20-50/month
- **Total**: **~$100-300/month**

## 🔄 State Management

For team collaboration, use remote state:

```hcl
# main.tf
terraform {
  backend "gcs" {
    bucket = "payroll-terraform-state"
    prefix = "terraform/state"
  }
}
```

Create the state bucket:

```bash
gsutil mb gs://payroll-terraform-state
gsutil versioning set on gs://payroll-terraform-state
```

## 📚 Terraform Files

- `main.tf` - Provider configuration
- `variables.tf` - Input variables
- `bigquery.tf` - BigQuery resources
- `storage.tf` - GCS buckets
- `iam.tf` - Service accounts & permissions
- `outputs.tf` - Output values
- `terraform.tfvars` - Variable values (create from .example)

## 🔍 Verification

After applying, verify resources:

```bash
# List BigQuery datasets
bq ls

# List GCS buckets
gsutil ls

# List service accounts
gcloud iam service-accounts list
```

## 🐛 Troubleshooting

### Error: API not enabled

```bash
# Enable required APIs
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable dataform.googleapis.com
```

### Error: Insufficient permissions

Ensure your GCP user has these roles:
- `roles/owner` or
- `roles/bigquery.admin`
- `roles/storage.admin`
- `roles/iam.serviceAccountAdmin`

### Error: Resource already exists

If resources exist from previous runs:

```bash
# Import existing resources
terraform import google_bigquery_dataset.datasets["raw"] payroll_raw

# Or destroy and recreate
terraform destroy
terraform apply
```

## 📖 Next Steps

After infrastructure is deployed:

1. **Verify Resources**:
   ```bash
   terraform output
   ```

2. **Configure Dataform**:
   - Update `dataform/dataform.json` with dataset IDs
   - Update `dataform/workflow_settings.yaml`

3. **Configure Airflow**:
   - Set Airflow variables with bucket names
   - Add service account key as Airflow connection

4. **Test Pipeline**:
   - Upload sample data to landing bucket
   - Run Airflow DAG

## 🔗 Related Documentation

- [GCP BigQuery Terraform](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset)
- [GCS Terraform](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket)
- [IAM Terraform](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_service_account)

---

**Managed with Terraform ❤️**
