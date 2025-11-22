variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "vm_labels" {
  description = "Labels to identify VMs to manage (format: key:value,key:value)"
  type        = string
  default     = "auto-schedule:true"
}

variable "vm_zones" {
  description = "Comma-separated list of zones to check for VMs"
  type        = string
  default     = "us-central1-a,us-central1-b,us-east1-b"
}

variable "scale_down_action" {
  description = "Action to perform when scaling down (STOP or SUSPEND)"
  type        = string
  default     = "STOP"
  
  validation {
    condition     = contains(["STOP", "SUSPEND"], var.scale_down_action)
    error_message = "scale_down_action must be either STOP or SUSPEND"
  }
}

variable "scale_up_action" {
  description = "Action to perform when scaling up (START or RESUME)"
  type        = string
  default     = "START"
  
  validation {
    condition     = contains(["START", "RESUME"], var.scale_up_action)
    error_message = "scale_up_action must be either START or RESUME"
  }
}

variable "scale_down_schedule" {
  description = "Cron schedule for scaling down VMs (default: Friday 6 PM)"
  type        = string
  default     = "0 18 * * 5"
}

variable "scale_up_schedule" {
  description = "Cron schedule for scaling up VMs (default: Monday 8 AM)"
  type        = string
  default     = "0 8 * * 1"
}

variable "timezone" {
  description = "Timezone for the Cloud Scheduler"
  type        = string
  default     = "America/New_York"
}

variable "function_timeout" {
  description = "Timeout for the Cloud Function in seconds"
  type        = number
  default     = 300
}
