# Recon-IQ Automatic Environment & API Key Provisioner (Windows PowerShell)
$ErrorActionPreference = "Stop"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Starting Automatic Environment & API Key Provisioning " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

# 1. Detect Active Project
$PROJECT_ID = $env:DEVSHELL_PROJECT_ID
if (-not $PROJECT_ID) {
    $PROJECT_ID = $env:GOOGLE_CLOUD_PROJECT
}
if (-not $PROJECT_ID) {
    $PROJECT_ID = (gcloud config get-value project 2>$null)
}

if (-not $PROJECT_ID) {
    Write-Error "No active GCP project found. Please run: gcloud config set project YOUR_PROJECT_ID"
    Exit 1
}

# Ensure the gcloud active config is set to this project
gcloud config set project $PROJECT_ID --quiet 2>$null | Out-Null

Write-Host "Detected active GCP project: $PROJECT_ID" -ForegroundColor Green

# 2. Enable APIs
Write-Host "Enabling Google Cloud APIs (apikeys, aiplatform, bigquery)..." -ForegroundColor Yellow
gcloud services enable apikeys.googleapis.com aiplatform.googleapis.com bigquery.googleapis.com --quiet

# 3. Retrieve or Create API Key
Write-Host "Searching for an existing API Key: 'Recon-IQ Gemini Key'..." -ForegroundColor Yellow
$keysJson = gcloud services api-keys list --format="json" | Out-String
$KEY_NAME = $null

if ($keysJson.Trim()) {
    $keys = $keysJson | ConvertFrom-Json
    # Check if we have an array or a single object
    if ($keys -is [array]) {
        $existingKey = $keys | Where-Object { $_.displayName -eq "Recon-IQ Gemini Key" }
    } else {
        $existingKey = if ($keys.displayName -eq "Recon-IQ Gemini Key") { $keys } else { $null }
    }
    
    if ($existingKey) {
        $KEY_NAME = $existingKey.name
        Write-Host "Found existing key: $KEY_NAME" -ForegroundColor Gray
    }
}

if (-not $KEY_NAME) {
    Write-Host "Creating a new API Key named 'Recon-IQ Gemini Key' in project '$PROJECT_ID'..." -ForegroundColor Yellow
    gcloud services api-keys create --display-name="Recon-IQ Gemini Key" --quiet | Out-Null
    
    # Query list again to get the actual key name, avoiding the async operation name
    $keysJson = gcloud services api-keys list --format="json" | Out-String
    if ($keysJson.Trim()) {
        $keys = $keysJson | ConvertFrom-Json
        if ($keys -is [array]) {
            $existingKey = $keys | Where-Object { $_.displayName -eq "Recon-IQ Gemini Key" }
        } else {
            $existingKey = if ($keys.displayName -eq "Recon-IQ Gemini Key") { $keys } else { $null }
        }
        if ($existingKey) {
            $KEY_NAME = $existingKey.name
        }
    }
}

# 4. Get the Key String
Write-Host "Extracting the secret API key string..." -ForegroundColor Yellow
$keyStringResult = gcloud services api-keys get-key-string $KEY_NAME --format="json" | Out-String | ConvertFrom-Json
$API_KEY = $keyStringResult.keyString

# 5. Write the .env file
Write-Host "Writing local environment configuration file: .env..." -ForegroundColor Yellow
$ENV_CONTENT = @"
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
"@

$ENV_CONTENT | Out-File -FilePath .env -Encoding utf8 -Force

Write-Host "======================================================" -ForegroundColor Green
Write-Host " Environment Auto-Provisioned Successfully!           " -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
Write-Host "Target Project: $PROJECT_ID" -ForegroundColor Yellow
Write-Host "Gemini API Key: $API_KEY" -ForegroundColor Yellow
Write-Host "Local file .env has been written with all parameters." -ForegroundColor Green
