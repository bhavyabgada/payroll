# Terraform Outputs
# Export important resource information

# BigQuery Dataset IDs
output "bigquery_datasets" {
  description = "Map of BigQuery dataset IDs"
  value = {
    for k, v in google_bigquery_dataset.datasets : k => v.dataset_id
  }
}

# GCS Bucket Names
output "gcs_buckets" {
  description = "Map of GCS bucket names"
  value = {
    for k, v in google_storage_bucket.buckets : k => v.name
  }
}

# Service Account Emails
output "service_accounts" {
  description = "Map of service account emails"
  value = {
    airflow      = google_service_account.airflow.email
    dataform     = google_service_account.dataform.email
    data_quality = google_service_account.data_quality.email
  }
}

# BigQuery Connection
output "bigquery_connection_id" {
  description = "BigQuery external connection ID"
  value       = google_bigquery_connection.external_connection.name
}

# Project Information
output "project_info" {
  description = "Project configuration information"
  value = {
    project_id  = var.project_id
    region      = var.region
    environment = var.environment
  }
}

# Service Account Key Locations (sensitive)
output "service_account_key_files" {
  description = "Locations of service account key files"
  value = {
    airflow      = local_sensitive_file.airflow_key_file.filename
    dataform     = local_sensitive_file.dataform_key_file.filename
    data_quality = local_sensitive_file.data_quality_key_file.filename
  }
  sensitive = true
}

