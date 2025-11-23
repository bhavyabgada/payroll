# BigQuery Resources
# Datasets for each layer of the data pipeline

# Create BigQuery datasets
resource "google_bigquery_dataset" "datasets" {
  for_each = var.bigquery_datasets

  dataset_id    = "payroll_${each.key}"
  friendly_name = "Payroll Analytics - ${title(each.key)} Layer"
  description   = each.value.description
  location      = var.location
  
  default_table_expiration_ms = each.value.default_table_expiration_ms
  delete_contents_on_destroy  = each.value.delete_contents_on_destroy
  
  labels = merge(
    local.labels,
    {
      layer = each.key
    }
  )
  
  access {
    role          = "OWNER"
    user_by_email = google_service_account.dataform.email
  }
  
  access {
    role          = "READER"
    special_group = "projectReaders"
  }
  
  access {
    role          = "WRITER"
    user_by_email = google_service_account.airflow.email
  }
}

# BigQuery connection for external data sources (optional)
resource "google_bigquery_connection" "external_connection" {
  connection_id = "payroll_external_connection"
  location      = var.region
  friendly_name = "External Data Connection"
  description   = "Connection for external tables (GCS)"
  
  cloud_resource {}
}

# Grant connection access to GCS
resource "google_project_iam_member" "external_connection_gcs" {
  project = var.project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_bigquery_connection.external_connection.cloud_resource[0].service_account_id}"
}

