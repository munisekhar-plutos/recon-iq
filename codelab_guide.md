# Build a High-Precision Financial Reconciliation Agent with Recon-IQ and google-adk 🚀

## 1. Introduction
**Duration: 2 mins**

In this Codelab, you will build and run **Recon-IQ**, an enterprise-grade, AI-powered financial reconciliation engine. The system leverages the **Google Agent Development Kit (ADK)** alongside Gemini 3.5 Flash and BigQuery to ingest multi-format transaction logs, align column schemas bidirectionally, perform high-precision reconciliation, and expose an interactive conversational AI interface modeled after Anthropic's Claude chatbot.

You will learn how to run the system both in a highly containerized local microservices environment (using Docker Compose) and how to deploy the entire containerized gateway keylessly to Google Cloud Run!

### What you'll build and learn:
- **High-Precision matching**: Run a Python Decimal Matching Engine that compares payment logs to a strict $0.001$ threshold.
- **Dynamic AI Schema Alignment**: Align arbitrary spreadsheet column names with system primitives.
- **Conversational BigQuery Analytics**: Query a date-partitioned ledger in BigQuery using natural language SQL generation.
- **Interactive Visualizations**: Render real-time Vega-Lite bar charts and markdown forensic tables inside a Claude-inspired UI.
- **Keyless Direct Deployments**: Use OIDC-capable direct deployment scripts to push code safely to Google Cloud.

> [!IMPORTANT]
> This guide is designed for developers of all levels. No advanced Python or DevOps knowledge is required!

---

## 2. Before you begin
**Duration: 5 mins**

