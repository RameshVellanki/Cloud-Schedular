terraform {
  backend "gcs" {
    bucket = "gcp-tftbk"
    prefix = "cloud-schedular/terraform/state"
  }
}
