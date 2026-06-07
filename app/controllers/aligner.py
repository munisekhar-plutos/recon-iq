import pandas as pd
import json
import logging
from typing import Dict, Any, List
from google.genai import types
from app.config import get_genai_client, settings
from app.models.transaction import SchemaAlignmentPayload, ColumnMapping

logger = logging.getLogger("recon-iq.aligner")

def generate_metadata_profile(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Pass 1: Subsample Profiling
    Analyzes up to a 50-row subsample of the DataFrame to construct a lightweight 
    structural schema profile including native types, density, and distinct samples.
    """
    sub_df = df.head(50)
    total_rows = len(sub_df)
    
    columns_profile = {}
    for col in df.columns:
        non_null_series = sub_df[col].dropna()
        non_null_count = len(non_null_series)
        unique_vals = non_null_series.unique().tolist()
        
        # Take up to 5 unique samples as string representations
        samples = [str(x) for x in unique_vals[:5]]
        
        # Simple dtype deduction
        inferred_type = str(df[col].dtype)
        
        columns_profile[col] = {
            "inferred_type": inferred_type,
            "non_null_count": non_null_count,
            "total_rows": total_rows,
            "density": float(non_null_count / total_rows) if total_rows > 0 else 0.0,
            "unique_count": len(unique_vals),
            "samples": samples
        }
        
    return {
        "columns": columns_profile,
        "row_count_profile": total_rows
    }

def get_deterministic_fallback_alignment(metadata_profile: Dict[str, Any]) -> SchemaAlignmentPayload:
    """
    Deterministic rule-based mapping fallback based on common column patterns.
    Ensures system works perfectly even without Gemini connectivity.
    """
    logger.warning("Using deterministic fallback alignment.")
    columns = list(metadata_profile["columns"].keys())
    mappings = []
    
    # ID regexes
    id_rx = re_compile = r"(id|ref|uuid|tx|key|num|code|reference|ident)"
    # Amount regexes
    amt_rx = r"(amt|amount|val|value|sum|price|charge|offset|fee|bal|balance)"
    # Timestamp regexes
    ts_rx = r"(time|date|ts|posted|utc|created|stamp|day)"
    
    mapped_primitives = {}
    
    # Simple score-based selection
    for prim, rx in [("transaction_id", id_rx), ("amount", amt_rx), ("timestamp", ts_rx)]:
        best_col = None
        best_score = -1
        
        for col in columns:
            if col in mapped_primitives.values():
                continue
            col_lower = col.lower()
            import re
            match = re.search(rx, col_lower)
            if match:
                # Score based on match position and length (prefer exact/shorter matches)
                score = 100 - len(col_lower) + (50 if col_lower == prim else 0)
                if score > best_score:
                    best_score = score
                    best_col = col
                    
        if best_col and best_col not in mapped_primitives.values():
            mapped_primitives[prim] = best_col
            mappings.append(ColumnMapping(
                target_primitive=prim,
                raw_field_name=best_col,
                inferred_format="Alphanumeric String" if prim == "transaction_id" else "String Numeric" if prim == "amount" else "Datetime/ISO-8601",
                confidence=0.85,
                rationale=f"Deterministic mapping fallback selected '{best_col}' based on regex heuristic."
            ))
            
    # Map remaining columns to metadata
    for col in columns:
        if col not in [m.raw_field_name for m in mappings]:
            mappings.append(ColumnMapping(
                target_primitive="metadata",
                raw_field_name=col,
                inferred_format="Text String",
                confidence=0.50,
                rationale="Unmatched field mapped as general transaction metadata."
            ))
            
    # Ensure we at least have dummy mappings for core primitives if not matched
    for prim in ["transaction_id", "amount", "timestamp"]:
        if not any(m.target_primitive == prim for m in mappings):
            # Fallback to first available columns
            available = [c for col in columns if col not in [m.raw_field_name for m in mappings]]
            fallback_col = available[0] if available else (columns[0] if columns else "dummy_column")
            mappings.append(ColumnMapping(
                target_primitive=prim,
                raw_field_name=fallback_col,
                inferred_format="String Value",
                confidence=0.20,
                rationale=f"No matching pattern found. Mapped to available column '{fallback_col}' as emergency fallback."
            ))
            
    return SchemaAlignmentPayload(
        mappings=mappings,
        overall_confidence=0.75 if len(mapped_primitives) == 3 else 0.50
    )

def align_schema_with_gemini(metadata_profile: Dict[str, Any]) -> SchemaAlignmentPayload:
    """
    Pass 2: Cognitive Mapping (Gemini-Powered Alignment)
    Invokes Gemini 2.5 using a structured response schema to evaluate column semantic 
    meaning bidirectionally, generating high-confidence mappings to core primitives.
    """
    try:
        genai_client = get_genai_client()
    except Exception as exc:
        logger.error(f"Failed to instantiate GenAI client: {str(exc)}")
        return get_deterministic_fallback_alignment(metadata_profile)
        
    profile_json = json.dumps(metadata_profile, indent=2)
    
    prompt = f"""
You are an expert financial ledger schema alignment agent. 
Your goal is to perform a rigorous two-way (bidirectional) cognitive mapping between the raw transaction file schema and the target primitives.

### Target System Primitives:
1. `transaction_id`: The primary unique alphanumeric key or reference code identifying each transaction.
2. `amount`: The numerical currency/monetary value (including positive/negative charges, offsets, etc.).
3. `timestamp`: The date, time, or datetime indicating when the transaction was completed or posted.
4. `metadata`: Any other supplementary description, agent names, or category fields.

### Structural Metadata Profile of Ingested File:
{profile_json}

### Strict Instructions:
1. Analyze the sample data, unique counts, density, and names of all raw columns.
2. Evaluate mappings bidirectionally:
   - Does Column A fit the target primitive semantically?
   - Does the target primitive require the format/attributes exhibited in Column A?
3. Ensure EXACTLY one raw column is mapped to each core primitive: `transaction_id`, `amount`, and `timestamp`.
4. Return a confidence score (between 0.0 and 1.0) and a brief technical rationale for each mapping.
5. All other unmapped columns should be categorized as target primitive `metadata`.
"""
    try:
        response = genai_client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=SchemaAlignmentPayload,
                temperature=0.1
            ),
        )
        
        # Check if response parsed successfully
        if response.parsed:
            return response.parsed
        else:
            logger.error("Gemini output could not be parsed into the SchemaAlignmentPayload schema.")
            return get_deterministic_fallback_alignment(metadata_profile)
            
    except Exception as exc:
        logger.error(f"Gemini API invocation error: {str(exc)}")
        return get_deterministic_fallback_alignment(metadata_profile)
