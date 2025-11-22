# Google Cloud VM Scheduler

Automated solution for scaling up and down virtual machines in Google Cloud Platform during weekends for cloud cost optimization. This project uses **Cloud Functions (2nd gen)**, **Cloud Scheduler**, **Pub/Sub**, and **Terraform** for infrastructure as code.

## 📊 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GitHub Actions (CI/CD)                      │
│                                                                     │
│  ┌──────────────┐      ┌──────────────┐      ┌─────────────────┐ │
│  │   Validate   │ -->  │  Terraform   │ -->  │  Deploy to GCP  │ │
│  │   (PR/Push)  │      │     Plan     │      │   (Push main)   │ │
│  └──────────────┘      └──────────────┘      └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                            │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │                   Terraform State (GCS)                    │   │
│  │            Bucket: gcp-tftbk (existing)                    │   │
│  │        Prefix: cloud-schedular/terraform/state             │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌──────────────────────┐        ┌──────────────────────┐         │
│  │  Cloud Scheduler     │        │  Cloud Scheduler     │         │
│  │  (Scale Down)        │        │  (Scale Up)          │         │
│  │  Cron: Fri 6 PM      │        │  Cron: Mon 8 AM      │         │
│  └──────────┬───────────┘        └──────────┬───────────┘         │
│             │                               │                      │
│             ▼                               ▼                      │
│  ┌──────────────────────┐        ┌──────────────────────┐         │
│  │   Pub/Sub Topic      │        │   Pub/Sub Topic      │         │
│  │   vm-scale-down      │        │   vm-scale-up        │         │
│  └──────────┬───────────┘        └──────────┬───────────┘         │
│             │                               │                      │
│             └───────────────┬───────────────┘                      │
│                             ▼                                      │
│              ┌──────────────────────────────┐                     │
│              │   Cloud Function (Gen 2)     │                     │
│              │      vm-scheduler            │                     │
│              │   • Python 3.11              │                     │
│              │   • Eventarc Trigger         │                     │
│              │   • Service Account Auth     │                     │
│              └──────────────┬───────────────┘                     │
│                             │                                      │
│                             ▼                                      │
│              ┌──────────────────────────────┐                     │
│              │   Compute Engine API         │                     │
│              │   • List VMs by labels       │                     │
│              │   • Stop/Start instances     │                     │
│              │   • Suspend/Resume instances │                     │
│              └──────────────┬───────────────┘                     │
│                             │                                      │
│                             ▼                                      │
│        ┌────────────────────────────────────────┐                │
│        │          Virtual Machines               │                │
│        │  (Filtered by labels)                   │                │
│        │                                         │                │
│        │  ┌──────┐  ┌──────┐  ┌──────┐         │                │
│        │  │ VM 1 │  │ VM 2 │  │ VM 3 │  ...    │                │
│        │  │ dev  │  │ dev  │  │ test │         │                │
│        │  └──────┘  └──────┘  └──────┘         │                │
│        │  Label: auto-schedule=true             │                │
│        └────────────────────────────────────────┘                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 🎯 Key Features

- ⏰ **Automated Scheduling**: Set custom cron schedules for scale up/down
- 🏷️ **Label-based Targeting**: Manage VMs using GCP labels
- 🔒 **Secure**: Workload Identity Federation (no service account keys)
- 📦 **Infrastructure as Code**: Complete Terraform configuration
- 🚀 **CI/CD Ready**: GitHub Actions for automated deployment
- 💰 **Cost Optimization**: Save ~29% on compute costs
- 🔄 **State Management**: Remote state with versioning and locking
- 🧪 **Easy Testing**: Manual trigger via GitHub Actions UI

## 📋 Prerequisites

