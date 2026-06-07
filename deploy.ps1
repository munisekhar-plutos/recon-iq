# Recon-IQ One-Click Direct Cloud Deployer (Windows PowerShell)
$ErrorActionPreference = "Stop"

# Configuration variables (Customizable)
# Retrieve active project ID from gcloud, or prompt the user if not configured
$ACTIVE_PROJECT = (gcloud config get-value project 2>$null)
if (-not $ACTIVE_PROJECT) {
    Write-Host "No active GCP project found in gcloud config." -ForegroundColor Yellow
    $PROJECT_ID = Read-Host "Please enter your GCP Project ID"
} else {
    Write-Host "Detected active GCP project from gcloud: $ACTIVE_PROJECT" -ForegroundColor Green
    $CHOICE = Read-Host "Press Enter to use '$ACTIVE_PROJECT', or enter a different GCP Project ID"
    if ($CHOICE) {
        $PROJECT_ID = $CHOICE.Trim()
    } else {
        $PROJECT_ID = $ACTIVE_PROJECT
    }
}
$REGION = "us-central1"
$SERVICE_NAME = "recon-iq-gateway"
$REPO_NAME = "recon-iq-repo"
$SERVICE_ACCOUNT_NAME = "recon-iq-cloud-runner"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Starting Recon-IQ Keyless Direct Cloud Deployment   " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Project Setup
Write-Host "Connecting to GCP project: $PROJECT_ID..." -ForegroundColor Yellow
gcloud config set project $PROJECT_ID

# 2. Enable APIs
Write-Host "Enabling required API services (Artifact Registry, Cloud Run, BigQuery, Vertex AI)..." -ForegroundColor Yellow
gcloud services enable `
    artifactregistry.googleapis.com `
    run.googleapis.com `
    bigquery.googleapis.com `
    aiplatform.googleapis.com

# 3. Create Artifact Registry
Write-Host "Verifying Artifact Registry repository..." -ForegroundColor Yellow
$repoExists = gcloud artifacts repositories describe $REPO_NAME --location=$REGION 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating Artifact Registry repo..." -ForegroundColor Gray
    gcloud artifacts repositories create $REPO_NAME `
        --repository-format=docker `
        --location=$REGION `
        --description="Recon-IQ Docker Repository"
}

# 4. Docker Auth
Write-Host "Configuring Docker credential helper..." -ForegroundColor Yellow
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# 5. Build and Push Container
$IMAGE_TAG = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"
Write-Host "Building local Docker container image: $IMAGE_TAG..." -ForegroundColor Yellow
docker build -t $IMAGE_TAG .

Write-Host "Uploading container image to GCP Artifact Registry..." -ForegroundColor Yellow
docker push $IMAGE_TAG

# 6. Setup Keyless Service Account
$SA_EMAIL = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
Write-Host "Verifying Cloud Service Account: $SA_EMAIL..." -ForegroundColor Yellow
$saExists = gcloud iam service-accounts describe $SA_EMAIL 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating service account..." -ForegroundColor Gray
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
        --display-name="Recon-IQ Cloud Runner Identity"
}

# 7. Bind permissions to Service Account
Write-Host "Binding required IAM permissions to service identity..." -ForegroundColor Yellow
# BigQuery Access
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA_EMAIL" `
    --role="roles/bigquery.admin" --quiet

# Vertex AI Access (Gemini)
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SA_EMAIL" `
    --role="roles/aiplatform.user" --quiet

# 8. Deploy to Cloud Run
Write-Host "Deploying container service to Google Cloud Run (Keyless mode)..." -ForegroundColor Yellow
gcloud run deploy $SERVICE_NAME `
    --image=$IMAGE_TAG `
    --service-account=$SA_EMAIL `
    --region=$REGION `
    --allow-unauthenticated `
    --quiet

Write-Host "======================================================" -ForegroundColor Green
Write-Host " Direct Deployment Completed Successfully!            " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Service Live URL:" -ForegroundColor Yellow
gcloud run services describe $SERVICE_NAME --region=$REGION --format="value(status.url)"
