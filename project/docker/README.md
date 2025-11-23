# Docker Containers

Containerized deployment for Payroll Analytics Platform

## 📦 Docker Images

### 1. Airflow Image (`Dockerfile.airflow`)
**Base**: `apache/airflow:2.7.3-python3.10`

**Contains**:
- Apache Airflow with LocalExecutor (dev) / KubernetesExecutor (prod)
- All Python dependencies
- Published OSS modules (synthetic-payroll-lab, scd2-bq-engine, etc.)
- DAG files
- Utility scripts
- Great Expectations configuration

**Size**: ~2 GB

### 2. Utils Image (`Dockerfile.utils`)
**Base**: `python:3.10-slim`

**Contains**:
- Lightweight Python runtime
- All Python dependencies
- Published OSS modules
- Utility scripts only
- Great Expectations configuration

**Size**: ~500 MB

**Use Cases**:
- Running data quality checks
- FinOps monitoring
- One-off tasks
- Testing

## 🚀 Quick Start

### Local Development with Docker Compose

```bash
# Navigate to docker directory
cd project/docker

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Access Airflow UI
open http://localhost:8080
# Username: airflow
# Password: airflow
```

### Stop Services

```bash
docker-compose down

# Remove volumes too
docker-compose down -v
```

## 🛠️ Building Images

### Build All Images

```bash
cd project/docker
./build.sh
```

### Build Individual Images

```bash
# Airflow
docker build -f Dockerfile.airflow -t payroll/airflow:latest ..

# Utils
docker build -f Dockerfile.utils -t payroll/utils:latest ..
```

### Build for Specific Platform

```bash
# Build for ARM (Apple Silicon)
docker build --platform linux/arm64 -f Dockerfile.airflow -t payroll/airflow:latest ..

# Build for AMD64 (Intel/GCP)
docker build --platform linux/amd64 -f Dockerfile.airflow -t payroll/airflow:latest ..
```

## 📤 Pushing to GCR

### Prerequisites

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project payroll-analytics-prod

# Configure Docker
gcloud auth configure-docker
```

### Push Images

```bash
# Use the push script
./push.sh

# Or manually
export GCP_PROJECT_ID="payroll-analytics-prod"
docker tag payroll/airflow:latest gcr.io/$GCP_PROJECT_ID/airflow:latest
docker push gcr.io/$GCP_PROJECT_ID/airflow:latest
```

## 🔧 Docker Compose Services

### Services Defined

1. **postgres**
   - PostgreSQL 13
   - Airflow metadata database
   - Persistent volume for data

2. **airflow-webserver**
   - Airflow UI (port 8080)
   - 2 replicas (load balanced)
   - Health checks enabled

3. **airflow-scheduler**
   - Task scheduler
   - 1 replica
   - Health checks enabled

4. **airflow-init**
   - One-time initialization
   - Creates admin user
   - Sets up database

5. **utils**
   - Utility container
   - Runs in background
   - Use for ad-hoc tasks

### Volumes

- `postgres-db-volume` - Database data
- `airflow-logs` - Airflow task logs
- Mounted directories:
  - `../airflow/dags` → `/opt/airflow/dags`
  - `../scripts` → `/opt/airflow/scripts`
  - `../great_expectations` → `/opt/airflow/great_expectations`
  - `./keys` → `/opt/airflow/keys`

## 🔑 Service Account Keys

Place your GCP service account key in `docker/keys/`:

```bash
mkdir -p docker/keys
cp /path/to/service-account-key.json docker/keys/
```

⚠️ **NEVER commit keys to git!** (Already in .gitignore)

## 🧪 Testing Containers

### Test Airflow Image

```bash
# Run Airflow commands
docker run --rm payroll/airflow:latest airflow version

# List DAGs
docker run --rm payroll/airflow:latest airflow dags list

# Test DAG
docker run --rm payroll/airflow:latest airflow dags test payroll_main_pipeline 2024-01-01
```

### Test Utils Image

```bash
# Run data quality checks
docker run --rm \
  -v $(pwd)/keys:/app/keys \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/service-account-key.json \
  payroll/utils:latest \
  python /app/scripts/run_data_quality_checks.py

# Run FinOps monitoring
docker run --rm \
  -v $(pwd)/keys:/app/keys \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/keys/service-account-key.json \
  payroll/utils:latest \
  python /app/scripts/finops_monitoring.py --project-id your-project --days 7

# Run tests
docker run --rm payroll/utils:latest pytest /app/tests/ -v
```

### Interactive Shell

```bash
# Airflow container
docker run --rm -it payroll/airflow:latest /bin/bash

# Utils container
docker run --rm -it payroll/utils:latest /bin/bash
```

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs
docker logs <container-id>

# Check Docker daemon
docker ps -a

# Check resources
docker stats
```

### Database Connection Issues

```bash
# Check Postgres is running
docker ps | grep postgres

# Connect to Postgres
docker exec -it <postgres-container> psql -U airflow

# Check Airflow DB connection
docker exec -it <airflow-container> airflow db check
```

### Volume Permission Issues

```bash
# Set AIRFLOW_UID
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Rebuild
docker-compose down -v
docker-compose up -d
```

### Image Build Fails

```bash
# Clear Docker cache
docker builder prune -a

# Build without cache
docker build --no-cache -f Dockerfile.airflow -t payroll/airflow:latest ..
```

### Out of Disk Space

```bash
# Clean up unused images
docker system prune -a

# Remove all stopped containers
docker container prune

# Remove unused volumes
docker volume prune
```

## 📊 Resource Requirements

### Development (Docker Compose)
- **RAM**: 4 GB minimum, 8 GB recommended
- **CPU**: 2 cores minimum, 4 cores recommended
- **Disk**: 10 GB free space

### Production (Kubernetes)
- See `k8s/README.md` for details

## 🔒 Security

### Best Practices

1. **Don't run as root**
   ```dockerfile
   USER airflow  # Already implemented
   ```

2. **Use secrets management**
   ```bash
   # Use Docker secrets (Swarm) or K8s secrets
   docker secret create gcp_key service-account-key.json
   ```

3. **Scan images for vulnerabilities**
   ```bash
   docker scan payroll/airflow:latest
   ```

4. **Keep base images updated**
   ```bash
   docker pull apache/airflow:2.7.3-python3.10
   ./build.sh
   ```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push Docker Images

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v1
      
      - name: Login to GCR
        uses: docker/login-action@v1
        with:
          registry: gcr.io
          username: _json_key
          password: ${{ secrets.GCR_JSON_KEY }}
      
      - name: Build and push Airflow
        uses: docker/build-push-action@v2
        with:
          context: ./project
          file: ./project/docker/Dockerfile.airflow
          push: true
          tags: gcr.io/${{ secrets.GCP_PROJECT_ID }}/airflow:latest
```

## 📚 Related Documentation

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Apache Airflow Docker](https://airflow.apache.org/docs/docker-stack/index.html)
- [GCR Documentation](https://cloud.google.com/container-registry/docs)

---

**Containerize all the things! 🐳**

