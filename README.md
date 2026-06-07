# Recon-IQ AI Financial Reconciliation Engine 🚀

Recon-IQ is an enterprise-grade, AI-powered financial reconciliation system built using a decoupled **Model-View-Controller (MVC)** architectural pattern. It parses multi-format transaction files, performs bidirectional column alignment using Gemini 3.5 Flash, matches transactions using Decimal-precision math, and provides cognitive, conversational analytics powered by the **Google Agent Development Kit (ADK)** and BigQuery.

---

## 🎨 Architectural Design System

Recon-IQ is fully modular and follows strict clean-code MVC principles:

- **Model Layer (`app/models`)**: Manages high-fidelity Pydantic validation schemas and MongoDB metadata models.
- **Controller Layer (`app/controllers`)**: Coordinates low-level logic, including memory-efficient file stream parsing, Gemini cognitive schema alignment, base-10 transactional matching engines, and ADK integration.
- **View Layer (`app/views` & `app/main.py`)**: Exposes REST API endpoints and hosts the premium Anthropic Claude-inspired interactive analyst web interface.

---

## ⚡ Quickstart: One-Command Local Environment Setup

To automatically configure your local development environment with absolutely **zero manual editing**, you can use our smart auto-provisioning tool. 

This tool will automatically:
1. Detect your current active `gcloud` project.
2. Enable required APIs in your GCP Project (including the `apikeys` and `aiplatform` service endpoints).
3. Check if a secure `"Recon-IQ Gemini Key"` API Key exists, and if not, **automatically generate one**.
4. Retrieve the secret API key string and write a complete, fully configured `.env` file!

### Run the Provisioning Command:
- **On Windows (PowerShell)**:
  ```powershell
  .\setup_env.ps1
  ```
- **On macOS/Linux (Bash)**:
  ```bash
  chmod +x setup_env.sh
  ./setup_env.sh
  ```

---

## 🔌 Running the App (Two Interactive Developer Options)

You can run and interact with the Recon-IQ agent in two different ways depending on your development workflow:

### Option A: The Codelab Way (Native ADK Web CLI) 📖
To run the agent using the native Google Agent SDK (ADK) web chat server—just like the developers in the [BigQuery & Maps Codelab](https://codelabs.developers.google.com/adk-mcp-bigquery-maps)—follow these steps in your terminal:

1. **Create and Activate a Python Virtual Environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. **Install Project Dependencies & Google ADK**:
   ```powershell
   pip install -r requirements.txt
   pip install google-adk
   ```

3. **Authenticate with Google Cloud (Application Default Credentials)**:
   ```powershell
   gcloud auth application-default login
   ```

4. **Launch the Native ADK Chat Server**:
   ```powershell
   adk web
   ```
   *The console will print a local URL (usually `http://127.0.0.1:8000`). Open this in your browser to chat with your BigQuery reconciliation agent!*

---

### Option B: The Premium Claude-Styled Interactive UI (FastAPI & Docker) 🌟
Recon-IQ includes a fully customized, production-ready **Anthropic Claude-styled Chatbot UI** built directly into the FastAPI gateway. It renders gorgeous, high-fidelity responsive layout components, markdown-to-HTML table formatting, code snippets, and fully interactive, live **Vega-Lite trend charts**!

1. **Verify or Configure your Environment (`.env`)**:
   Make sure you have your environment variables set up (such as `GEMINI_API_KEY` and target `GOOGLE_CLOUD_PROJECT`).

2. **Start the Microservices Stack with Docker Compose**:
   ```bash
   docker compose up -d
   ```
   *This starts the MongoDB metadata warehouse, Mongo Express Web Portal, and the FastAPI application in a single unified network.*

3. **Explore and Interact**:
   - **Interactive Claude Chatbot UI**: [http://localhost:8000/](http://localhost:8000/)
   - **FastAPI OpenAPI Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
   - **Mongo Express Web-Admin Panel**: [http://localhost:8081/](http://localhost:8081/) *(Username: `admin` | Password: `pass`)*

---

## ☁️ Manual Cloud Run Deployment (To Any GCP Project)

To deploy the entire gateway container securely to Google Cloud Run **without hardcoding any project-specific settings**, we have created zero-dependency deployment utilities. These scripts automatically detect your active `gcloud` configuration, let you override or enter *any* target GCP project ID interactively, and build, push, and deploy the service keylessly using modern GCP IAM configurations.

### Option 1: Native Windows Deployer (PowerShell)
Double-click or run the following script in a PowerShell session:
```powershell
.\deploy.ps1
```

### Option 2: Bash/Linux/macOS Deployer (Shell)
Run the following commands in a Bash shell:
```bash
chmod +x deploy.sh
./deploy.sh
```

### What these scripts do under the hood:
1. **Interactive Target Selection**: Scans `gcloud config` for your current active project, asks if you want to use it, or lets you enter *any custom GCP Project ID* of your choice.
2. **API Activation**: Enables necessary Google APIs (`run.googleapis.com`, `artifactregistry.googleapis.com`, `bigquery.googleapis.com`, `aiplatform.googleapis.com`).
3. **Artifact Registry Setup**: Provisions a secure Docker repository inside your target project.
4. **Keyless IAM Configuration**: Creates an isolated runner identity (`recon-iq-cloud-runner` service account) and binds only the narrow roles required for operation (`roles/bigquery.admin`, `roles/aiplatform.user`).
5. **Container Orchestration**: Builds your local Docker container and pushes it to your custom registry.
6. **Live Deployment**: Deploys the service directly to Google Cloud Run, returning a live, fully-secured public URL!

---

## 🔒 Automated GitHub CI/CD Workflows

An automated CI/CD pipeline is configured in [.github/workflows/deploy.yml](file:///.github/workflows/deploy.yml). When you push code changes to the `main` branch, the workflow will build and deploy the container directly to Cloud Run.

### Setting up the GitHub Workflow:
1. In your GitHub repository, navigate to **Settings > Secrets and variables > Actions**.
2. Create a Repository Secret named **`GCP_SA_KEY`** and paste the JSON contents of your Google Cloud Service Account credential key.
3. Open [.github/workflows/deploy.yml](file:///.github/workflows/deploy.yml) and update the `PROJECT_ID` environment variable placeholder to your specific target GCP project ID.
4. Push your commits to `main` to trigger the automated deployment pipeline!
