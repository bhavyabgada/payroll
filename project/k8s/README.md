# Kubernetes Deployment

Production Kubernetes deployment for Payroll Analytics Platform

## 📦 Components

### Core Services
- **Airflow Webserver** (2 replicas, LoadBalancer)
- **Airflow Scheduler** (1 replica)
- **PostgreSQL** (StatefulSet, 1 replica)

### Batch Jobs
- **FinOps Monitoring** (CronJob, weekly)

### Storage
- **Airflow Logs PVC** (50 GB, ReadWriteMany)
- **Reports PVC** (10 GB, ReadWriteMany)
- **PostgreSQL PVC** (10 GB, ReadWriteOnce)

## 🚀 Prerequisites

### 1. GKE Cluster Setup

```bash
# Create GKE cluster
gcloud container clusters create payroll-analytics-cluster \
  --zone us-central1-a \
  --num-nodes 3 \
  --machine-type n1-standard-2 \
  --enable-autoscaling \
  --min-nodes 2 \
  --max-nodes 5 \
  --enable-autorepair \
  --enable-autoupgrade

# Get cluster credentials
gcloud container clusters get-credentials payroll-analytics-cluster \
  --zone us-central1-a
```

### 2. Build and Push Docker Images

```bash
# Set project ID
export GCP_PROJECT_ID="payroll-analytics-prod"

# Configure Docker for GCR
gcloud auth configure-docker

# Build Airflow image
cd project
docker build -f docker/Dockerfile.airflow -t gcr.io/$GCP_PROJECT_ID/airflow:latest .
docker push gcr.io/$GCP_PROJECT_ID/airflow:latest

# Build Utils image
docker build -f docker/Dockerfile.utils -t gcr.io/$GCP_PROJECT_ID/utils:latest .
docker push gcr.io/$GCP_PROJECT_ID/utils:latest
```

### 3. Create Secrets

```bash
# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Create GCP service account key secret
kubectl create secret generic gcp-credentials \
  --from-file=service-account-key.json=/path/to/your/key.json \
  -n payroll-analytics

# Generate Fernet key for Airflow
FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Create Airflow secrets
kubectl create secret generic payroll-secrets \
  --from-literal=postgres-user=airflow \
  --from-literal=postgres-password=airflow \
  --from-literal=airflow-admin-username=admin \
  --from-literal=airflow-admin-password=changeme \
  --from-literal=airflow-fernet-key=$FERNET_KEY \
  -n payroll-analytics
```

## 📋 Deployment Steps

### Step 1: Apply Namespace & ConfigMap

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/configmap.yaml
```

### Step 2: Deploy PostgreSQL

```bash
kubectl apply -f k8s/postgres.yaml

# Wait for Postgres to be ready
kubectl wait --for=condition=ready pod -l app=postgres -n payroll-analytics --timeout=300s
```

### Step 3: Deploy Airflow

```bash
kubectl apply -f k8s/airflow-deployment.yaml

# Wait for Airflow to be ready
kubectl wait --for=condition=ready pod -l app=airflow -n payroll-analytics --timeout=300s
```

### Step 4: Deploy CronJobs

```bash
kubectl apply -f k8s/cronjob-finops.yaml
```

### Step 5: Verify Deployment

```bash
# Check all resources
kubectl get all -n payroll-analytics

# Check pods
kubectl get pods -n payroll-analytics

# Check services
kubectl get svc -n payroll-analytics
```

## 🌐 Access Airflow UI

### Get LoadBalancer IP

```bash
kubectl get svc airflow-webserver -n payroll-analytics
```

Access Airflow at `http://<EXTERNAL-IP>:8080`

**Default credentials**:
- Username: `admin`
- Password: `changeme` (or what you set in secrets)

### Port Forwarding (Development)

```bash
kubectl port-forward svc/airflow-webserver 8080:8080 -n payroll-analytics
```

Access at `http://localhost:8080`

## 🔍 Monitoring & Logs

### View Logs

```bash
# Airflow webserver logs
kubectl logs -l app=airflow,component=webserver -n payroll-analytics -f

# Airflow scheduler logs
kubectl logs -l app=airflow,component=scheduler -n payroll-analytics -f

# PostgreSQL logs
kubectl logs -l app=postgres -n payroll-analytics -f

# FinOps CronJob logs (last run)
kubectl logs job/$(kubectl get jobs -n payroll-analytics -l cronjob=finops-monitoring --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}') -n payroll-analytics
```

### Execute Commands in Pods

```bash
# Shell into Airflow webserver
kubectl exec -it deployment/airflow-webserver -n payroll-analytics -- /bin/bash

# Shell into utils container (for manual jobs)
kubectl run -it --rm debug --image=gcr.io/$GCP_PROJECT_ID/utils:latest -n payroll-analytics -- /bin/bash
```

## 🔧 Configuration Updates

### Update ConfigMap

