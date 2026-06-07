import uuid
import logging
import hashlib
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel, Field

from app.config import get_mongo_db, get_bq_client, settings
from app.controllers.parser import parse_incoming_file_stream
from app.controllers.aligner import generate_metadata_profile, align_schema_with_gemini
from app.controllers.engine import reconcile_two_party_ledgers, reconcile_three_party_ledgers

logger = logging.getLogger("recon-iq.views.upload")

# Initialize both routers under their respective specs
router = APIRouter(prefix="/api/sync", tags=["synchronization"])
upload_router = APIRouter(prefix="/api/upload", tags=["ingestion"])

# --- Models ---
class BigQueryDirectLoadPayload(BaseModel):
    bank_name: str = Field(..., example="Chase Enterprise")
    agent_name: str = Field(..., example="ACH_Processor_v2")
    from_date: str = Field(..., example="2026-06-01")
    to_date: str = Field(..., example="2026-06-07")
    records: list[dict] = Field(..., description="Array of normalized transaction dictionaries")


# --- Synchronization Route (as per spec) ---
@router.post("/direct-load", status_code=status.HTTP_201_CREATED)
async def direct_load_to_warehouse(payload: BigQueryDirectLoadPayload):
    """
    Streams transaction arrays directly to partitioned BigQuery tables
    and logs run metadata to MongoDB.
    """
    table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{settings.bigquery_table}"
    
    formatted_rows = []
    for item in payload.records:
        # Convert values precisely to prevent floating point inaccuracies
        try:
            amt_dec = Decimal(str(item["amount"]))
            amt_str = str(amt_dec)
        except Exception:
            amt_str = "0.00"
            
        formatted_rows.append({
            "bank_name": payload.bank_name,
            "agent_name": payload.agent_name,
            "transaction_id": str(item["transaction_id"]),
            "amount": amt_str,  # Exact precision NUMERIC type represented as string for stream load
            "transaction_date": str(item["transaction_date"]),
            "timestamp": str(item.get("timestamp", datetime.utcnow().isoformat())),
            "status": str(item.get("status", "UNRECONCILED")),
            "matching_checksum": str(item.get("matching_checksum", ""))
        })
        
    try:
        db = get_mongo_db()
    except Exception as exc:
        logger.error(f"MongoDB connection failed: {str(exc)}")
        db = None

    bq_success = False
    bq_err_msg = ""
    try:
        bq_client = get_bq_client()
        # Ensure BigQuery table exists or create it dynamically (or handle gracefully)
        bq_errors = bq_client.insert_rows_json(table_id, formatted_rows)
        if bq_errors:
            bq_err_msg = f"BigQuery write pipeline warnings: {bq_errors}"
            logger.warning(bq_err_msg)
        else:
            bq_success = True
    except Exception as exc:
        bq_err_msg = f"BigQuery client error: {str(exc)}"
        logger.error(bq_err_msg)

    # MongoDB metadata logging
    mongo_id = None
    if db is not None:
        try:
            res = db.historical_sync_runs.insert_one({
                "bank_name": payload.bank_name,
                "agent_name": payload.agent_name,
                "date_range": {"from": payload.from_date, "to": payload.to_date},
                "records_count": len(payload.records),
                "bq_streamed": bq_success,
                "bq_errors": bq_err_msg if not bq_success else None,
                "timestamp": datetime.utcnow()
            })
            mongo_id = str(res.inserted_id)
        except Exception as exc:
            logger.error(f"Failed to log metadata to MongoDB: {str(exc)}")

    # Return success, falling back gracefully if BQ execution context is sandbox-limited
    return {
        "status": "success" if (bq_success or mongo_id) else "partial_success",
        "synchronized_records_count": len(formatted_rows),
        "destination_table": table_id,
        "bigquery_streamed": bq_success,
        "mongodb_logged": mongo_id is not None,
        "errors": bq_err_msg if not bq_success else None
    }


# --- Dynamic Ingestion & Alignment Routes ---
@upload_router.post("/align", status_code=status.HTTP_200_OK)
async def upload_and_align_schema(file: UploadFile = File(...)):
    """
    Ingests an arbitrary transaction ledger, profiles its headers/records,
    and returns its bidirectional AI schema alignment mappings.
    """
    # 1. Parse incoming upload stream
    df = parse_incoming_file_stream(file)
    
    if df.empty:
        raise HTTPException(status_code=400, detail="The uploaded file contains zero records.")
        
    # 2. Pass 1: Generate Metadata Profile
    profile = generate_metadata_profile(df)
    
    # Generate schema signature for audit trails
    schema_cols = sorted(list(df.columns))
    sig = hashlib.sha256("|".join(schema_cols).encode("utf-8")).hexdigest()
    profile["schema_signature"] = sig
    profile["filename"] = file.filename
    profile["mime_type"] = file.content_type
    
    # 3. Pass 2: Gemini Cognitive Column Alignment
    alignment = align_schema_with_gemini(profile)
    
    return {
        "filename": file.filename,
        "row_count": len(df),
        "schema_signature": sig,
        "profile": profile,
        "alignment": alignment
    }


