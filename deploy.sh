#!/bin/bash
# Recon-IQ One-Click Direct Cloud Deployer (Bash/Linux/macOS)
set -e

# Configuration variables (Customizable)
# Retrieve active project ID from gcloud, or prompt the user if not configured
ACTIVE_PROJECT=$(gcloud config get-value project 2>/dev/null)
if [ -z "$ACTIVE_PROJECT" ]; then
    echo -e "\033[1;33mNo active GCP project found in gcloud config.\033[0m"
    read -p "Please enter your GCP Project ID: " PROJECT_ID
else
    echo -e "\033[1;32mDetected active GCP project from gcloud: $ACTIVE_PROJECT\033[0m"
    read -p "Press Enter to use '$ACTIVE_PROJECT', or enter a different GCP Project ID: " CHOICE
    if [ -n "$CHOICE" ]; then
        PROJECT_ID=$(echo "$CHOICE" | xargs)
    else
        PROJECT_ID="$ACTIVE_PROJECT"
    fi
fi
REGION="us-central1"
SERVICE_NAME="recon-iq-gateway"
REPO_NAME="recon-iq-repo"
SERVICE_ACCOUNT_NAME="recon-iq-cloud-runner"

echo "======================================================"
echo " Starting Recon-IQ Keyless Direct Cloud Deployment   "
echo "======================================================"

# 1. Project Setup
echo "Connecting to GCP project: $PROJECT_ID..."
gcloud config set project "$PROJECT_ID"

# 2. Enable APIs
echo "Enabling required API services (Artifact Registry, Cloud Run, BigQuery, Vertex AI)..."
gcloud services enable \
    artifactregistry.googleapis.com \
    run.googleapis.com \
    bigquery.googleapis.com \
    aiplatform.googleapis.com

# 3. Create Artifact Registry
echo "Verifying Artifact Registry repository..."
gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" &>/dev/null || \
gcloud artifacts repositories create "$REPO_NAME" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Recon-IQ Docker Repository"

# 4. Docker Auth
echo "Configuring Docker credential helper..."
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# 5. Build and Push Container
IMAGE_TAG="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$SERVICE_NAME:latest"
echo "Building local Docker container image: $IMAGE_TAG..."
docker build -t "$IMAGE_TAG" .

echo "Uploading container image to GCP Artifact Registry..."
docker push "$IMAGE_TAG"

# 6. Setup Keyless Service Account
SA_EMAIL="$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
echo "Verifying Cloud Service Account: $SA_EMAIL..."
gcloud iam service-accounts describe "$SA_EMAIL" &>/dev/null || \
gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
    --display-name="Recon-IQ Cloud Runner Identity"

# 7. Bind permissions to Service Account
echo "Binding required IAM permissions to service identity..."
# BigQuery Access
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/bigquery.admin" --quiet

# Vertex AI Access (Gemini)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user" --quiet

# 8. Deploy to Cloud Run
echo "Deploying container service to Google Cloud Run (Keyless mode)..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_TAG" \
    --service-account="$SA_EMAIL" \
    --region="$REGION" \
    --allow-unauthenticated \
    --quiet

echo "======================================================"
echo " Direct Deployment Completed Successfully!            "
echo "======================================================"
echo "Service Live URL:"
gcloud run services describe "$SERVICE_NAME" --region="$REGION" --format="value(status.url)"
