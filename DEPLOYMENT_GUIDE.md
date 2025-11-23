# 🚀 Deployment Guide
## Enterprise Payroll Analytics Platform

**Status**: ✅ Ready for Deployment  
**Last Updated**: November 23, 2025

---

## 📦 What's Ready to Deploy

### ✅ Complete Codebase
- **157 files** committed to Git
- **20,976 lines** of code
- **4 OSS modules** published to PyPI
- **Complete infrastructure** (Terraform, Docker, K8s)
- **35 automated tests** (all passing)
- **Comprehensive documentation**

### ✅ Docker Images Built
```bash
payroll/airflow:latest   1.78GB   ✅ Built
payroll/utils:latest     2.03GB   ✅ Built
```

### ✅ Git Repository
```bash
Repository:  https://github.com/bhavyabgada/payroll
Branch:      main
Commit:      6c12851 (Initial commit)
Status:      Ready to push
```

---

## 🔄 Deployment Workflow

### Phase 1: Push to GitHub ✅ READY

```bash
# Push to GitHub (run from project root)
git push -u origin main

# Verify on GitHub
open https://github.com/bhavyabgada/payroll
```

**What gets pushed**:
- ✅ All source code (157 files)
- ✅ Documentation (25+ markdown files)
- ✅ Terraform configuration
- ✅ Docker configurations
- ✅ Kubernetes manifests
- ✅ Tests & scripts
- ✅ Module source code

**⚠️ What won't be pushed** (.gitignore):
- Service account keys
- Virtual environments
- Docker images (binary)
- Build artifacts
- Cached files
- Local environment files

---

### Phase 2: Deploy GCP Infrastructure

#### Step 1: Authenticate with GCP

```bash
# Login to GCP
gcloud auth login

# Set project
gcloud config set project payroll-analytics-prod

# Create project if needed
gcloud projects create payroll-analytics-prod \
  --name="Payroll Analytics Platform"

# Enable billing
gcloud beta billing projects link payroll-analytics-prod \
  --billing-account=YOUR_BILLING_ACCOUNT_ID
```

#### Step 2: Enable Required APIs

```bash
# Enable GCP services
gcloud services enable bigquery.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable dataform.googleapis.com
gcloud services enable logging.googleapis.com
gcloud services enable monitoring.googleapis.com
gcloud services enable container.googleapis.com
```

#### Step 3: Deploy with Terraform

```bash
cd project/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Initialize Terraform
terraform init

# Preview changes
terraform plan

# Deploy infrastructure
terraform apply
```

**Created Resources**:
- 5 BigQuery datasets (raw, staging, warehouse, marts, assertions)
- 3 GCS buckets (landing, archive, temp)
- 3 Service accounts (airflow, dataform, data-quality)
- IAM bindings
- BigQuery connection

**Time**: ~5 minutes  
**Cost**: ~$0 (using free tier)

---

### Phase 3: Build & Push Docker Images

#### Step 1: Configure GCR

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Set project ID
export GCP_PROJECT_ID="payroll-analytics-prod"
```

#### Step 2: Build Images

```bash
cd project/docker

# Build all images
./build.sh

# Or build individually
docker build -f Dockerfile.airflow -t gcr.io/$GCP_PROJECT_ID/airflow:latest ..
docker build -f Dockerfile.utils -t gcr.io/$GCP_PROJECT_ID/utils:latest ..
```

#### Step 3: Push to GCR

```bash
# Push all images
./push.sh

# Or push individually
docker push gcr.io/$GCP_PROJECT_ID/airflow:latest
docker push gcr.io/$GCP_PROJECT_ID/utils:latest
```

**Time**: ~10-15 minutes (first build)  
**Storage**: ~4 GB in GCR  
**Cost**: ~$0.50/month

---

### Phase 4: Deploy to Kubernetes

#### Step 1: Create GKE Cluster

```bash
# Create cluster
gcloud container clusters create payroll-analytics-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5

# Get credentials
gcloud container clusters get-credentials payroll-analytics-cluster \
  --zone us-central1-a
```

**Time**: ~5-10 minutes  
**Cost**: ~$150-300/month

#### Step 2: Create Secrets

```bash
cd project/k8s

# Create namespace
kubectl apply -f namespace.yaml

# Create GCP credentials secret
kubectl create secret generic gcp-credentials \
  --from-file=service-account-key.json=../terraform/keys/airflow-sa-key.json \
  -n payroll-analytics

# Generate Fernet key
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create application secrets
kubectl create secret generic payroll-secrets \
  --from-literal=postgres-user=airflow \
  --from-literal=postgres-password=$(openssl rand -base64 32) \
  --from-literal=airflow-admin-username=admin \
  --from-literal=airflow-admin-password=$(openssl rand -base64 32) \
  --from-literal=airflow-fernet-key=$FERNET_KEY \
  -n payroll-analytics
