from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class DateRange(BaseModel):
    from_date: str = Field(..., description="ISO start date (YYYY-MM-DD)")
    to_date: str = Field(..., description="ISO end date (YYYY-MM-DD)")

class IngestedFile(BaseModel):
    filename: str = Field(..., description="Name of the uploaded file")
    mime_type: str = Field(..., description="MIME-type of the file")
    row_count: int = Field(..., description="Number of parsed records")
    schema_signature: str = Field(..., description="SHA-256 hash or signature of the schema columns")

class DynamicMappings(BaseModel):
    transaction_id: str = Field(..., description="Target mapped field name for unique transaction ID")
    amount: str = Field(..., description="Target mapped field name for numeric amount")
    timestamp: str = Field(..., description="Target mapped field name for transaction datetime")

class RunMetrics(BaseModel):
    total_records: int = Field(0, description="Total number of combined records processed")
    perfect_matches: int = Field(0, description="Number of fully reconciled records")
    mismatch_count: int = Field(0, description="Number of mismatched or flagged records")
    unresolved_amount: str = Field("0.00", description="Total net value variance represented as precise decimal string")

class ReconciliationSession(BaseModel):
    id: Optional[str] = Field(None, alias="_id", description="MongoDB BSON Object ID represented as string")
    session_id: str = Field(..., description="UUID representing the unique run or session")
    bank_name: str = Field(..., description="Name of the reconciled bank or institution")
    agent_name: str = Field(..., description="Name of the clearing agent or ACH processor")
    date_range: DateRange
    ingested_files: List[IngestedFile] = Field(default_factory=list)
    dynamic_mappings: DynamicMappings
    run_metrics: Optional[RunMetrics] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "session_id": "a9e5b32f-48cf-432d-905e-df659ba912a3",
                "bank_name": "Chase Enterprise",
                "agent_name": "ACH_Processor_v2",
                "date_range": {
                    "from_date": "2026-06-01",
                    "to_date": "2026-06-07"
                },
                "ingested_files": [
                    {
                        "filename": "internal_ledger_june.csv",
                        "mime_type": "text/csv",
                        "row_count": 145020,
                        "schema_signature": "d2f4a138..."
                    }
                ],
                "dynamic_mappings": {
                    "transaction_id": "Bank_Tx_Ref",
                    "amount": "posted_amt",
                    "timestamp": "Timestamp_UTC"
                },
                "run_metrics": {
                    "total_records": 145020,
                    "perfect_matches": 144985,
                    "mismatch_count": 35,
                    "unresolved_amount": "45.021"
                }
            }
        }
    }