```bash
# Edit configmap
kubectl edit configmap payroll-config -n payroll-analytics

# Or apply changes
kubectl apply -f k8s/configmap.yaml

# Restart pods to pick up changes
kubectl rollout restart deployment/airflow-webserver -n payroll-analytics
kubectl rollout restart deployment/airflow-scheduler -n payroll-analytics
```

### Update Secrets

```bash
# Update secret
kubectl delete secret payroll-secrets -n payroll-analytics
kubectl create secret generic payroll-secrets \
  --from-literal=postgres-user=airflow \
  --from-literal=postgres-password=new-password \
  -n payroll-analytics

# Restart pods
kubectl rollout restart deployment/airflow-webserver -n payroll-analytics
```

### Update Docker Images

```bash
# Rebuild and push
docker build -f docker/Dockerfile.airflow -t gcr.io/$GCP_PROJECT_ID/airflow:latest .
docker push gcr.io/$GCP_PROJECT_ID/airflow:latest

# Rolling update
kubectl rollout restart deployment/airflow-webserver -n payroll-analytics
kubectl rollout restart deployment/airflow-scheduler -n payroll-analytics

# Check status
kubectl rollout status deployment/airflow-webserver -n payroll-analytics
```

## 📊 Resource Management

### Scaling

```bash
# Scale webserver
kubectl scale deployment airflow-webserver --replicas=3 -n payroll-analytics

# Check HPA (if configured)
kubectl get hpa -n payroll-analytics
```

### Resource Usage

```bash
# Check resource usage
kubectl top pods -n payroll-analytics
kubectl top nodes

# Check resource requests/limits
kubectl describe pod <pod-name> -n payroll-analytics
```

## 🐛 Troubleshooting

### Pod Not Starting

```bash
# Check events
kubectl describe pod <pod-name> -n payroll-analytics

# Check logs
kubectl logs <pod-name> -n payroll-analytics

# Check previous container logs (if crashed)
kubectl logs <pod-name> -n payroll-analytics --previous
```

### Database Connection Issues

```bash
# Test Postgres connectivity
kubectl run -it --rm psql --image=postgres:13 -n payroll-analytics -- \
  psql -h postgres -U airflow -d airflow

# Check Postgres logs
kubectl logs -l app=postgres -n payroll-analytics
```

### Service Account Permissions

```bash
# Verify service account exists
gcloud iam service-accounts list

# Grant necessary permissions
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:payroll-airflow-prod@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/bigquery.admin"
```

### Image Pull Errors

```bash
# Configure GCR access
kubectl create secret docker-registry gcr-json-key \
  --docker-server=gcr.io \
  --docker-username=_json_key \
  --docker-password="$(cat /path/to/key.json)" \
  -n payroll-analytics

# Add to deployment
# spec:
#   imagePullSecrets:
#   - name: gcr-json-key
```

## 🧹 Cleanup

### Delete All Resources

```bash
# Delete all resources in namespace
kubectl delete namespace payroll-analytics

# Or delete individually
kubectl delete -f k8s/airflow-deployment.yaml
kubectl delete -f k8s/postgres.yaml
kubectl delete -f k8s/cronjob-finops.yaml
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/namespace.yaml
```

### Delete GKE Cluster

```bash
gcloud container clusters delete payroll-analytics-cluster \
  --zone us-central1-a
```

## 💰 Cost Optimization

### Development Environment
- **Node Type**: n1-standard-2 (2 vCPU, 7.5 GB RAM)
- **Node Count**: 2-3 nodes
- **Estimated Cost**: ~$150/month

### Production Environment
- **Node Type**: n1-standard-4 (4 vCPU, 15 GB RAM)
- **Node Count**: 3-5 nodes (autoscaling)
- **Estimated Cost**: ~$500-800/month

### Cost-Saving Tips
1. Use preemptible nodes for non-critical workloads
2. Enable cluster autoscaling
3. Set resource requests/limits accurately
4. Use node auto-provisioning
5. Schedule non-urgent jobs during off-hours

```bash
# Create cluster with preemptible nodes
gcloud container clusters create payroll-analytics-cluster \
  --preemptible \
  --num-nodes 3 \
  --machine-type n1-standard-2
```

## 🔐 Security Best Practices

1. **Use Workload Identity** instead of service account keys
2. **Enable Network Policies** for pod-to-pod communication
3. **Use Pod Security Policies** to restrict container privileges
4. **Rotate secrets** regularly
5. **Enable audit logging** for compliance
6. **Use private GKE clusters** for production

```bash
# Enable Workload Identity
gcloud container clusters update payroll-analytics-cluster \
  --workload-pool=$GCP_PROJECT_ID.svc.id.goog \
  --zone us-central1-a
```

## 📚 Related Documentation

- [GKE Documentation](https://cloud.google.com/kubernetes-engine/docs)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Airflow on Kubernetes](https://airflow.apache.org/docs/apache-airflow/stable/kubernetes.html)
- [GCR Documentation](https://cloud.google.com/container-registry/docs)

---

**Deploy with confidence! 🚀**