```

#### Step 3: Deploy Applications

```bash
# Apply configurations
kubectl apply -f configmap.yaml
kubectl apply -f postgres.yaml
kubectl apply -f airflow-deployment.yaml
kubectl apply -f cronjob-finops.yaml

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=airflow -n payroll-analytics --timeout=300s
```

#### Step 4: Access Airflow UI

```bash
# Get LoadBalancer IP
kubectl get svc airflow-webserver -n payroll-analytics

# Or use port forwarding
kubectl port-forward svc/airflow-webserver 8080:8080 -n payroll-analytics
```

Access at `http://<EXTERNAL-IP>:8080` or `http://localhost:8080`

**Default credentials**: Check secrets or use admin/[generated-password]

**Time**: ~10-15 minutes  
**Cost**: Included in GKE cost

---

### Phase 5: Load Test Data

#### Step 1: Generate Synthetic Data

```bash
# Install the module
pip install synthetic-payroll-lab

# Generate data
synthetic-payroll generate \
  --num-employees 10000 \
  --output-dir ./test-data \
  --format csv

# Or use Docker
docker run --rm -v $(pwd)/test-data:/data \
  payroll/utils:latest \
  synthetic-payroll generate \
    --num-employees 10000 \
    --output-dir /data \
    --format csv
```

#### Step 2: Upload to GCS

```bash
# Upload to landing bucket
gsutil -m cp -r ./test-data/* gs://payroll-landing-prod/

# Verify
gsutil ls gs://payroll-landing-prod/
```

#### Step 3: Trigger Pipeline

```bash
# Access Airflow UI
# Enable DAG: payroll_main_pipeline
# Trigger manual run

# Or use CLI
gcloud composer environments run payroll-analytics \
  --location us-central1 \
  dags trigger -- payroll_main_pipeline
```

---

### Phase 6: Verify Deployment

#### Check BigQuery Tables

```bash
# List tables
bq ls payroll_staging
bq ls payroll_warehouse
bq ls payroll_marts

# Query data
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as employee_count FROM payroll_warehouse.dim_employee WHERE is_current = TRUE'
```

#### Check Data Quality

```bash
# Run Great Expectations
kubectl exec -it deployment/airflow-webserver -n payroll-analytics -- \
  python /opt/airflow/scripts/run_data_quality_checks.py

# Check results in BigQuery
bq query --use_legacy_sql=false \
  'SELECT * FROM payroll_assertions.staging_checkpoint_results ORDER BY run_time DESC LIMIT 10'
```

#### Check Costs

```bash
# Run FinOps analysis
kubectl exec -it deployment/airflow-webserver -n payroll-analytics -- \
  python /opt/airflow/scripts/finops_monitoring.py \
    --project-id payroll-analytics-prod \
    --days 7

# View reports
gsutil ls gs://payroll-archive-prod/reports/
```

---

## 🔒 Security Checklist

### Before Deployment

- [ ] **Change default passwords** in K8s secrets
- [ ] **Restrict service account permissions** to minimum required
- [ ] **Enable VPC peering** for GKE cluster
- [ ] **Set up Cloud Armor** for DDoS protection
- [ ] **Enable binary authorization** for container images
- [ ] **Configure network policies** for pod-to-pod communication
- [ ] **Enable audit logging** for compliance
- [ ] **Set up Secret Manager** instead of K8s secrets (production)
- [ ] **Configure Workload Identity** instead of service account keys
- [ ] **Enable private GKE cluster** for production

### After Deployment

- [ ] **Rotate service account keys** regularly
- [ ] **Review IAM permissions** monthly
- [ ] **Monitor security alerts** in Cloud Console
- [ ] **Set up vulnerability scanning** for containers
- [ ] **Enable Cloud DLP** for PII detection
- [ ] **Configure data retention policies**
- [ ] **Set up backup & disaster recovery**
- [ ] **Document incident response procedures**

---

## 💰 Cost Management

### Development Environment
```
GKE (3 nodes, n1-standard-2):    $150/month
BigQuery (storage + queries):     $10/month
Cloud Storage:                     $5/month
Docker images (GCR):               $1/month
──────────────────────────────────────────
Total:                           ~$170/month
```

### Production Environment
```
GKE (5 nodes, n1-standard-4):    $500/month
BigQuery (storage + queries):    $100/month
Cloud Storage:                    $20/month
Load Balancer:                    $20/month
──────────────────────────────────────────
Total:                          ~$640/month
```

### Cost Optimization Tips

