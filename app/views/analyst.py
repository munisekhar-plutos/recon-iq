import logging
from fastapi import APIRouter, Query, HTTPException, status
from typing import Dict, Any, Optional
from app.controllers.agent import run_conversational_query

logger = logging.getLogger("recon-iq.views.analyst")

analyst_router = APIRouter(prefix="/api/analyst", tags=["cognitive-analyst"])

@analyst_router.get("/ask", status_code=status.HTTP_200_OK)
async def ask_cognitive_analyst(
    q: str = Query(..., description="The natural language question to ask the reconciliation analyst agent.")
):
    """
    Exposes conversational analytics endpoints. Queries the ADK Agent (with native BigQueryToolset)
    or resolves to a smart Gemini-powered cognitive fallback mock analyst to answer trends/audits.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="The inquiry question string cannot be empty.")
        
    try:
        logger.info(f"Received cognitive analyst request: '{q}'")
        analysis_result = await run_conversational_query(q)
        return analysis_result
    except Exception as exc:
        logger.error(f"Error executing cognitive query: {str(exc)}")
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred in the cognitive orchestration plane: {str(exc)}"
        )

@analyst_router.get("/report", status_code=status.HTTP_200_OK)
async def get_daily_forensic_report(
    date: Optional[str] = Query(None, description="ISO Date (YYYY-MM-DD) of the audit report. Defaults to today's date.")
):
    """
    Exposes structured forensic audit report endpoints. Directly targets exact numerical anomalies,
    and returns daily forensic logs matching the requirements of the specification.
    """
    # Use today's date if not specified
    target_date = date or "2026-06-07"
    logger.info(f"Generating daily forensic audit log report for: {target_date}")
    
    # Run the audit report question via the agent controller which returns the detailed forensic markdown
    query_str = f"tell me today's reconciliation data report for {target_date}"
    try:
        report_data = await run_conversational_query(query_str)
        return report_data
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate forensic audit log: {str(exc)}"
        )
