project_id = "your-gcp-project-id"
region     = "us-central1"

# VM labels to identify which VMs to manage
# Format: "key:value,key:value"
vm_labels = "auto-schedule:true,environment:dev"

# Zones to check for VMs
vm_zones = "us-central1-a,us-central1-b,us-east1-b"

# Scale down action: STOP (completely stop) or SUSPEND (suspend to disk)
scale_down_action = "STOP"

# Scale up action: START (start stopped VMs) or RESUME (resume suspended VMs)
scale_up_action = "START"

# Cron schedules (in Cloud Scheduler format)
# Default: Scale down on Friday at 6 PM, scale up on Monday at 8 AM
scale_down_schedule = "0 18 * * 5"  # Friday 6 PM
scale_up_schedule   = "0 8 * * 1"   # Monday 8 AM

# Timezone for schedules
timezone = "America/New_York"

# Function timeout in seconds
function_timeout = 300