1. **Use preemptible nodes** for non-critical workloads (-70% cost)
2. **Enable cluster autoscaling** to match workload
3. **Set table expiration** policies (already configured)
4. **Use partition pruning** in queries
5. **Enable BI Engine** for frequent queries
6. **Schedule heavy jobs** during off-peak hours
7. **Use committed use discounts** for long-term projects
8. **Monitor with FinOps CLI** weekly

```bash
# Weekly cost check
bq-finops analyze --project-id payroll-analytics-prod --days 7
```

---

## 📊 Monitoring & Alerts

### Set Up Monitoring

```bash
# Create alert policies
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="BigQuery High Costs" \
  --condition-display-name="Daily cost exceeds $50" \
  --condition-threshold-value=50
```

### Logs to Monitor

1. **Airflow Scheduler Logs**: DAG failures
2. **BigQuery Audit Logs**: Expensive queries
3. **Great Expectations Results**: Data quality failures
4. **FinOps Reports**: Budget overruns
5. **GKE Events**: Pod crashes, OOM errors

### Dashboards

Create Cloud Monitoring dashboards for:
- Pipeline execution times
- Data quality metrics
- BigQuery costs
- Kubernetes resource usage
- Data freshness (SLI)

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: Airflow pods not starting
```bash
# Check events
kubectl describe pod -l app=airflow -n payroll-analytics

# Check logs
kubectl logs -l app=airflow,component=webserver -n payroll-analytics

# Solution: Usually service account permissions or secrets missing
```

#### Issue: BigQuery access denied
```bash
# Check service account permissions
gcloud projects get-iam-policy payroll-analytics-prod \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:*airflow*"

# Solution: Grant bigquery.admin role
gcloud projects add-iam-policy-binding payroll-analytics-prod \
  --member="serviceAccount:payroll-airflow-prod@payroll-analytics-prod.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

#### Issue: Docker image pull failed
```bash
# Check GCR permissions
gcloud projects get-iam-policy payroll-analytics-prod \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/storage.objectViewer"

# Solution: Grant GKE access to GCR
gcloud projects add-iam-policy-binding payroll-analytics-prod \
  --member="serviceAccount:payroll-analytics-prod.svc.id.goog[payroll-analytics/default]" \
  --role="roles/storage.objectViewer"
```

---

## 🔄 CI/CD (Future Enhancement)

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to GCP

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v0
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: payroll-analytics-prod
      
      - name: Build and Push Docker Images
        run: |
          cd project/docker
          ./build.sh
          ./push.sh
      
      - name: Deploy to GKE
        run: |
          gcloud container clusters get-credentials payroll-analytics-cluster --zone us-central1-a
          kubectl apply -f project/k8s/
```

---

## ✅ Deployment Checklist

### Pre-Deployment
- [x] Code committed to Git
- [x] Docker images built
- [x] Tests passing (35/35)
- [x] Documentation complete
- [ ] GCP project created
- [ ] Billing enabled
- [ ] APIs enabled

### Infrastructure
- [ ] Terraform applied
- [ ] Service accounts created
- [ ] IAM permissions granted
- [ ] GCS buckets created
- [ ] BigQuery datasets created

### Kubernetes
- [ ] GKE cluster created
- [ ] Secrets configured
- [ ] ConfigMaps applied
- [ ] Deployments running
- [ ] Services accessible

### Data Pipeline
- [ ] Test data generated
- [ ] Data uploaded to GCS
- [ ] DAGs enabled
- [ ] Pipeline executed
- [ ] Tables populated

### Verification
- [ ] Airflow UI accessible
- [ ] BigQuery tables have data
- [ ] Great Expectations passing
- [ ] FinOps monitoring working
- [ ] Costs within budget

---

## 📞 Support

### Documentation
- Main README: `README.md`
- Final Report: `FINAL_COMPLETION_REPORT.md`
- Terraform Guide: `project/terraform/README.md`
- Docker Guide: `project/docker/README.md`
- Kubernetes Guide: `project/k8s/README.md`

### Resources
- GitHub: https://github.com/bhavyabgada/payroll
- PyPI Modules:
  - https://pypi.org/project/synthetic-payroll-lab/
  - https://pypi.org/project/scd2-bq-engine/
  - https://pypi.org/project/dataform-warehouse-blueprints/
  - https://pypi.org/project/bq-finops-cli/

---

## 🎉 You're Ready to Deploy!

Everything is prepared and tested. Just run:

```bash
# 1. Push to GitHub
git push -u origin main

# 2. Deploy infrastructure
cd project/terraform && terraform apply

# 3. Build & push images
cd ../docker && ./build.sh && ./push.sh

# 4. Deploy to K8s
cd ../k8s && kubectl apply -f .

# 5. Load test data & trigger pipeline
```

**Good luck! 🚀**

---

*Last updated: November 23, 2025*

