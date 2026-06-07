import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pymongo import MongoClient
from google.cloud import bigquery
from google import genai

class Settings(BaseSettings):
    # App Settings
    app_name: str = "recon-iq"
    
    # MongoDB settings
    mongo_uri: str = "mongodb://recon-iq-metadata:27017/"
    mongo_db_name: str = "recon_iq_metadata"
    
    # GCP settings
    google_cloud_project: str = "recon-iq-production"
    google_cloud_location: str = "us-central1"
    
    # BigQuery settings
    bigquery_dataset: str = "analytics_warehouse"
    bigquery_table: str = "historical_ledger"
    
    # Gemini settings
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate settings
settings = Settings()

# Lazy database client initializers to prevent instantiation during testing or if credentials are missing
_mongo_client = None
_bq_client = None
_genai_client = None

def get_mongo_db():
    global _mongo_client
    if _mongo_client is None:
        _mongo_client = MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=2000)
    return _mongo_client[settings.mongo_db_name]

def get_bq_client():
    global _bq_client
    if _bq_client is None:
        # Check if project ID is explicitly specified in the environment or settings
        _bq_client = bigquery.Client(project=settings.google_cloud_project)
    return _bq_client

def get_genai_client():
    global _genai_client
    if _genai_client is None:
        # google-genai Client automatically reads GEMINI_API_KEY from env, but we can also set it explicitly
        if settings.gemini_api_key:
            _genai_client = genai.Client(api_key=settings.gemini_api_key)
        else:
            _genai_client = genai.Client()
    return _genai_client
