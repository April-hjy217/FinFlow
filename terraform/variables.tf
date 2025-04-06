variable "gcp_project" {
  type = string
}
variable "gcp_region" {
  type    = string
  default = "us-central1"
}
variable "gcp_zone" {
  type    = string
  default = "us-central1-a"
}
variable "dataset_id" {
  type    = string
  default = "my_dataset"
}
