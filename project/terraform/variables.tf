# Terraform Variables
# Payroll Analytics Platform

variable "project_id" {
  description = "GCP Project ID"
  type        = string
  default     = "payroll-analytics-dev"
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "location" {
  description = "BigQuery location"
  type        = string
  default     = "US"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "bigquery_datasets" {
  description = "BigQuery datasets to create"
  type = map(object({
    description           = string
    default_table_expiration_ms = number
    delete_contents_on_destroy = bool
  }))
  default = {
    raw = {
      description                 = "Raw layer (Bronze) - external tables"
      default_table_expiration_ms = null
      delete_contents_on_destroy  = true
    }
    staging = {
      description                 = "Staging layer (Silver) - cleaned data"
      default_table_expiration_ms = 5184000000  # 60 days
      delete_contents_on_destroy  = true
    }
    warehouse = {
      description                 = "Warehouse layer (Gold) - dimensions & facts"
      default_table_expiration_ms = 63072000000  # 730 days (2 years)
      delete_contents_on_destroy  = false
    }
    marts = {
      description                 = "Marts layer (Platinum) - business aggregates"
      default_table_expiration_ms = 31536000000  # 365 days
      delete_contents_on_destroy  = false
    }
    assertions = {
      description                 = "Data quality assertions"
      default_table_expiration_ms = 2592000000  # 30 days
      delete_contents_on_destroy  = true
    }
  }
}

variable "gcs_buckets" {
  description = "GCS buckets to create"
  type = map(object({
    storage_class = string
    lifecycle_age = number
  }))
  default = {
    landing = {
      storage_class = "STANDARD"
      lifecycle_age = 30
    }
    archive = {
      storage_class = "NEARLINE"
      lifecycle_age = 730  # 2 years
    }
    temp = {
      storage_class = "STANDARD"
      lifecycle_age = 7
    }
  }
}

variable "enable_apis" {
  description = "List of GCP APIs to enable"
  type        = list(string)
  default = [
    "bigquery.googleapis.com",
    "storage.googleapis.com",
    "dataform.googleapis.com",
    "logging.googleapis.com",
    "monitoring.googleapis.com",
  ]
}