### Create a Google Cloud Project
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Select or [create a new Google Cloud project](https://cloud.google.com/resource-manager/docs/creating-managing-projects).
3. Confirm that **Billing** is enabled for your project. [Learn how to check billing status](https://cloud.google.com/billing/docs/how-to/verify-billing-enabled).

### Authenticate your Developer Machine
Ensure you have the Google Cloud SDK (`gcloud`) installed on your system. Run these commands in your shell to authenticate and configure your local project:

```powershell
# Authenticate your account
gcloud auth login

# Set your active project ID
gcloud config set project YOUR_GCP_PROJECT_ID

# Authorize your local application environment (Application Default Credentials)
gcloud auth application-default login
```

> [!IMPORTANT]
> **Permission Denied / Troubleshooting `AUTH_PERMISSION_DENIED`:**
> If you encounter an error like `AUTH_PERMISSION_DENIED` or `Permission denied to enable service` when running the setup script, it means your active GCP user account does not have sufficient permissions (such as `Owner`, `Editor`, or `Service Usage Admin` + `API Keys Admin` roles) on the current project.
> 
> To resolve this:
> 1. Ensure you set `gcloud config set project` to a project where you have administrative access (e.g., your personal sandbox project or a pre-prod project).
> 2. You can view all projects available to your account by running:
>    ```bash
>    gcloud projects list
>    ```
> 3. Switch to a personal/sandbox project if needed:
>    ```bash
>    gcloud config set project <your-sandbox-project-id>
>    ```

---

## 3. Clone the Repository & Configure Environment
**Duration: 5 mins**

### Get the Code
Clone the repository to your local computer and enter the project directory:

```bash
git clone https://github.com/munisekhar-plutos/recon-iq.git
cd recon-iq
```

### Configure your Local Environment (One-Click Auto-Setup)

Instead of manually creating a `.env` file, enabling Google APIs, and generating/copying an API key, you can run a **single automated script** that does it all for you! This script will automatically:
1. Detect your current active `gcloud` project.
2. Enable all required APIs in your GCP project (including the `apikeys`, `aiplatform`, and `bigquery` services).
3. Check if a secure API Key named `"Recon-IQ Gemini Key"` exists, and if not, **automatically generate one** under your GCP account.
4. Retrieve the secret API key string and dynamically write a complete, perfectly configured `.env` file!

Run the appropriate command for your platform:

#### Windows (PowerShell)
```powershell
.\setup_env.ps1
```

#### macOS/Linux (Bash)
```bash
chmod +x setup_env.sh
./setup_env.sh
```

---

### Manual Environment Template (Optional Fallback)
If you prefer to configure your parameters manually, create a `.env` file in the project root and populate it with your own settings:

```ini
# Recon-IQ Environment Configurations

# FastAPI configuration
APP_NAME=recon-iq

# MongoDB Metadata Warehouse
MONGO_URI=mongodb://recon-iq-metadata:27017/
MONGO_DB_NAME=recon_iq_metadata

# Google Cloud Platform (GCP)
GOOGLE_GENAI_USE_VERTEXAI=True
GOOGLE_CLOUD_PROJECT=YOUR_GCP_PROJECT_ID
GOOGLE_CLOUD_LOCATION=us-central1

# Google BigQuery Data Warehouse
BIGQUERY_DATASET=analytics_warehouse
BIGQUERY_TABLE=historical_ledger

# Google Gemini / Vertex AI
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
```

> [!WARNING]
> Keep your `.env` secure and never commit it to your public git ledger. A standard `.gitignore` has been pre-configured in the repository to protect your credentials.

---

## 4. Install Project Requirements
**Duration: 5 mins**

To run unit tests or launch the native ADK debugging server, create a Python virtual environment and install the required modules:

### Windows (PowerShell)
```powershell
# Initialize Python virtual environment
python -m venv .venv

# Activate the virtual environment
.\.venv\Scripts\Activate.ps1

# Install requirements & google-adk CLI
pip install -r requirements.txt
pip install google-adk==1.28.0
```

### macOS/Linux (Bash)
```bash
# Initialize Python virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Install requirements & google-adk CLI
pip install -r requirements.txt
pip install google-adk==1.28.0
```

---

## 5. Run and Test the Application Locally
**Duration: 10 mins**

You are now ready to spin up the local services. You can start the background metadata server and the FastAPI gateway with Docker Compose:

### 1. Launch the Microservices Stack
```bash
docker compose up -d
```
This orchestrates:
- **FastAPI Gateway**: Running on `http://localhost:8000/`.
- **MongoDB Metadata Warehouse**: Persistent database on port `27017` for session logs.
- **Mongo Express Portal**: Web-based administration panel on `http://localhost:8081/` (Username: `admin`, Password: `pass`).

### 2. Run the Verification Tests
To confirm that your local environment is fully operational, run the high-precision unit tests inside the running gateway container:
```bash
docker compose exec recon-iq-gateway python -m unittest tests/test_recon_iq.py
```
*You should see all 4 unit test suites execute and return a clean `OK`!*

---

## 6. Chat with your Reconciliation Agent!
**Duration: 10 mins**

Now comes the fun part! Open your web browser and navigate to:
👉 **[http://localhost:8000/](http://localhost:8000/)**

This renders a state-of-the-art, **Anthropic Claude-inspired Web UI** connected directly to your FastAPI gateway. 

### Try Ingesting some Transactions:
1. Navigate to the **Upload Transactions** section.
2. Ingest a sample financial settlement spreadsheet (CSV, XML, or XLSX format).
3. Watch the Gemini-powered aligner analyze your columns in real-time and map them to standard fields like `transaction_id`, `amount`, and `timestamp`!

### Try Asking your Agent these Analytical Questions:
Type the following inquiries into the Chat Interface to activate the google-adk cognitive BigQuery generator:

1. **Ask for an Overview**: 
   *"Generate a daily forensic report summarizing transaction discrepancies for today."*
   *(The UI will render a gorgeous markdown board detailing precise ledger variances exceeding the $0.001$ threshold).*

2. **Ask for a Trend Chart**: 
   *"Visualize the monthly reconciliation match rate for the last trailing 12 months."*
   *(The agent will construct a SQL query, fetch matched vs. mismatched data, and return a live interactive **Vega-Lite** bar chart).*

---

## 7. Deploy Keylessly to Google Cloud Run
**Duration: 8 mins**

When you are ready to push the application to production, you can deploy it to **any** Google Cloud project using our zero-dependency, one-click deployers. These scripts will automatically ask you to confirm your active project or enter a custom one!

### Native Windows Deployer (PowerShell)
```powershell
.\deploy.ps1
```

### Linux/macOS Deployer (Bash)
```bash
chmod +x deploy.sh
./deploy.sh
```

### What these scripts automate:
1. **Interactive Target Selection**: Safely prompts you to confirm or change your target GCP Project ID.
2. **API Enablement**: Activates Cloud Run, Artifact Registry, BigQuery, and Vertex AI.
3. **Keyless Service Identity**: Creates a secure Google Service Account (`recon-iq-cloud-runner`) with read-only BigQuery and Vertex AI cognitive query rights.
4. **Image Compile**: Builds your Docker container and uploads it to Artifact Registry.
5. **Live Deployment**: Deploys the service to Cloud Run and returns a fully-secured public URL!

---

## 8. Congratulations!
**Duration: 1 min**

**Mission Accomplished!** 🎉  
You have built a highly secure, enterprise-grade AI Financial Reconciliation Engine. 

### What you accomplished:
- **MVC Architecture**: Designed a highly modular FastAPI application.
- **Robust Ingestion**: Configured dynamic XML namespace flattening and Excel streaming.
- **Base-10 Arithmetic**: Implemented precise Python Decimal math to prevent standard float representation drift.
- **Cognitive Agent**: Connected the Google Agent SDK (ADK) to BigQuery to answer questions via natural SQL generation.
- **Stunning UI**: Serves a premium Claude-styled interface featuring responsive Vega-Lite components.
- **Keyless GCP Pipeline**: Implemented OIDC-compliant one-click deployment pipelines to Google Cloud Run!

Feel free to customize the system instruction prompts in `app/controllers/agent.py` to tailor the cognitive analyst to your specific financial ledgers!
