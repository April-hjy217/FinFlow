provider "google" {
  project = var.gcp_project
  region  = var.gcp_region
  zone    = var.gcp_zone


credentials = file("${path.module}/../credentials/key.json")
}

# 1) Enable Cloud Resource Manager
resource "google_project_service" "enable_resource_manager" {
  project = var.gcp_project
  service = "cloudresourcemanager.googleapis.com"
}

# 2) Enable IAM API 
resource "google_project_service" "enable_iam_api" {
  project = var.gcp_project
  service = "iam.googleapis.com"
  depends_on = [google_project_service.enable_resource_manager]
}

# 3) GCS bucket
resource "google_storage_bucket" "data_lake" {
  name          = "${var.gcp_project}-data-lake"
  location      = var.gcp_region
  force_destroy = true
}

# 4) BigQuery dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.dataset_id
  project    = var.gcp_project
  location   = var.gcp_region
}


# 5) Service account for accessing GCS/BigQuery
#    Depends on google_project_service.enable_iam_api

resource "google_service_account" "airflow_sa" {
  depends_on   = [google_project_service.enable_iam_api]
  account_id   = "airflow-service-account"
  display_name = "Airflow Service Account"
}

# 6) Assign roles
resource "google_project_iam_member" "airflow_sa_roles" {
  project = var.gcp_project
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.airflow_sa.email}"

  depends_on = [google_service_account.airflow_sa]
}

resource "google_project_iam_member" "airflow_sa_storage_roles" {
  project = var.gcp_project
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.airflow_sa.email}"

  depends_on = [google_service_account.airflow_sa]
}
