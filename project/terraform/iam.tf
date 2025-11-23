# IAM Resources
# Service accounts and permissions

# Service Account for Airflow
resource "google_service_account" "airflow" {
  account_id   = "payroll-airflow-${var.environment}"
  display_name = "Payroll Analytics - Airflow Service Account"
  description  = "Service account for Airflow orchestration"
}

# Service Account for Dataform
resource "google_service_account" "dataform" {
  account_id   = "payroll-dataform-${var.environment}"
  display_name = "Payroll Analytics - Dataform Service Account"
  description  = "Service account for Dataform transformations"
}

# Service Account for Data Quality (Great Expectations)
resource "google_service_account" "data_quality" {
  account_id   = "payroll-dq-${var.environment}"
  display_name = "Payroll Analytics - Data Quality Service Account"
  description  = "Service account for Great Expectations"
}

# IAM roles for Airflow service account
resource "google_project_iam_member" "airflow_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_project_iam_member" "airflow_dataform_admin" {
  project = var.project_id
  role    = "roles/dataform.admin"
  member  = "serviceAccount:${google_service_account.airflow.email}"
}

# IAM roles for Dataform service account
resource "google_project_iam_member" "dataform_bigquery_admin" {
  project = var.project_id
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.dataform.email}"
}

resource "google_project_iam_member" "dataform_storage_viewer" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.dataform.email}"
}

# IAM roles for Data Quality service account
resource "google_project_iam_member" "dq_bigquery_data_viewer" {
  project = var.project_id
  role    = "roles/bigquery.dataViewer"
  member  = "serviceAccount:${google_service_account.data_quality.email}"
}

resource "google_project_iam_member" "dq_bigquery_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.data_quality.email}"
}

# Service account keys (for local development)
resource "google_service_account_key" "airflow_key" {
  service_account_id = google_service_account.airflow.name
}

resource "google_service_account_key" "dataform_key" {
  service_account_id = google_service_account.dataform.name
}

resource "google_service_account_key" "data_quality_key" {
  service_account_id = google_service_account.data_quality.name
}

# Save keys to local files (for development only)
resource "local_sensitive_file" "airflow_key_file" {
  content  = base64decode(google_service_account_key.airflow_key.private_key)
  filename = "${path.module}/keys/airflow-sa-key.json"
}

resource "local_sensitive_file" "dataform_key_file" {
  content  = base64decode(google_service_account_key.dataform_key.private_key)
  filename = "${path.module}/keys/dataform-sa-key.json"
}

resource "local_sensitive_file" "data_quality_key_file" {
  content  = base64decode(google_service_account_key.data_quality_key.private_key)
  filename = "${path.module}/keys/data-quality-sa-key.json"
}

