import logging
from datetime import datetime
from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError

from app.views.upload import router as sync_router, upload_router
from app.views.analyst import analyst_router
from app.config import settings

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("recon-iq.main")

# Initialize FastAPI App
app = FastAPI(
    title=settings.app_name,
    description="Enterprise-Grade AI-Powered Financial Reconciliation Engine",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for maximum client UI flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers under their structured domains
app.include_router(sync_router)
app.include_router(upload_router)
app.include_router(analyst_router)

# --- Global Exception Handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "error_type": "InternalServerError",
            "detail": f"An unexpected system exception occurred: {str(exc)}"
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Request schema validation failed on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "error",
            "error_type": "ValidationError",
            "detail": exc.errors()
        }
    )

# --- Home / Health Endpoints ---
@app.get("/", response_class=HTMLResponse)
async def read_root_index():
    """
    Renders a stunning premium developer landing page for Recon-IQ API gateway.
    Uses rich gradient styling and Glassmorphic aesthetics.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Recon-IQ | Enterprise AI Financial Reconciliation</title>
        <!-- Premium Google Fonts: Lora (Serif) & Inter (Sans-Serif) -->
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Lora:ital,wght@0,400;0,500;0,600;0,700;1,400&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
        <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>
        <style>
            :root {
                /* Claude Light Theme */
                --bg-primary: #F9F6F0;
                --bg-secondary: #F3EFE6;
                --bg-card: #FFFFFF;
                --text-primary: #191919;
                --text-secondary: #6E695F;
                --border-color: #E6DFD5;
                --accent-color: #D96B27;
                --accent-hover: #C25615;
                --accent-light: rgba(217, 107, 39, 0.08);
                --chat-user-bg: #ECE6DC;
                --chat-agent-bg: transparent;
                --success: #10B981;
                --warning: #F59E0B;
                --danger: #EF4444;
                --primary-glow: rgba(217, 107, 39, 0.1);
                --sidebar-width: 280px;
                --shadow-sm: 0 1px 3px rgba(0,0,0,0.05);
                --shadow-md: 0 4px 12px rgba(0,0,0,0.04);
                --shadow-lg: 0 12px 30px rgba(0,0,0,0.06);
            }

            body.dark-theme {
                /* Claude Dark Theme */
                --bg-primary: #191919;
                --bg-secondary: #222222;
                --bg-card: #1E1E1E;
                --text-primary: #E6E1DC;
                --text-secondary: #96918A;
                --border-color: #2D2D2D;
                --accent-color: #EE8262;
                --accent-hover: #D56B55;
                --accent-light: rgba(238, 130, 98, 0.08);
                --chat-user-bg: #2E2E2A;
                --chat-agent-bg: transparent;
                --primary-glow: rgba(238, 130, 98, 0.1);
                --shadow-sm: 0 1px 3px rgba(0,0,0,0.2);
                --shadow-md: 0 4px 12px rgba(0,0,0,0.25);
                --shadow-lg: 0 12px 30px rgba(0,0,0,0.3);
            }
            
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            
            body {
                background-color: var(--bg-primary);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
                min-height: 100vh;
                overflow-x: hidden;
                transition: background-color 0.3s ease, color 0.3s ease;
            }
            
            /* Custom Scrollbar */
            ::-webkit-scrollbar {
                width: 6px;
                height: 6px;
            }
            ::-webkit-scrollbar-track {
                background: transparent;
            }
            ::-webkit-scrollbar-thumb {
                background: var(--border-color);
                border-radius: 100px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: var(--text-secondary);
            }

            /* Main Page Grid Wrapper */
            .app-wrapper {
                display: flex;
                min-height: 100vh;
            }
            
            /* Left Sidebar Styling (Claude-style) */
            .sidebar {
                width: var(--sidebar-width);
                background-color: var(--bg-secondary);
                border-right: 1px solid var(--border-color);
                display: flex;
                flex-direction: column;
                padding: 28px 24px;
                position: fixed;
                height: 100vh;
                top: 0;
                left: 0;
                z-index: 100;
                transition: background-color 0.3s ease, border-color 0.3s ease;
            }
            
            .sidebar-logo {
                font-family: 'Lora', serif;
                font-size: 1.55rem;
                font-weight: 700;
                letter-spacing: -0.015em;
                margin-bottom: 36px;
                display: flex;
                align-items: center;
                gap: 12px;
                color: var(--text-primary);
            }
            
            .logo-dot {
                width: 14px;
                height: 14px;
                background-color: var(--accent-color);
                border-radius: 50%;
                display: inline-block;
                box-shadow: 0 0 10px var(--primary-glow);
                animation: softGlow 3s infinite alternate;
            }

            @keyframes softGlow {
                0% { opacity: 0.8; transform: scale(0.95); }
                100% { opacity: 1; transform: scale(1.05); }
            }
            
            .sidebar-nav {
                list-style: none;
                display: flex;
                flex-direction: column;
                gap: 8px;
                margin-bottom: auto;
            }
            
            .nav-item {
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 12px 16px;
                border-radius: 12px;
                color: var(--text-secondary);
                text-decoration: none;
                font-size: 0.95rem;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s ease;
                border: none;
                background: transparent;
                width: 100%;
                text-align: left;
                font-family: inherit;
            }
            
            .nav-item:hover {
                background-color: rgba(0, 0, 0, 0.03);
                color: var(--text-primary);
            }
            
            body.dark-theme .nav-item:hover {
                background-color: rgba(255, 255, 255, 0.03);
            }
            
            .nav-item.active {
                background-color: var(--accent-light);
                color: var(--accent-color);
                font-weight: 600;
            }
            
            .sidebar-footer {
                margin-top: auto;
                border-top: 1px solid var(--border-color);
                padding-top: 20px;
                display: flex;
                flex-direction: column;
                gap: 16px;
            }
            
            .health-badge-group {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 8px;
                font-size: 0.75rem;
                font-weight: 600;
                width: fit-content;
            }
            
            .badge-active {
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.15);
                color: var(--success);
            }
            
            .badge-info {
                background: rgba(0, 0, 0, 0.03);
                border: 1px solid var(--border-color);
                color: var(--text-secondary);
            }
            
            body.dark-theme .badge-info {
                background: rgba(255, 255, 255, 0.03);
            }
            
            .theme-toggle-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 10px;
                background: var(--bg-card);
                border: 1px solid var(--border-color);
                color: var(--text-primary);
                padding: 10px;
                border-radius: 12px;
                font-size: 0.85rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: var(--shadow-sm);
                font-family: inherit;
            }
            
            .theme-toggle-btn:hover {
                border-color: var(--accent-color);
                background-color: var(--bg-secondary);
            }
            
            /* Main Content Container */
            .main-content {
                margin-left: var(--sidebar-width);
                flex: 1;
                padding: 40px;
                max-width: calc(100vw - var(--sidebar-width));
                overflow-y: auto;
                min-height: 100vh;
            }
            
            /* Viewport boundaries on panels */
            .tab-panel {
                display: none;
                animation: panelFadeIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                max-width: 1000px;
                margin: 0 auto;
            }
            
            .tab-panel.active {
                display: block;
            }
            
            @keyframes panelFadeIn {
                from { opacity: 0; transform: translateY(12px); }
                to { opacity: 1; transform: translateY(0); }
            }
            
            /* Typography & Editorial Accents */
            .serif-title {
                font-family: 'Lora', serif;
                font-size: 2.1rem;
                font-weight: 500;
                letter-spacing: -0.01em;
                color: var(--text-primary);
                margin-bottom: 8px;
            }
            
            .section-desc {
                font-size: 0.95rem;
                color: var(--text-secondary);
                line-height: 1.5;
                margin-bottom: 28px;
            }
            
            /* Minimalist Card Design */
            .card {
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 28px;
                box-shadow: var(--shadow-sm);
                margin-bottom: 24px;
                transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.3s ease;
            }
            
            .card-title {
                font-family: 'Lora', serif;
                font-size: 1.25rem;
                font-weight: 600;
                margin-bottom: 18px;
                display: flex;
                align-items: center;
                gap: 10px;
                color: var(--text-primary);
            }
            
            /* Upload & Dropzone Layout */
            .upload-grid {
                display: grid;
                grid-template-columns: 1.1fr 0.9fr;
                gap: 28px;
                align-items: start;
            }
            
            @media (max-width: 900px) {
                .upload-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            .dropzone {
                border: 2px dashed var(--border-color);
                background-color: var(--bg-secondary);
                padding: 44px 24px;
                border-radius: 14px;
                text-align: center;
                cursor: pointer;
                transition: all 0.25s ease;
                position: relative;
            }
            
            .dropzone:hover, .dropzone.dragover {
                border-color: var(--accent-color);
                background-color: var(--accent-light);
                box-shadow: inset 0 0 15px rgba(217, 107, 39, 0.02);
            }
            
            .dropzone input[type="file"] {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                opacity: 0;
                cursor: pointer;
            }
            
            .dropzone-icon {
                font-size: 2.6rem;
                margin-bottom: 14px;
                display: inline-block;
                color: var(--text-secondary);
                transition: transform 0.2s ease;
            }
            
            .dropzone:hover .dropzone-icon {
                transform: translateY(-4px);
                color: var(--accent-color);
            }
            
            .dropzone h3 {
                font-size: 1.05rem;
                font-weight: 600;
                margin-bottom: 6px;
                color: var(--text-primary);
            }
            
            .dropzone p {
                font-size: 0.85rem;
                color: var(--text-secondary);
            }
            
            /* Form Fields styling */
            .form-row {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }
            
            label {
                font-size: 0.85rem;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.03em;
            }
            
            input[type="text"], input[type="date"], select {
                width: 100%;
                background-color: var(--bg-secondary);
                border: 1px solid var(--border-color);
                padding: 12px 16px;
                border-radius: 10px;
                color: var(--text-primary);
                font-family: inherit;
                font-size: 0.95rem;
                transition: border-color 0.2s ease, background-color 0.2s ease;
            }
            
            input[type="text"]:focus, input[type="date"]:focus, select:focus {
                outline: none;
                border-color: var(--accent-color);
                background-color: var(--bg-card);
            }
            
            /* Buttons styling */
            .btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                background-color: var(--accent-color);
                color: #FFFFFF;
                border: none;
                padding: 14px 24px;
                border-radius: 12px;
                font-family: inherit;
                font-weight: 600;
                font-size: 0.95rem;
                cursor: pointer;
                transition: all 0.2s ease;
                box-shadow: var(--shadow-sm);
                width: 100%;
            }
            
            .btn:hover {
                background-color: var(--accent-hover);
                box-shadow: 0 4px 12px rgba(217, 107, 39, 0.2);
            }
            
            .btn:active {
                transform: scale(0.98);
            }
            
            /* Metric Cards Grid */
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(4, 1fr);
                gap: 16px;
                margin-bottom: 24px;
            }
            
            @media (max-width: 800px) {
                .metrics-grid {
                    grid-template-columns: 1fr 1fr;
                }
            }
            
            .metric-card {
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 14px;
                padding: 20px;
                box-shadow: var(--shadow-sm);
            }
            
            .metric-label {
                font-size: 0.75rem;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                margin-bottom: 6px;
                font-weight: 600;
            }
            
            .metric-value {
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--text-primary);
                font-family: 'Lora', serif;
            }
            
            /* Premium Tables Design */
            .table-container {
                overflow-x: auto;
                border-radius: 12px;
                border: 1px solid var(--border-color);
                background-color: var(--bg-card);
                margin-top: 15px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-size: 0.9rem;
            }
            
            th, td {
                padding: 14px 18px;
                border-bottom: 1px solid var(--border-color);
            }
            
            th {
                background-color: var(--bg-secondary);
                font-weight: 600;
                color: var(--text-secondary);
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            
            tr:last-child td {
                border-bottom: none;
            }
            
            tr:hover td {
                background-color: rgba(0, 0, 0, 0.015);
            }
            
            body.dark-theme tr:hover td {
                background-color: rgba(255, 255, 255, 0.015);
            }
            
            /* Tags Design */
            .status-tag {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 10px;
                border-radius: 100px;
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .status-tag.matched {
                background: rgba(16, 185, 129, 0.08);
                border: 1px solid rgba(16, 185, 129, 0.15);
                color: var(--success);
            }
            
            .status-tag.discrepancy {
                background: rgba(245, 158, 11, 0.08);
                border: 1px solid rgba(245, 158, 11, 0.15);
                color: var(--warning);
            }
            
            .status-tag.unresolved {
                background: rgba(239, 68, 68, 0.08);
                border: 1px solid rgba(239, 68, 68, 0.15);
                color: var(--danger);
            }
            
            .status-tag.fuzzy {
                background: rgba(217, 107, 39, 0.08);
                border: 1px solid rgba(217, 107, 39, 0.15);
                color: var(--accent-color);
            }
            
            /* Confidence meter */
            .confidence-meter {
                height: 6px;
                background: var(--bg-secondary);
                border-radius: 10px;
                overflow: hidden;
                margin-top: 8px;
                border: 1px solid var(--border-color);
            }
            
            .confidence-fill {
                height: 100%;
                background-color: var(--success);
                transition: width 0.3s ease;
            }
            
            /* Aligner list view */
            .mapping-list {
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin-top: 15px;
            }
            
            .mapping-row {
                display: grid;
                grid-template-columns: 140px 40px 1fr 120px;
                align-items: center;
                background-color: var(--bg-secondary);
                border: 1px solid var(--border-color);
                padding: 10px 16px;
                border-radius: 10px;
                gap: 10px;
            }
            
            .mapping-primitive {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.8rem;
                font-weight: 600;
                color: var(--accent-color);
            }
            
            .mapping-arrow {
                color: var(--text-secondary);
                text-align: center;
            }
            
            .mapping-field select {
                padding: 6px 12px;
                font-size: 0.85rem;
                background-color: var(--bg-card);
            }
            
            .mapping-conf {
                text-align: right;
                font-weight: 600;
                font-size: 0.85rem;
            }
            
            /* Dynamic loader element */
            .spinner-block {
                text-align: center;
                padding: 30px;
            }
            
            .spinner {
                display: inline-block;
                width: 22px;
                height: 22px;
                border: 3px solid var(--border-color);
                border-radius: 50%;
                border-top-color: var(--accent-color);
                animation: spin 0.8s ease infinite;
            }
            
            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            /* --- Immersive Claude Chatbot Layout --- */
            .chat-workspace {
                max-width: 840px;
                margin: 0 auto;
                display: flex;
                flex-direction: column;
                height: calc(100vh - 120px);
                position: relative;
            }
            
            /* Welcome screen shown inside empty chat panel */
            .chat-welcome {
                text-align: center;
                margin-top: 60px;
                margin-bottom: 24px;
                transition: opacity 0.3s ease, transform 0.3s ease;
            }
            
            .welcome-title {
                font-family: 'Lora', serif;
                font-size: 2.2rem;
                font-weight: 500;
                color: var(--text-primary);
                margin-bottom: 32px;
                letter-spacing: -0.01em;
            }
            
            .welcome-grid {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                max-width: 720px;
                margin: 0 auto;
            }
            
            @media (max-width: 600px) {
                .welcome-grid {
                    grid-template-columns: 1fr;
                }
            }
            
            .welcome-card {
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 16px;
                padding: 18px 20px;
                cursor: pointer;
                transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
                box-shadow: var(--shadow-sm);
                text-align: left;
            }
            
            .welcome-card:hover {
                border-color: var(--accent-color);
                box-shadow: var(--shadow-md);
                transform: translateY(-2px);
            }
            
            .welcome-card h3 {
                font-size: 0.95rem;
                font-weight: 600;
                margin-bottom: 4px;
                color: var(--text-primary);
            }
            
            .welcome-card p {
                font-size: 0.8rem;
                color: var(--text-secondary);
                line-height: 1.4;
            }
            
            /* Active chat logs flow */
            .chat-history {
                flex: 1;
                overflow-y: auto;
                padding-bottom: 160px; /* space for absolute text-area */
                display: flex;
                flex-direction: column;
                gap: 24px;
                padding-right: 8px;
            }
            
            .chat-row {
                display: flex;
                width: 100%;
                margin-bottom: 4px;
            }
            
            .chat-row.user-row {
                justify-content: flex-end;
            }
            
            .chat-row.agent-row {
                justify-content: flex-start;
                border-bottom: 1px solid rgba(0, 0, 0, 0.03);
                padding-bottom: 24px;
            }
            
            body.dark-theme .chat-row.agent-row {
                border-bottom-color: rgba(255, 255, 255, 0.03);
            }
            
            .chat-bubble {
                max-width: 85%;
                font-size: 0.98rem;
                line-height: 1.6;
            }
            
            .chat-bubble.user-bubble {
                background-color: var(--chat-user-bg);
                color: var(--text-primary);
                padding: 12px 18px;
                border-radius: 20px;
                border-bottom-right-radius: 4px;
                box-shadow: var(--shadow-sm);
            }
            
            .chat-bubble.agent-bubble {
                color: var(--text-primary);
                width: 100%;
            }
            
            .agent-header {
                font-family: 'Lora', serif;
                font-weight: 700;
                font-size: 1.05rem;
                margin-bottom: 8px;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 8px;
            }
            
            .agent-avatar {
                width: 24px;
                height: 24px;
                background-color: var(--accent-color);
                color: #FFFFFF;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.75rem;
                font-weight: 800;
            }
            
            /* Floating capsule text input container like Claude */
            .chat-input-wrapper {
                position: absolute;
                bottom: 16px;
                left: 0;
                width: 100%;
                background-color: var(--bg-card);
                border: 1px solid var(--border-color);
                border-radius: 20px;
                padding: 10px 16px;
                box-shadow: var(--shadow-lg);
                display: flex;
                flex-direction: column;
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            
            .chat-input-wrapper:focus-within {
                border-color: var(--accent-color);
                box-shadow: 0 8px 30px rgba(0,0,0,0.05);
            }
            
            .chat-input-main {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .chat-textarea {
                flex: 1;
                border: none;
                background: transparent;
                resize: none;
                height: 48px;
                padding: 12px 4px;
                color: var(--text-primary);
                font-family: inherit;
                font-size: 0.98rem;
                line-height: 1.4;
            }
            
            .chat-textarea:focus {
                outline: none;
            }
            
            .chat-input-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 8px;
                border-top: 1px solid rgba(0, 0, 0, 0.04);
                padding-top: 8px;
            }
            
            body.dark-theme .chat-input-actions {
                border-top-color: rgba(255, 255, 255, 0.04);
            }
            
            .chat-btn-circle {
                width: 34px;
                height: 34px;
                border-radius: 50%;
                background-color: var(--accent-color);
                color: #FFFFFF;
                border: none;
                display: flex;
                align-items: center;
                justify-content: center;
                cursor: pointer;
                transition: background-color 0.2s ease, transform 0.1s ease;
            }
            
            .chat-btn-circle:hover {
                background-color: var(--accent-hover);
                transform: scale(1.05);
            }
            
            .chat-btn-secondary {
                background: transparent;
                border: none;
                color: var(--text-secondary);
                cursor: pointer;
                font-size: 0.85rem;
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 8px;
                transition: background-color 0.2s ease;
                font-family: inherit;
            }
            
            .chat-btn-secondary:hover {
                background-color: rgba(0, 0, 0, 0.03);
                color: var(--text-primary);
            }
            
            body.dark-theme .chat-btn-secondary:hover {
                background-color: rgba(255, 255, 255, 0.03);
            }
            
            /* Attachment details tag badge */
            .attachment-tag {
                background-color: var(--bg-secondary);
                border: 1px solid var(--border-color);
                padding: 6px 12px;
                border-radius: 10px;
                font-size: 0.8rem;
                font-weight: 500;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                align-self: flex-start;
                animation: panelFadeIn 0.2s ease;
            }
            
            .attachment-remove {
                cursor: pointer;
                color: var(--danger);
                font-weight: bold;
                margin-left: 4px;
                font-size: 0.85rem;
            }
            
            .attachment-remove:hover {
                color: #B91C1C;
            }
            
            /* Vega spec visualization chart card inside bubble */
            .chart-bubble-container {
                background-color: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                padding: 16px;
                margin-top: 10px;
                width: 100%;
                box-shadow: var(--shadow-sm);
            }
            
            /* Dynamic Toast Notification alerts */
            .toast-container {
                position: fixed;
                bottom: 24px;
                right: 24px;
                display: flex;
                flex-direction: column;
                gap: 10px;
                z-index: 1000;
            }
            
            .toast {
                background-color: var(--bg-card);
                border-left: 4px solid var(--accent-color);
                border-top: 1px solid var(--border-color);
                border-right: 1px solid var(--border-color);
                border-bottom: 1px solid var(--border-color);
                padding: 14px 20px;
                border-radius: 8px;
                font-size: 0.85rem;
                font-weight: 500;
                box-shadow: var(--shadow-md);
                display: flex;
                align-items: center;
                gap: 10px;
                animation: toastIn 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                color: var(--text-primary);
            }
            
            @keyframes toastIn {
                from { opacity: 0; transform: translateX(100px); }
                to { opacity: 1; transform: translateX(0); }
            }

            /* Premium Chat Markdown Rendering Styles */
            .chat-p {
                font-size: 0.98rem;
                line-height: 1.6;
                margin-bottom: 12px;
                color: var(--text-primary);
            }

            .chat-h1, .chat-h2, .chat-h3 {
                font-family: 'Lora', serif;
                font-weight: 600;
                color: var(--text-primary);
                margin-top: 24px;
                margin-bottom: 12px;
            }

            .chat-h1 { font-size: 1.6rem; border-bottom: 1px solid var(--border-color); padding-bottom: 6px; }
            .chat-h2 { font-size: 1.35rem; }
            .chat-h3 { font-size: 1.15rem; }

            .chat-blockquote {
                border-left: 3px solid var(--accent-color);
                background-color: var(--bg-secondary);
                padding: 12px 18px;
                margin: 16px 0;
                border-radius: 4px;
                font-style: italic;
                font-size: 0.95rem;
                color: var(--text-secondary);
            }

            .chat-list, .chat-num-list {
                margin-left: 24px;
                margin-bottom: 16px;
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .chat-list { list-style-type: disc; }
            .chat-num-list { list-style-type: decimal; }

            .chat-list li, .chat-num-list li {
                font-size: 0.95rem;
                line-height: 1.5;
                color: var(--text-primary);
            }

            .chat-inline-code {
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                background-color: rgba(217, 107, 39, 0.06);
                color: var(--accent-color);
                padding: 2px 6px;
                border-radius: 4px;
                border: 1px solid rgba(217, 107, 39, 0.12);
            }

            body.dark-theme .chat-inline-code {
                background-color: rgba(238, 130, 98, 0.08);
                border-color: rgba(238, 130, 98, 0.15);
            }

            .chat-code-block {
                background-color: var(--bg-secondary);
                border: 1px solid var(--border-color);
                border-radius: 12px;
                margin: 16px 0;
                overflow: hidden;
                box-shadow: var(--shadow-sm);
            }

            .code-block-header {
                background-color: rgba(0, 0, 0, 0.02);
                border-bottom: 1px solid var(--border-color);
                padding: 8px 16px;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-weight: 700;
                color: var(--text-secondary);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            body.dark-theme .code-block-header {
                background-color: rgba(255, 255, 255, 0.02);
            }

            .code-block-body {
                display: block;
                padding: 16px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.85rem;
                line-height: 1.5;
                overflow-x: auto;
                color: var(--text-primary);
                white-space: pre;
            }

            .chat-table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-size: 0.9rem;
                margin: 16px 0;
                border-radius: 8px;
                border: 1px solid var(--border-color);
                overflow: hidden;
            }

            .chat-table th, .chat-table td {
                padding: 10px 14px;
                border-bottom: 1px solid var(--border-color);
                text-align: left;
            }

            .chat-table th {
                background-color: var(--bg-secondary);
                color: var(--text-secondary);
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-weight: 700;
            }

            .chat-table tr:last-child td {
                border-bottom: none;
            }

            .chat-table tr:hover td {
                background-color: rgba(0, 0, 0, 0.01);
            }

            body.dark-theme .chat-table tr:hover td {
                background-color: rgba(255, 255, 255, 0.01);
            }

            .null-value {
                color: var(--text-secondary);
                font-style: italic;
                opacity: 0.7;
            }
        </style>
    </head>
    <body>
        <div class="app-wrapper">
            <!-- Left Navigation Sidebar -->
            <aside class="sidebar">
                <div class="sidebar-logo">
                    <span class="logo-dot"></span>
                    <span>recon-iq</span>
                </div>
                
                <nav style="flex: 1;">
                    <ul class="sidebar-nav">
                        <li>
                            <button class="nav-item active" id="btn-nav-chatbot" onclick="switchTab('chatbot')">
                                💬 Conversational Analyst
                            </button>
                        </li>
                        <li>
                            <button class="nav-item" id="btn-nav-upload" onclick="switchTab('upload')">
                                📁 Schema AI Ingestion
                            </button>
                        </li>
                        <li>
                            <button class="nav-item" id="btn-nav-matching" onclick="switchTab('matching')">
                                🔄 Precision Reconciler
                            </button>
                        </li>
                    </ul>
                </nav>
                
                <div class="sidebar-footer">
                    <div class="health-badge-group">
                        <div class="badge badge-active">
                            <span style="width: 6px; height: 6px; background-color: var(--success); border-radius: 50%;"></span>
                            Engine Online
                        </div>
                        <div class="badge badge-info">Gemini 3.5 Flash</div>
                    </div>
                    
                    <button class="theme-toggle-btn" id="theme-toggle-button" onclick="toggleTheme()">
                        🌙 Dark Theme
                    </button>
                </div>
            </aside>
            
            <!-- Main panel area -->
            <main class="main-content">
                
                <!-- 1. Conversational Analyst Chat Panel (Claude layout) -->
                <div id="panel-chatbot" class="tab-panel active">
                    <div class="chat-workspace">
                        
                        <!-- Empty Chat Welcome Display -->
                        <div class="chat-welcome" id="chat-welcome-overlay">
                            <h1 class="welcome-title">How can Recon-IQ help you analyze today's reconciliation?</h1>
                            <div class="welcome-grid">
                                <div class="welcome-card" onclick="sendSuggestion('Analyze last year\\'s monthly reconciliation trends and visualize them.')">
                                    <h3>📊 Monthly Trends Chart</h3>
                                    <p>Examine aggregate volumes, match success rates, and draw trend lines using interactive Vega-Lite visualizers.</p>
                                </div>
                                <div class="welcome-card" onclick="sendSuggestion('tell me today\\'s reconciliation data report')">
                                    <h3>🕵️ Forensic Audit Log</h3>
                                    <p>Inspect raw decimal-precision balances, discrepancies, and get automated system correction routes.</p>
                                </div>
                                <div class="welcome-card" onclick="sendSuggestion('How does the absolute decimal precision logic avoid double rounding drift?')">
                                    <h3>🧮 Precision Math FAQ</h3>
                                    <p>Learn how the Python Decimal class down to 0.001 tolerance prevents transactional floating-point drift.</p>
                                </div>
                                <div class="welcome-card" onclick="document.getElementById('btn-nav-upload').click()">
                                    <h3>📁 Schema Extraction</h3>
                                    <p>Directly upload a raw spreadsheet or structured XML payload to align headers with Gemini cognitive agents.</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Chat message thread stream -->
                        <div class="chat-history" id="chat-history">
                            <!-- Welcoming starter bubble -->
                            <div class="chat-row agent-row">
                                <div class="chat-bubble agent-bubble">
                                    <div class="agent-header">
                                        <div class="agent-avatar">IQ</div>
                                        <span>Recon-IQ Analyst Agent</span>
                                    </div>
                                    <p>Welcome to the Cognitive Analytics workstation. I am connected directly to your historical BigQuery ledger via the Agent Development Kit and the native BigQueryToolset. How can I assist with your audits or ledger visualizations today?</p>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Embedded Floating input capsule -->
                        <div class="chat-input-wrapper">
                            <!-- Hidden indicator for file attachment inside chatbot wrapper -->
                            <div class="attachment-tag" id="chat-attachment-tag" style="display: none;">
                                📄 <span id="chat-attachment-filename">filename.csv</span>
                                <span class="attachment-remove" onclick="removeChatAttachment()">✕</span>
                            </div>
                            
                            <div class="chat-input-main">
                                <textarea class="chat-textarea" id="chat-user-input" placeholder="Ask a financial analytics inquiry or drag files here..." onkeypress="handleChatEnter(event)"></textarea>
                            </div>
                            
                            <div class="chat-input-actions">
                                <div>
                                    <!-- Hidden files input specifically for chatbot attach file actions -->
                                    <input type="file" id="chat-file-attach-input" style="display: none;" onchange="handleChatFileAttached()">
                                    <button class="chat-btn-secondary" onclick="triggerChatFilePicker()">
                                        📎 Attach Ledger
                                    </button>
                                </div>
                                <button class="chat-btn-circle" onclick="sendChatInquiry()">
                                    ➔
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 2. Schema AI Ingestion Panel -->
                <div id="panel-upload" class="tab-panel">
                    <h2 class="serif-title">AI Schema Alignment</h2>
                    <p class="section-desc">Stream raw financial transactions in real-time. The system profiles structured samples and triggers Gemini 3.5 Flash to automatically discover and map arbitrary headers to target system primitives.</p>
                    
                    <div class="upload-grid">
                        <div class="card">
                            <div class="card-title">Extract & Profile Ledger</div>
                            <p style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 24px;">
                                Supported formats include CSV, XLSX, XLS, and hierarchical XML files. Elements are parsed safely utilizing asynchronous memory-spooled buffers.
                            </p>
                            
                            <div class="dropzone" id="align-dropzone">
                                <span class="dropzone-icon">📥</span>
                                <h3>Drag & drop your file here</h3>
                                <p>Standard spreadsheet and XML ledgers (Max 5GB)</p>
                                <input type="file" id="align-file-input" onchange="triggerSchemaAlignment()">
                            </div>
                            
                            <div id="align-loader" style="display:none;" class="spinner-block">
                                <div class="spinner"></div>
                                <p style="margin-top: 12px; font-weight: 500; font-size: 0.9rem;">Gemini is running bidirectional cognitive mapping...</p>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">Dynamic Alignment Mapping</div>
                            <div id="alignment-results-placeholder" style="color: var(--text-secondary); text-align: center; padding: 48px 0; font-size: 0.9rem;">
                                Upload a transaction file on the left to extract metadata and view Gemini alignment results.
                            </div>
                            
                            <div id="alignment-results" style="display:none;">
                                <div style="margin-bottom: 24px;">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                                        <span style="font-weight: 600; font-size: 0.9rem;">Overall Mapping Confidence</span>
                                        <span id="overall-confidence-val" style="font-weight: bold; color: var(--success);">98%</span>
                                    </div>
                                    <div class="confidence-meter">
                                        <div class="confidence-fill" id="overall-confidence-bar" style="width: 98%;"></div>
                                    </div>
                                </div>
                                
                                <h4 style="font-family: 'Lora', serif; font-size: 1.05rem; margin-bottom: 12px;">Standard Primitive Handshakes</h4>
                                <div class="mapping-list" id="mapping-list">
                                    <!-- Dynamic Mapping Rows -->
                                </div>
                                
                                <div style="margin-top: 28px;">
                                    <button class="btn" onclick="saveMappingsAndProceed()">Apply & Prepare Matcher</button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- 3. Precision Reconciler Panel -->
                <div id="panel-matching" class="tab-panel">
                    <h2 class="serif-title">Reconciliation Matching Run</h2>
                    <p class="section-desc">Cross-check accounts down to absolute 0.001 precision tolerance utilizing pure Decimal arithmetic. Maps settlement delay windows and structures forensic audit classifications.</p>
                    
                    <div class="card">
                        <div class="card-title">Execution Parameters</div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>Institution / Bank Name</label>
                                <input type="text" id="bank-name" value="Chase Enterprise">
                            </div>
                            <div class="form-group">
                                <label>Clearing Agent Name</label>
                                <input type="text" id="agent-name" value="ACH_Processor_v2">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label>From Date Range</label>
                                <input type="date" id="from-date" value="2026-06-01">
                            </div>
                            <div class="form-group">
                                <label>To Date Range</label>
                                <input type="date" id="to-date" value="2026-06-07">
                            </div>
                        </div>
                        
                        <div class="form-row" style="grid-template-columns: 1fr 2fr;">
                            <div class="form-group">
                                <label>Reconciliation Core</label>
                                <select id="recon-type" onchange="toggleReconType()">
                                    <option value="2-party">2-Way Reconciliation</option>
                                    <option value="3-party">3-Way Reconciliation</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Target Column Alignment JSON Configuration</label>
                                <input type="text" id="mapped-json-config" placeholder="Pre-compiled from alignment screen.">
                            </div>
                        </div>
                        
                        <div class="form-row" style="margin-top: 14px; margin-bottom: 24px;">
                            <div class="form-group">
                                <label>File 1: Internal Ledger (Source)</label>
                                <input type="file" id="recon-file1">
                            </div>
                            <div class="form-group">
                                <label>File 2: Payment Gateway (Target)</label>
                                <input type="file" id="recon-file2">
                            </div>
                            <div class="form-group" id="file3-group" style="display:none;">
                                <label>File 3: Bank Statement (Third-Party)</label>
                                <input type="file" id="recon-file3">
                            </div>
                        </div>
                        
                        <button class="btn" id="run-recon-btn" onclick="executeReconciliationRun()">
                            ⚡ Run Base-10 Arithmetic Match
                        </button>
                        
                        <div id="recon-loader" style="display:none;" class="spinner-block">
                            <div class="spinner"></div>
                            <p style="margin-top: 12px; font-weight: 500; font-size: 0.9rem;">Reconciling multi-source data streams...</p>
                        </div>
                    </div>
                    
                    <!-- Run Results Report -->
                    <div id="recon-results-section" style="display:none;">
                        <div class="metrics-grid">
                            <div class="metric-card">
                                <div class="metric-label">Audited Records</div>
                                <div class="metric-value" id="stat-total">0</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label" style="color: var(--success);">Perfect Matched</div>
                                <div class="metric-value" style="color: var(--success);" id="stat-matched">0</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label" style="color: var(--warning);">Mismatched Flags</div>
                                <div class="metric-value" style="color: var(--warning);" id="stat-discrepancy">0</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-label" style="color: var(--danger);">Unresolved Variance</div>
                                <div class="metric-value" style="color: var(--danger);" id="stat-variance">$0.000</div>
                            </div>
                        </div>
                        
                        <div class="card">
                            <div class="card-title">Absolute Matching Ledger Table</div>
                            <div class="table-container">
                                <table id="recon-table">
                                    <thead>
                                        <!-- Header labels generated dynamically -->
                                    </thead>
                                    <tbody id="recon-table-body">
                                        <!-- Records populated dynamically -->
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
        
        <!-- Interactive toast containers -->
        <div class="toast-container" id="toast-container"></div>
        
        <script>
            let currentMappings = {};
            let availableHeaders = [];
            let attachedFile = null;
            
            // On load, apply local storage theme preference
            window.addEventListener('DOMContentLoaded', () => {
                const savedTheme = localStorage.getItem('theme');
                if (savedTheme === 'dark') {
                    document.body.classList.add('dark-theme');
                    document.getElementById('theme-toggle-button').innerText = '☀️ Light Theme';
                }
                
                // Add drag over listener to chatbot panel to capture drag-and-dropped files
                const chatbotWorkspace = document.querySelector('.chat-workspace');
                chatbotWorkspace.addEventListener('dragover', (e) => {
                    e.preventDefault();
                });
                chatbotWorkspace.addEventListener('drop', (e) => {
                    e.preventDefault();
                    if (e.dataTransfer.files.length) {
                        setChatAttachment(e.dataTransfer.files[0]);
                    }
                });
            });
            
            function toggleTheme() {
                const btn = document.getElementById('theme-toggle-button');
                if (document.body.classList.contains('dark-theme')) {
                    document.body.classList.remove('dark-theme');
                    localStorage.setItem('theme', 'light');
                    btn.innerText = '🌙 Dark Theme';
                } else {
                    document.body.classList.add('dark-theme');
                    localStorage.setItem('theme', 'dark');
                    btn.innerText = '☀️ Light Theme';
                }
            }
            
            function switchTab(tab) {
                // Switch sidebar tab buttons active state
                document.querySelectorAll('.nav-item').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
                
                if (tab === 'chatbot') {
                    document.getElementById('btn-nav-chatbot').classList.add('active');
                    document.getElementById('panel-chatbot').classList.add('active');
                } else if (tab === 'upload') {
                    document.getElementById('btn-nav-upload').classList.add('active');
                    document.getElementById('panel-upload').classList.add('active');
                } else if (tab === 'matching') {
                    document.getElementById('btn-nav-matching').classList.add('active');
                    document.getElementById('panel-matching').classList.add('active');
                }
            }
            
            function showToast(text, type='primary') {
                const container = document.getElementById('toast-container');
                const toast = document.createElement('div');
                toast.className = 'toast';
                if (type === 'success') toast.style.borderLeftColor = 'var(--success)';
                if (type === 'danger') toast.style.borderLeftColor = 'var(--danger)';
                if (type === 'warning') toast.style.borderLeftColor = 'var(--warning)';
                toast.innerText = text;
                container.appendChild(toast);
                setTimeout(() => {
                    toast.remove();
                }, 4000);
            }
            
            // Paperclip Trigger functions for chatbot
            function triggerChatFilePicker() {
                document.getElementById('chat-file-attach-input').click();
            }
            
            function handleChatFileAttached() {
                const input = document.getElementById('chat-file-attach-input');
                if (input.files.length) {
                    setChatAttachment(input.files[0]);
                }
            }
            
            function setChatAttachment(file) {
                attachedFile = file;
                document.getElementById('chat-attachment-filename').innerText = file.name;
                document.getElementById('chat-attachment-tag').style.display = 'inline-flex';
                showToast(`Ledger attached: ${file.name}`, 'success');
            }
            
            function removeChatAttachment() {
                attachedFile = null;
                document.getElementById('chat-file-attach-input').value = '';
                document.getElementById('chat-attachment-tag').style.display = 'none';
            }
            
            async function triggerSchemaAlignment() {
                const fileInput = document.getElementById('align-file-input');
                const loader = document.getElementById('align-loader');
                const resultsPlaceholder = document.getElementById('alignment-results-placeholder');
                const resultsDiv = document.getElementById('alignment-results');
                
                if (!fileInput.files.length) return;
                
                loader.style.display = 'block';
                resultsPlaceholder.style.display = 'none';
                resultsDiv.style.display = 'none';
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);
                
                try {
                    const response = await fetch('/api/upload/align', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) throw new Error('Ingestion align API failed.');
                    
                    const data = await response.json();
                    
                    loader.style.display = 'none';
                    resultsDiv.style.display = 'block';
                    
                    // Display results
                    const overallConf = Math.round(data.alignment.overall_confidence * 100);
                    document.getElementById('overall-confidence-val').innerText = `${overallConf}%`;
                    document.getElementById('overall-confidence-bar').style.width = `${overallConf}%`;
                    
                    // Extract headers
                    availableHeaders = Object.keys(data.profile.columns);
                    
                    // Render selectors for mappings
                    const listContainer = document.getElementById('mapping-list');
                    listContainer.innerHTML = '';
                    
                    currentMappings = {};
                    const targets = ['transaction_id', 'amount', 'timestamp'];
                    
                    targets.forEach(target => {
                        const aligned = data.alignment.mappings.find(m => m.target_primitive === target);
                        const selectedHeader = aligned ? aligned.raw_field_name : availableHeaders[0];
                        currentMappings[target] = selectedHeader;
                        
                        const row = document.createElement('div');
                        row.className = 'mapping-row';
                        
                        // Select element option list
                        let selectHtml = `<select id="map-select-${target}" onchange="updateMappingConfig('${target}')">`;
                        availableHeaders.forEach(hdr => {
                            const isSelected = hdr === selectedHeader ? 'selected' : '';
                            selectHtml += `<option value="${hdr}" ${isSelected}>${hdr}</option>`;
                        });
                        selectHtml += '</select>';
                        
                        const confidenceValue = aligned ? Math.round(aligned.confidence * 100) : 50;
                        const confidenceColor = confidenceValue > 80 ? 'var(--success)' : confidenceValue > 50 ? 'var(--warning)' : 'var(--danger)';
                        
                        row.innerHTML = `
                            <div class="mapping-primitive">${target}</div>
                            <div class="mapping-arrow">➡️</div>
                            <div class="mapping-field">${selectHtml}</div>
                            <div class="mapping-conf" style="color: ${confidenceColor}">${confidenceValue}% Conf</div>
                        `;
                        
                        listContainer.appendChild(row);
                    });
                    
                    showToast('Dynamic AI Alignment completed successfully!', 'success');
                    
                } catch (err) {
                    loader.style.display = 'none';
                    resultsPlaceholder.style.display = 'block';
                    showToast(`Error aligning schema: ${err.message}`, 'danger');
                }
            }
            
            function updateMappingConfig(primitive) {
                const select = document.getElementById(`map-select-${primitive}`);
                currentMappings[primitive] = select.value;
            }
            
            function saveMappingsAndProceed() {
                const compiledConfig = {
                    "source_id": currentMappings.transaction_id,
                    "source_amount": currentMappings.amount,
                    "source_time": currentMappings.timestamp,
                    "target_id": currentMappings.transaction_id,
                    "target_amount": currentMappings.amount,
                    "target_time": currentMappings.timestamp
                };
                
                const compiled3Way = {
                    "file1": { "transaction_id": currentMappings.transaction_id, "amount": currentMappings.amount, "timestamp": currentMappings.timestamp },
                    "file2": { "transaction_id": currentMappings.transaction_id, "amount": currentMappings.amount, "timestamp": currentMappings.timestamp },
                    "file3": { "transaction_id": currentMappings.transaction_id, "amount": currentMappings.amount, "timestamp": currentMappings.timestamp }
                };
                
                const type = document.getElementById('recon-type').value;
                document.getElementById('mapped-json-config').value = JSON.stringify(type === '3-party' ? compiled3Way : compiledConfig);
                
                showToast('Mapped primitive configurations saved!', 'success');
                switchTab('matching');
            }
            
            function toggleReconType() {
                const type = document.getElementById('recon-type').value;
                const file3Grp = document.getElementById('file3-group');
                
                if (type === '3-party') {
                    file3Grp.style.display = 'block';
                } else {
                    file3Grp.style.display = 'none';
                }
                
                if (Object.keys(currentMappings).length > 0) {
                    saveMappingsAndProceed();
                }
            }
            
            async function executeReconciliationRun() {
                const bank = document.getElementById('bank-name').value;
                const agent = document.getElementById('agent-name').value;
                const fromDate = document.getElementById('from-date').value;
                const toDate = document.getElementById('to-date').value;
                const type = document.getElementById('recon-type').value;
                const jsonConfig = document.getElementById('mapped-json-config').value;
                
                const file1 = document.getElementById('recon-file1').files[0];
                const file2 = document.getElementById('recon-file2').files[0];
                const file3 = document.getElementById('recon-file3').files[0];
                
                if (!file1 || !file2) {
                    showToast('Please upload File 1 and File 2.', 'warning');
                    return;
                }
                
                if (type === '3-party' && !file3) {
                    showToast('Please upload File 3 for 3-way reconciliation.', 'warning');
                    return;
                }
                
                if (!jsonConfig.trim()) {
                    showToast('Please ensure column mappings are compiled from AI Alignment first.', 'warning');
                    return;
                }
                
                const loader = document.getElementById('recon-loader');
                const resultsSec = document.getElementById('recon-results-section');
                
                loader.style.display = 'block';
                resultsSec.style.display = 'none';
                
                const formData = new FormData();
                formData.append('bank_name', bank);
                formData.append('agent_name', agent);
                formData.append('from_date', fromDate);
                formData.append('to_date', toDate);
                formData.append('mappings_json', jsonConfig);
                formData.append('file1', file1);
                formData.append('file2', file2);
                if (type === '3-party' && file3) {
                    formData.append('file3', file3);
                }
                
                try {
                    const response = await fetch('/api/upload/reconcile', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!response.ok) throw new Error('Reconciliation execution endpoint failed.');
                    
                    const data = await response.json();
                    
                    loader.style.display = 'none';
                    resultsSec.style.display = 'block';
                    
                    // Render stats
                    document.getElementById('stat-total').innerText = data.metrics.total_records.toLocaleString();
                    document.getElementById('stat-matched').innerText = data.metrics.perfect_matches.toLocaleString();
                    document.getElementById('stat-discrepancy').innerText = data.metrics.mismatch_count.toLocaleString();
                    document.getElementById('stat-variance').innerText = `$${parseFloat(data.metrics.unresolved_amount).toFixed(3)}`;
                    
                    // Render Table
                    const tableHead = document.querySelector('#recon-table thead');
                    const tableBody = document.getElementById('recon-table-body');
                    
                    tableHead.innerHTML = '';
                    tableBody.innerHTML = '';
                    
                    if (type === '2-party') {
                        tableHead.innerHTML = `
                            <tr>
                                <th>Transaction ID</th>
                                <th>Source Amt ($)</th>
                                <th>Target Amt ($)</th>
                                <th>Variance</th>
                                <th>Status</th>
                                <th>Source Date</th>
                            </tr>
                        `;
                        
                        data.records_summary.forEach(rec => {
                            const tr = document.createElement('tr');
                            const varianceClass = rec.status === 'MATCHED' ? 'matched' : rec.status === 'FUZZY_MATCHED' ? 'fuzzy' : 'unresolved';
                            
                            tr.innerHTML = `
                                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">${rec.transaction_id}</td>
                                <td>${parseFloat(rec.source_amount).toFixed(2)}</td>
                                <td>${parseFloat(rec.target_amount).toFixed(2)}</td>
                                <td style="font-weight: 600; color: ${rec.variance > 0 ? 'var(--danger)' : 'var(--text-secondary)'}">${parseFloat(rec.variance).toFixed(3)}</td>
                                <td><span class="status-tag ${varianceClass}">${rec.status}</span></td>
                                <td style="font-size: 0.8rem; color: var(--text-secondary);">${new Date(rec.source_timestamp).toLocaleDateString()}</td>
                            `;
                            tableBody.appendChild(tr);
                        });
                    } else {
                        tableHead.innerHTML = `
                            <tr>
                                <th>Transaction ID</th>
                                <th>Internal ($)</th>
                                <th>Gateway ($)</th>
                                <th>Bank Statement ($)</th>
                                <th>Max Variance</th>
                                <th>Status</th>
                                <th>Correction Vector Path</th>
                            </tr>
                        `;
                        
                        data.records_summary.forEach(rec => {
                            const tr = document.createElement('tr');
                            const varianceClass = rec.status === 'MATCHED' ? 'matched' : 'unresolved';
                            
                            const v1 = rec.internal_amount ? parseFloat(rec.internal_amount).toFixed(2) : '-';
                            const v2 = rec.gateway_amount ? parseFloat(rec.gateway_amount).toFixed(2) : '-';
                            const v3 = rec.bank_amount ? parseFloat(rec.bank_amount).toFixed(2) : '-';
                            
                            tr.innerHTML = `
                                <td style="font-family: 'JetBrains Mono', monospace; font-size: 0.85rem;">${rec.transaction_id}</td>
                                <td>${v1}</td>
                                <td>${v2}</td>
                                <td>${v3}</td>
                                <td style="font-weight: 600; color: ${rec.max_variance > 0 ? 'var(--danger)' : 'var(--text-secondary)'}">${parseFloat(rec.max_variance).toFixed(3)}</td>
                                <td><span class="status-tag ${varianceClass}">${rec.status}</span></td>
                                <td style="font-size: 0.8rem; color: var(--text-secondary);">${rec.correction_path}</td>
                            `;
                            tableBody.appendChild(tr);
                        });
                    }
                    
                    showToast('Absolute Precision Reconciliation run executed successfully!', 'success');
                    
                } catch (err) {
                    loader.style.display = 'none';
                    showToast(`Run matching failed: ${err.message}`, 'danger');
                }
            }
            
            async function sendSuggestion(text) {
                document.getElementById('chat-user-input').value = text;
                sendChatInquiry();
            }
            
            function handleChatEnter(event) {
                if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault();
                    sendChatInquiry();
                }
            }
            
            async function sendChatInquiry() {
                const input = document.getElementById('chat-user-input');
                const query = input.value.trim();
                
                // If there's an attached file and no query, or we have a file, guide user elegantly
                if (attachedFile && !query) {
                    // Smart file alignment handshake!
                    showToast('Initiating Ledger Schema extraction pipeline...', 'success');
                    
                    // Pre-fill file input on Tab 2 and switch tabs
                    const fileInput = document.getElementById('align-file-input');
                    
                    // Handover file list
                    const dataTransfer = new DataTransfer();
                    dataTransfer.items.add(attachedFile);
                    fileInput.files = dataTransfer.files;
                    
                    removeChatAttachment();
                    switchTab('upload');
                    triggerSchemaAlignment();
                    return;
                }
                
                if (!query) return;
                
                // Hide welcome screen on first text query submission
                const welcomeOverlay = document.getElementById('chat-welcome-overlay');
                if (welcomeOverlay) {
                    welcomeOverlay.style.display = 'none';
                }
                
                const history = document.getElementById('chat-history');
                
                // Append User Chat Row
                const userRow = document.createElement('div');
                userRow.className = 'chat-row user-row';
                userRow.innerHTML = `<div class="chat-bubble user-bubble">${query}</div>`;
                history.appendChild(userRow);
                
                input.value = '';
                history.scrollTop = history.scrollHeight;
                
                // Append Agent Processing Indicator
                const loaderRow = document.createElement('div');
                loaderRow.className = 'chat-row agent-row';
                loaderRow.id = 'chat-temp-loader';
                loaderRow.innerHTML = `
                    <div class="chat-bubble agent-bubble">
                        <div class="agent-header">
                            <div class="agent-avatar">IQ</div>
                            <span>Recon-IQ Agent</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="spinner" style="width:14px; height:14px; border-width:2px;"></div>
                            <span style="font-size: 0.85rem; color: var(--text-secondary);">Querying date-partitioned BigQuery database...</span>
                        </div>
                    </div>
                `;
                history.appendChild(loaderRow);
                history.scrollTop = history.scrollHeight;
                
                try {
                    const response = await fetch(`/api/analyst/ask?q=${encodeURIComponent(query)}`);
                    if (!response.ok) throw new Error('Cognitive analyst API returned an error.');
                    
                    const data = await response.json();
                    loaderRow.remove();
                    
                    // Append Agent Response Row
                    const agentRow = document.createElement('div');
                    agentRow.className = 'chat-row agent-row';
                    
                    let replyHtml = `
                        <div class="chat-bubble agent-bubble">
                            <div class="agent-header">
                                <div class="agent-avatar">IQ</div>
                                <span>Recon-IQ Cognitive Agent</span>
                            </div>
                    `;
                    
                    if (data.narrative_synthesis) {
                        replyHtml += `<div class="narrative-content" style="margin-bottom: 12px;">${parseMarkdownToHTML(data.narrative_synthesis)}</div>`;
                    }
                    
                    if (data.summary_markdown) {
                        replyHtml += `<div class="markdown-report" style="margin-top: 10px;">${parseMarkdownToHTML(data.summary_markdown)}</div>`;
                    }
                    
                    replyHtml += `</div>`;
                    agentRow.innerHTML = replyHtml;
                    history.appendChild(agentRow);
                    
                    // If visual speculative vega specs are returned, append the render node
                    if (data.vega_lite_spec) {
                        const chartId = `chart-${Date.now()}`;
                        const chartContainer = document.createElement('div');
                        chartContainer.className = 'chart-bubble-container';
                        chartContainer.innerHTML = `
                            <p style="font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Generated Vega-Lite Trend Visualization</p>
                            <div id="${chartId}" style="width: 100%;"></div>
                        `;
                        history.appendChild(chartContainer);
                        
                        // Embed Vega-Lite with dark/light background adaptive themes
                        const isDark = document.body.classList.contains('dark-theme');
                        vegaEmbed(`#${chartId}`, data.vega_lite_spec, {
                            actions: false, 
                            theme: isDark ? 'dark' : 'excel'
                        });
                    }
                    
                    history.scrollTop = history.scrollHeight;
                    showToast('Response synthesized successfully!', 'success');
                    
                } catch (err) {
                    loaderRow.remove();
                    const errRow = document.createElement('div');
                    errRow.className = 'chat-row agent-row';
                    errRow.innerHTML = `
                        <div class="chat-bubble agent-bubble" style="border-color: var(--danger);">
                            <div class="agent-header">
                                <div class="agent-avatar" style="background-color: var(--danger);">✕</div>
                                <span style="color: var(--danger);">Query Failed</span>
                            </div>
                            <p>An error occurred while compiling results: ${err.message}</p>
                        </div>
                    `;
                    history.appendChild(errRow);
                    history.scrollTop = history.scrollHeight;
                    showToast('Query execution error.', 'danger');
                }
            }

            /* Premium Anthropic Claude UI Markdown Engine */
            function parseMarkdownToHTML(markdown) {
                if (!markdown) return "";
                
                const lines = markdown.split('\n');
                let html = '';
                let inList = false;
                let listType = ''; // 'ul' or 'ol'
                let inTable = false;
                let tableHeaders = [];
                let tableRows = [];
                let inCodeBlock = false;
                let codeBlockContent = '';
                let codeBlockLang = '';

                for (let i = 0; i < lines.length; i++) {
                    let line = lines[i];

                    // Code Blocks
                    if (line.trim().startsWith('```')) {
                        if (inCodeBlock) {
                            html += `<pre class="chat-code-block"><div class="code-block-header"><span>${escapeHTML(codeBlockLang || 'code')}</span><span style="cursor: pointer; opacity: 0.8;" onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.innerText); showToast('Copied to clipboard!', 'success');">📋 Copy</span></div><code class="code-block-body">${escapeHTML(codeBlockContent.trim())}</code></pre>`;
                            inCodeBlock = false;
                            codeBlockContent = '';
                            codeBlockLang = '';
                        } else {
                            inCodeBlock = true;
                            codeBlockLang = line.trim().substring(3).trim();
                        }
                        continue;
                    }

                    if (inCodeBlock) {
                        codeBlockContent += line + '\n';
                        continue;
                    }

                    // Close list if needed
                    const isUnorderedList = line.trim().startsWith('* ') || line.trim().startsWith('- ') || line.trim().startsWith('+ ');
                    const isOrderedList = !!line.trim().match(/^\d+\.\s+/);
                    
                    if (inList && !isUnorderedList && !isOrderedList) {
                        html += listType === 'ul' ? '</ul>' : '</ol>';
                        inList = false;
                        listType = '';
                    }

                    // Close table if needed
                    if (inTable && !line.trim().startsWith('|')) {
                        html += renderTableHTML(tableHeaders, tableRows);
                        inTable = false;
                        tableHeaders = [];
                        tableRows = [];
                    }

                    // Tables
                    if (line.trim().startsWith('|')) {
                        const parts = line.split('|').map(p => p.trim()).filter((p, index, arr) => index > 0 && index < arr.length - 1);
                        const isSeparator = parts.every(p => p.startsWith(':') || p.endsWith(':') || p.replace(/-/g, '') === '');
                        
                        if (isSeparator) {
                            continue;
                        }

                        if (!inTable) {
                            inTable = true;
                            tableHeaders = parts;
                        } else {
                            tableRows.push(parts);
                        }
                        continue;
                    }

                    // Headings
                    if (line.startsWith('# ')) {
                        html += `<h1 class="chat-h1">${inlineFormatting(line.substring(2))}</h1>`;
                        continue;
                    }
                    if (line.startsWith('## ')) {
                        html += `<h2 class="chat-h2">${inlineFormatting(line.substring(3))}</h2>`;
                        continue;
                    }
                    if (line.startsWith('### ')) {
                        html += `<h3 class="chat-h3">${inlineFormatting(line.substring(4))}</h3>`;
                        continue;
                    }

                    // Blockquotes
                    if (line.startsWith('> ')) {
                        html += `<blockquote class="chat-blockquote">${inlineFormatting(line.substring(2))}</blockquote>`;
                        continue;
                    }

                    // Lists
                    if (isUnorderedList) {
                        if (!inList) {
                            html += '<ul class="chat-list">';
                            inList = true;
                            listType = 'ul';
                        }
                        const itemText = line.trim().substring(2).trim();
                        html += `<li>${inlineFormatting(itemText)}</li>`;
                        continue;
                    }

                    if (isOrderedList) {
                        if (!inList) {
                            html += '<ol class="chat-num-list">';
                            inList = true;
                            listType = 'ol';
                        }
                        const indexPeriod = line.trim().indexOf('.');
                        const itemText = line.trim().substring(indexPeriod + 1).trim();
                        html += `<li>${inlineFormatting(itemText)}</li>`;
                        continue;
                    }

                    // Empty line
                    if (line.trim() === '') {
                        continue;
                    }

                    // Normal paragraph
                    html += `<p class="chat-p">${inlineFormatting(line)}</p>`;
                }

                // Final cleanups
                if (inList) {
                    html += listType === 'ul' ? '</ul>' : '</ol>';
                }
                if (inTable) {
                    html += renderTableHTML(tableHeaders, tableRows);
                }

                return html;
            }

            function escapeHTML(str) {
                return str
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#039;');
            }

            function inlineFormatting(text) {
                return text
                    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                    .replace(/__(.*?)__/g, '<strong>$1</strong>')
                    .replace(/\*(.*?)\*/g, '<em>$1</em>')
                    .replace(/_(.*?)_/g, '<em>$1</em>')
                    .replace(/`(.*?)`/g, '<code class="chat-inline-code">$1</code>')
                    .replace(/\\\$/g, '$');
            }

            function renderTableHTML(headers, rows) {
                let html = '<div class="table-container" style="margin: 16px 0;"><table class="chat-table"><thead><tr>';
                headers.forEach(h => {
                    html += `<th>${inlineFormatting(h)}</th>`;
                });
                html += '</tr></thead><tbody>';
                rows.forEach(row => {
                    html += '<tr>';
                    for (let i = 0; i < headers.length; i++) {
                        const cell = row[i] || '';
                        const displayCell = cell === 'Null' ? '<span class="null-value">Null</span>' : inlineFormatting(cell);
                        html += `<td>${displayCell}</td>`;
                    }
                    html += '</tr>';
                });
                html += '</tbody></table></div>';
                return html;
            }
        </script>
    </body>
    </html>
    """



@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """System health assessment API."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "precision_engine": "Decimal_1e-3",
        "timestamp": datetime.utcnow().isoformat()
    }
