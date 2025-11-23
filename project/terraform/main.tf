# Main Terraform Configuration
# Payroll Analytics Platform - GCP Infrastructure

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  
  # Backend configuration for remote state (optional)
  # backend "gcs" {
  #   bucket = "payroll-terraform-state"
  #   prefix = "terraform/state"
  # }
}

# Provider configuration
provider "google" {
  project = var.project_id
  region  = var.region
}

# Local variables
locals {
  labels = {
    project     = "payroll-analytics"
    environment = var.environment
    managed_by  = "terraform"
  }
}

