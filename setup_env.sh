#!/bin/bash
# Recon-IQ Automatic Environment & API Key Provisioner (Bash/Linux/macOS)
set -e

echo "======================================================"
echo " Starting Automatic Environment & API Key Provisioning "
echo "======================================================"

# 1. Detect Active Project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "\033[1;31mNo active GCP project found in gcloud. Please run: gcloud config set project YOUR_PROJECT_ID\033[0m"
    exit 1
fi

echo -e "\033[1;32mDetected active GCP project: $PROJECT_ID\033[0m"

# 2. Enable APIs
echo "Enabling Google Cloud APIs (apikeys, aiplatform, bigquery)..."
gcloud services enable apikeys.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com --quiet

# 3. Retrieve or Create API Key
echo "Searching for an existing API Key: 'Recon-IQ Gemini Key'..."
KEY_NAME=$(gcloud services api-keys list --format="value(name)" --filter="displayName='Recon-IQ Gemini Key'" | head -n 1)

if [ -z "$KEY_NAME" ]; then
    echo "Creating a new API Key named 'Recon-IQ Gemini Key' in project '$PROJECT_ID'..."
    KEY_NAME=$(gcloud services api-keys create --display-name="Recon-IQ Gemini Key" --format="value(name)")
fi

# 4. Get the Key String
echo "Extracting the secret API key string..."
API_KEY=$(gcloud services api-keys get-key-string "$KEY_NAME" --format="value(keyString)")

# 5. Write the .env file
echo "Writing local environment configuration file: .env..."
cat <<EOF > .env
# Recon-IQ Environment Configurations

# FastAPI configuration
APP_NAME=recon-iq

# MongoDB Metadata Warehouse
MONGO_URI=mongodb://recon-iq-metadata:27017/
MONGO_DB_NAME=recon_iq_metadata

# Google Cloud Platform (GCP)
GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/cloud_service_key.json
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=$PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1

# Google BigQuery Data Warehouse
BIGQUERY_DATASET=analytics_warehouse
BIGQUERY_TABLE=historical_ledger

# Google Gemini / Vertex AI
GEMINI_API_KEY=$API_KEY
GEMINI_MODEL=gemini-3.5-flash
EOF

echo "======================================================"
echo -e "\033[1;32m Environment Auto-Provisioned Successfully!           \033[0m"
echo "======================================================"
echo "Target Project: $PROJECT_ID"
echo "Gemini API Key: $API_KEY"
echo "Local file .env has been written with all parameters."