@upload_router.post("/reconcile", status_code=status.HTTP_200_OK)
async def execute_matching_reconciliation(
    bank_name: str = Form(...),
    agent_name: str = Form(...),
    from_date: str = Form(...),
    to_date: str = Form(...),
    file1: UploadFile = File(..., description="Internal Ledger file (Source)"),
    file2: UploadFile = File(..., description="Payment Gateway file (Target)"),
    file3: Optional[UploadFile] = File(None, description="Bank Statement file (Optional 3-Way)"),
    mappings_json: str = Form(..., description="JSON-serialized alignment configurations")
):
    """
    Uploads 2 or 3 ledgers, executes precision matching calculations,
    streams results to BigQuery, and archives session execution metadata in MongoDB.
    """
    import json
    try:
        align_config = json.loads(mappings_json)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid mappings_json payload. Must be standard JSON serialization.")

    # Parse mandatory files
    df1 = parse_incoming_file_stream(file1)
    df2 = parse_incoming_file_stream(file2)
    
    if df1.empty or df2.empty:
        raise HTTPException(status_code=400, detail="One or more uploaded files contain zero records.")

    session_uuid = str(uuid.uuid4())
    db_recs = []
    
    # 2-way run
    if file3 is None:
        logger.info(f"Starting 2-way reconciliation session: {session_uuid}")
        # Resolve mappings for two-party
        # align_config expects keys 'source_id', 'source_amount', 'source_time', 'target_id', 'target_amount', 'target_time'
        matched_df, unmatched_s, unmatched_t = reconcile_two_party_ledgers(
            df1, df2, align_config
        )
        
        # Format results for BigQuery logging
        for _, row in matched_df.iterrows():
            db_recs.append({
                "transaction_id": str(row["transaction_id"]),
                "amount": str(row["source_amount"]),
                "transaction_date": str(pd.to_datetime(row["source_timestamp"]).strftime("%Y-%m-%d")),
                "timestamp": str(pd.to_datetime(row["source_timestamp"]).isoformat()),
                "status": str(row["status"]),
                "matching_checksum": str(row["matching_checksum"])
            })
            
        metrics = {
            "total_records": len(df1) + len(df2),
            "perfect_matches": len(matched_df[matched_df["status"] == "MATCHED"]),
            "mismatch_count": len(matched_df[matched_df["status"] != "MATCHED"]) + len(unmatched_s) + len(unmatched_t),
            "unresolved_amount": str(sum([clean_decimal(x) for x in matched_df[matched_df["status"] == "VALUE_MISMATCH"]["variance"]]))
        }
    else:
        logger.info(f"Starting 3-way reconciliation session: {session_uuid}")
        df3 = parse_incoming_file_stream(file3)
        if df3.empty:
            raise HTTPException(status_code=400, detail="The optional 3rd bank statement file is empty.")
            
        matched_df, audit_trail = reconcile_three_party_ledgers(
            df1, df2, df3, align_config
        )
        
        for _, row in matched_df.iterrows():
            db_recs.append({
                "transaction_id": str(row["transaction_id"]),
                "amount": str(row["internal_amount"] or row["gateway_amount"] or row["bank_amount"] or "0.00"),
                "transaction_date": str(pd.to_datetime(row["timestamp"]).strftime("%Y-%m-%d")),
                "timestamp": str(pd.to_datetime(row["timestamp"]).isoformat()),
                "status": str(row["status"]),
                "matching_checksum": str(row["matching_checksum"])
            })
            
        metrics = {
            "total_records": len(df1) + len(df2) + len(df3),
            "perfect_matches": len(matched_df[matched_df["status"] == "MATCHED"]),
            "mismatch_count": len(matched_df[matched_df["status"] != "MATCHED"]),
            "unresolved_amount": str(sum([Decimal(str(x)) for x in matched_df[matched_df["status"] != "MATCHED"]["max_variance"]]))
        }

    # Stream results asynchronously to BigQuery
    table_id = f"{settings.google_cloud_project}.{settings.bigquery_dataset}.{settings.bigquery_table}"
    bq_success = False
    try:
        bq_client = get_bq_client()
        bq_errors = bq_client.insert_rows_json(table_id, db_recs)
        if not bq_errors:
            bq_success = True
    except Exception as exc:
        logger.error(f"Asynchronous BigQuery upload error during match run: {str(exc)}")

    # Log operational session details to MongoDB
    session_logged = False
    try:
        db = get_mongo_db()
        db.conciliation_sessions.insert_one({
            "session_id": session_uuid,
            "bank_name": bank_name,
            "agent_name": agent_name,
            "date_range": {
                "from_date": from_date,
                "to_date": to_date
            },
            "ingested_files": [
                {"filename": file1.filename, "row_count": len(df1)},
                {"filename": file2.filename, "row_count": len(df2)},
                *( [{"filename": file3.filename, "row_count": len(df3)}] if file3 else [] )
            ],
            "dynamic_mappings": align_config,
            "run_metrics": metrics,
            "bq_persisted": bq_success,
            "created_at": datetime.utcnow()
        })
        session_logged = True
    except Exception as exc:
        logger.error(f"Failed to log reconciliation session to MongoDB: {str(exc)}")

    # Return reconciliation run report
    return {
        "session_id": session_uuid,
        "bank_name": bank_name,
        "agent_name": agent_name,
        "reconciliation_run_type": "3-party" if file3 else "2-party",
        "metrics": metrics,
        "bigquery_uploaded": bq_success,
        "mongodb_persisted": session_logged,
        "records_summary": matched_df.head(20).to_dict(orient="records") # return first 20 records for UI display
    }

def clean_decimal(val: Any) -> Decimal:
    if val is None or pd.isna(val) or val == "":
        return Decimal("0.0")
    try:
        return Decimal(str(val))
    except Exception:
        return Decimal("0.0")