- Google Cloud Platform account with billing enabled
- GitHub repository (for CI/CD automation)
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) - for local development
- [Terraform](https://www.terraform.io/downloads) >= 1.0 - for manual deployment (optional)

## 🚀 Complete Setup Guide

### Step 1: Configure Project Settings

Edit `terraform/terraform.tfvars` with your configuration:

```hcl
project_id = "your-gcp-project-id"
region     = "us-central1"

# VM labels to identify which VMs to manage
vm_labels = "auto-schedule:true,environment:dev"

# Zones to check for VMs
vm_zones = "us-central1-a,us-central1-b,us-east1-b"

# Scale actions: STOP/START or SUSPEND/RESUME
scale_down_action = "STOP"
scale_up_action   = "START"

# Cron schedules (Cloud Scheduler format)
scale_down_schedule = "0 18 * * 5"  # Friday 6 PM
scale_up_schedule   = "0 8 * * 1"   # Monday 8 AM

timezone = "America/New_York"
```

### Step 2: Label Your VMs

Tag VMs you want to manage with appropriate labels:

**Option 1 - gcloud CLI**:
```bash
gcloud compute instances add-labels INSTANCE_NAME \
  --labels=auto-schedule=true,environment=dev \
  --zone=us-central1-a
```

**Option 2 - Console**:
1. Go to Compute Engine → VM instances
2. Click on instance → Edit
3. Add labels: `auto-schedule: true`, `environment: dev`
4. Save

**Option 3 - Terraform**:
```hcl
resource "google_compute_instance" "example" {
  name         = "my-vm"
  machine_type = "n1-standard-1"
  zone         = "us-central1-a"
  
  labels = {
    auto-schedule = "true"
    environment   = "dev"
  }
  # ... other configuration
}
```

### Step 3: Set Up GitHub Actions (Recommended)

#### 3.1 Enable Required APIs

```bash
export PROJECT_ID="your-gcp-project-id"

gcloud services enable \
  iamcredentials.googleapis.com \
  sts.googleapis.com \
  cloudresourcemanager.googleapis.com \
  storage.googleapis.com \
  --project="${PROJECT_ID}"
```

#### 3.2 Get Project Number

```bash
export PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} \
  --format='value(projectNumber)')
echo "Project Number: ${PROJECT_NUMBER}"
```

#### 3.3 Create Workload Identity Pool

```bash
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"
```

#### 3.4 Create Workload Identity Provider

```bash
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

#### 3.5 Create Service Account

```bash
gcloud iam service-accounts create github-actions \
  --project="${PROJECT_ID}" \
  --display-name="GitHub Actions Deployment"

# Grant necessary permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/editor"
```

#### 3.6 Allow GitHub to Impersonate Service Account

Replace with your GitHub username and repo name:

```bash
export GITHUB_REPO="YOUR_GITHUB_USERNAME/Cloud-Schedular"

gcloud iam service-accounts add-iam-policy-binding \
  "github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"
```

#### 3.7 Get Workload Identity Provider Name

```bash
gcloud iam workload-identity-pools providers describe "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --format="value(name)"
```

Copy the output (looks like: `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider`)

#### 3.8 Configure GitHub Secrets

1. Go to your GitHub repository
2. Navigate to: **Settings** → **Secrets and variables** → **Actions**
3. Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Output from step 3.7 |
| `GCP_SERVICE_ACCOUNT` | `github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com` |

#### 3.9 Deploy

```bash
git add .
git commit -m "Deploy VM Scheduler"
git push origin main
```

The GitHub Actions workflow will automatically:
- Create the Terraform state bucket
- Initialize Terraform
- Plan and apply the infrastructure
- Deploy Cloud Functions and schedulers

### Alternative: Manual Deployment

```bash
cd terraform

# Authenticate
gcloud auth application-default login

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

### Step 4: Verify Deployment

```bash
# Check deployed resources
gcloud functions list --project=${PROJECT_ID}
gcloud scheduler jobs list --project=${PROJECT_ID}
gcloud pubsub topics list --project=${PROJECT_ID}

# View function logs
gcloud functions logs read vm-scheduler \
  --project=${PROJECT_ID} \
  --region=us-central1 \
  --limit=50
```

## 🧪 Testing

### Option 1: Manual Trigger via GitHub Actions

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Select **Manual VM Scaling** workflow
4. Click **Run workflow**
5. Choose action (`scale_down` or `scale_up`)
6. Click **Run workflow**

The workflow will publish a message to Pub/Sub and show the function logs.

### Option 2: Manual Testing via gcloud CLI

Test the scale-down operation:
```bash
gcloud pubsub topics publish vm-scale-down \
  --project="YOUR_PROJECT_ID" \
  --message='{"action":"scale_down","project_id":"YOUR_PROJECT_ID"}'
```

Test the scale-up operation:
```bash
gcloud pubsub topics publish vm-scale-up \
  --project="YOUR_PROJECT_ID" \
  --message='{"action":"scale_up","project_id":"YOUR_PROJECT_ID"}'
```

### Check Function Logs

```bash
gcloud functions logs read vm-scheduler \
  --project=YOUR_PROJECT_ID \
  --region=us-central1 \
  --limit=50
```

## 📅 Schedule Configuration

The schedules use standard cron format: `minute hour day month day_of_week`

### Common Schedule Examples

```hcl
# Friday 6 PM
scale_down_schedule = "0 18 * * 5"

# Monday 8 AM
scale_up_schedule = "0 8 * * 1"

# Every day at 7 PM
scale_down_schedule = "0 19 * * *"

# Every day at 7 AM
scale_up_schedule = "0 7 * * *"

# Saturday 12 AM (midnight Friday)
scale_down_schedule = "0 0 * * 6"

# Multiple times a day (8 AM and 6 PM)
# Create separate scheduler jobs
```

### Timezone

Set the timezone in `terraform.tfvars`:
```hcl
timezone = "America/New_York"      # Eastern Time
timezone = "America/Los_Angeles"   # Pacific Time
timezone = "Europe/London"         # UK
timezone = "Asia/Tokyo"            # Japan
```

[Full timezone list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones)

## ⚙️ Configuration Options

### VM Selection

**Option 1: By Labels** (Recommended)
```hcl
vm_labels = "auto-schedule:true,environment:dev"
vm_zones  = "us-central1-a,us-central1-b"
```

**Option 2: Modify for specific instances**
Edit `main.py` to hardcode specific instances if needed.

### Scale Actions

**STOP vs SUSPEND**:
- **STOP**: Completely stops the VM (no memory preserved, slower restart)
- **SUSPEND**: Suspends to disk (memory preserved, faster restart, charges for disk)

```hcl
scale_down_action = "STOP"     # or "SUSPEND"
scale_up_action   = "START"    # or "RESUME"
```

## 💰 Cost Optimization

### Estimated Savings

For a VM running 24/7 vs weekends-off:
- **Normal operation**: 168 hours/week
- **With weekend shutdown**: 120 hours/week
- **Savings**: ~29% on compute costs

Example:
- n1-standard-4 VM: $140/month → $99/month = **$41/month saved per VM**

### Service Costs

- **Cloud Functions**: Free tier covers most usage (~2 invocations/week)
- **Cloud Scheduler**: Free tier covers up to 3 jobs
- **Pub/Sub**: First 10 GB free
- **Total additional cost**: ~$0-1/month

## 🔒 Security & Permissions

The Terraform configuration automatically creates:

1. **Service Account**: `vm-scheduler-sa`
   - `roles/compute.instanceAdmin.v1`: Stop/start VMs
   - `roles/compute.viewer`: List VMs

2. **Scheduler Service Account**: `vm-scheduler-invoker`
   - `roles/pubsub.publisher`: Publish to Pub/Sub topics

### Least Privilege Principle

The service accounts have minimal required permissions. Review and adjust based on your security requirements.

## 🛠️ Troubleshooting

### Issue: VMs not stopping/starting

**Check**:
1. VM labels match configuration
2. VMs are in specified zones
3. Function has correct permissions
4. Check function logs for errors

```bash
gcloud functions logs read vm-scheduler \
  --project=YOUR_PROJECT_ID \
  --region=us-central1
```

### Issue: Scheduler not triggering

**Check**:
1. Scheduler jobs are enabled
2. Timezone is correct
3. Cron schedule is valid

```bash
gcloud scheduler jobs list --project=YOUR_PROJECT_ID
gcloud scheduler jobs describe vm-scale-down-weekend --project=YOUR_PROJECT_ID
```

### Issue: Permission denied errors

**Fix**:
```bash
# Ensure APIs are enabled
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudscheduler.googleapis.com
gcloud services enable compute.googleapis.com

# Re-apply Terraform to fix IAM
cd terraform
terraform apply
```

## 📊 Monitoring

### View Logs

```bash
# Function logs
gcloud functions logs read vm-scheduler --limit=50

# Scheduler logs
gcloud scheduler jobs describe vm-scale-down-weekend

# List recent executions
gcloud scheduler jobs executions list vm-scale-down-weekend
```

### Set Up Alerts

Create alerts in Cloud Monitoring for:
- Function execution failures
- Scheduler job failures
- VM state changes

## 🔄 Updates and Maintenance

### Update Configuration

1. Modify `terraform.tfvars`
2. Run `terraform apply`

### Update Function Code

1. Modify `main.py`
2. Run `terraform apply` (Terraform will detect changes and redeploy)

### Destroy Resources

```bash
cd terraform
terraform destroy
```

## 🔧 Technical Details

### Terraform Backend

**State Storage**:
- **Bucket**: `gcp-tftbk` (existing bucket)
- **Prefix**: `cloud-schedular/terraform/state`
- **Versioning**: Managed on existing bucket
- **Locking**: Automatic via GCS
- **Access**: IAM-controlled

**State Commands**:
```bash
# View current state
terraform state list

# Show specific resource
terraform state show google_cloudfunctions2_function.vm_scheduler

# Pull state for inspection
terraform state pull > state.json

# Force unlock if needed
terraform force-unlock LOCK_ID
```

### Cloud Function Specifications

| Property | Value |
|----------|-------|
| **Runtime** | Python 3.11 |
| **Trigger** | Eventarc (Pub/Sub) |
| **Memory** | 256Mi |
| **Timeout** | 300 seconds |
| **Concurrency** | 1 instance max |
| **Auth** | Service Account |

**Environment Variables**:
```bash
GCP_PROJECT=your-project-id          # Project ID
VM_LABELS=auto-schedule:true         # Labels to filter VMs
VM_ZONES=us-central1-a,us-central1-b # Zones to check
SCALE_DOWN_ACTION=STOP               # STOP or SUSPEND
SCALE_UP_ACTION=START                # START or RESUME
```

### IAM & Security Model

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Architecture                    │
└─────────────────────────────────────────────────────────────┘

GitHub Actions (CI/CD)
  │
  └─> Workload Identity Federation (No Keys!)
        │
        └─> github-actions@PROJECT.iam.gserviceaccount.com
              │
              └─> roles/editor (Deploy Infrastructure)


Cloud Scheduler
  │
  └─> vm-scheduler-invoker@PROJECT.iam.gserviceaccount.com
        │
        └─> roles/pubsub.publisher (Publish Messages)


Cloud Function
  │
  └─> vm-scheduler-sa@PROJECT.iam.gserviceaccount.com
        │
        ├─> roles/compute.instanceAdmin.v1 (Start/Stop VMs)
        └─> roles/compute.viewer (List VMs)
```

**Security Best Practices**:
- ✅ Workload Identity Federation (no service account keys)
- ✅ Least privilege IAM roles
- ✅ Versioned state with audit logs
- ✅ Automated deployments from GitHub only
- ✅ No secrets in code or version control

## 📁 Project Structure

```
Cloud-Schedular/
├── main.py                          # Cloud Function code (Python 3.11)
├── requirements.txt                 # Python dependencies
├── .gcloudignore                    # Files excluded from function deployment
├── .gitignore                       # Git ignore patterns
├── README.md                        # Complete documentation (this file)
├── .github/
│   └── workflows/
│       ├── deploy.yml               # CI/CD: Deploy on push to main
│       ├── validate.yml             # CI/CD: Validate on pull requests
│       └── manual-trigger.yml       # Manual VM scaling trigger
└── terraform/
    ├── main.tf                      # Provider configuration
    ├── backend.tf                   # GCS backend for state (uses gcp-tftbk)
    ├── variables.tf                 # Input variables with validation
    ├── resources.tf                 # All GCP resources
    ├── outputs.tf                   # Deployment outputs
    └── terraform.tfvars             # Your configuration (committed)
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## 📝 License

This project is open source and available under the MIT License.

## 🔗 Related Resources

- [Google Cloud Functions Documentation](https://cloud.google.com/functions/docs)
- [Cloud Scheduler Documentation](https://cloud.google.com/scheduler/docs)
- [Terraform Google Provider](https://registry.terraform.io/providers/hashicorp/google/latest/docs)
- [Compute Engine API Reference](https://cloud.google.com/compute/docs/reference/rest/v1/instances)

## ⚠️ Important Notes

1. **Test in non-production first**: Always test in a dev environment before production
2. **Backup important data**: Ensure critical VMs are backed up
3. **Review schedules**: Double-check timezones and cron expressions
4. **Cost monitoring**: Monitor your GCP billing to verify savings
5. **Persistent disks**: Standard persistent disks continue to incur charges when VMs are stopped

## 📧 Support

For issues and questions:
- Open an issue in the repository
- Check Cloud Function logs for detailed error messages
- Review GCP documentation for API-specific issues
