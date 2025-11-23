# Google Cloud Storage Resources
# Buckets for data landing, archive, and temporary storage

# Create GCS buckets
resource "google_storage_bucket" "buckets" {
  for_each = var.gcs_buckets

  name          = "payroll-${each.key}-${var.environment}"
  location      = var.region
  storage_class = each.value.storage_class
  
  uniform_bucket_level_access = true
  
  labels = merge(
    local.labels,
    {
      purpose = each.key
    }
  )
  
  # Lifecycle rules
  lifecycle_rule {
    condition {
      age = each.value.lifecycle_age
    }
    action {
      type = "Delete"
    }
  }
  
  # Versioning for landing and archive buckets
  versioning {
    enabled = each.key == "landing" || each.key == "archive"
  }
  
  # Force destroy for dev environment
  force_destroy = var.environment == "dev"
}

# IAM bindings for buckets
resource "google_storage_bucket_iam_member" "airflow_landing" {
  bucket = google_storage_bucket.buckets["landing"].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "airflow_archive" {
  bucket = google_storage_bucket.buckets["archive"].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "airflow_temp" {
  bucket = google_storage_bucket.buckets["temp"].name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.airflow.email}"
}

resource "google_storage_bucket_iam_member" "dataform_landing" {
  bucket = google_storage_bucket.buckets["landing"].name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.dataform.email}"
}

