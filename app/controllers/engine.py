import pandas as pd
from decimal import Decimal, getcontext, ROUND_HALF_UP
from datetime import datetime
from typing import Dict, Any, Tuple, List, Optional
import hashlib

# Configure decimal environment to support high precision (up to 28 digits)
getcontext().prec = 28
getcontext().rounding = ROUND_HALF_UP

def clean_decimal(val: Any) -> Decimal:
    """Safely converts input values into a precise Decimal, avoiding float representation errors."""
    if val is None or pd.isna(val) or val == "":
        return Decimal("0.0")
    try:
        # Strip currency symbols and formatting commas
        clean_str = str(val).replace("$", "").replace(",", "").strip()
        return Decimal(clean_str)
    except Exception:
        return Decimal("0.0")

def clean_datetime(val: Any) -> datetime:
    """Safely converts input values into a standard datetime object."""
    if val is None or pd.isna(val) or val == "":
        return datetime.utcnow()
    try:
        return pd.to_datetime(val, utc=True).to_pydatetime()
    except Exception:
        return datetime.utcnow()

def compute_checksum(*args: Any) -> str:
    """Generates a SHA-256 matching checksum for audit-level ledger tracking."""
    normalized = "|".join([str(arg).strip().lower() for arg in args])
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def reconcile_two_party_ledgers(
    source_df: pd.DataFrame,
    target_df: pd.DataFrame,
    mapping: Dict[str, str],
    tolerance_threshold: Decimal = Decimal("0.001")
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Executes a high-precision 2-way reconciliation with a fallback fuzzy-matching window.
    Compares source and target records by unique ID or fallbacks to amount/timestamp window.
    """
    matched_records = []
    
    # Get column names mapped to primitives
    s_id_col = mapping.get("source_id", "transaction_id")
    s_amt_col = mapping.get("source_amount", "amount")
    s_time_col = mapping.get("source_time", "timestamp")
    
    t_id_col = mapping.get("target_id", "transaction_id")
    t_amt_col = mapping.get("target_amount", "amount")
    t_time_col = mapping.get("target_time", "timestamp")

    # Create shallow copies to prevent mutating input DataFrames
    s_df = source_df.copy()
    t_df = target_df.copy()

    # Normalize columns for exact evaluation
    s_df["_clean_id"] = s_df[s_id_col].astype(str).str.strip()
    s_df["_clean_amt"] = s_df[s_amt_col].apply(clean_decimal)
    s_df["_clean_time"] = s_df[s_time_col].apply(clean_datetime)
    s_df["_matched"] = False

    t_df["_clean_id"] = t_df[t_id_col].astype(str).str.strip()
    t_df["_clean_amt"] = t_df[t_amt_col].apply(clean_decimal)
    t_df["_clean_time"] = t_df[t_time_col].apply(clean_datetime)
    t_df["_matched"] = False

    # Fast index lookup for Target
    target_by_id = t_df.set_index("_clean_id", drop=False)

    # First Pass: Match by Transaction ID
    for idx, s_row in s_df.iterrows():
        s_id = s_row["_clean_id"]
        s_amt = s_row["_clean_amt"]
        s_time = s_row["_clean_time"]

        if s_id and s_id != "" and s_id != "nan" and s_id in target_by_id.index:
            t_row = target_by_id.loc[s_id]
            # Handle possible duplicate IDs in target
            if isinstance(t_row, pd.DataFrame):
                t_row = t_row.iloc[0]
            
            t_amt = t_row["_clean_amt"]
            t_time = t_row["_clean_time"]
            
            # Math comparison using exact base-10
            variance = abs(s_amt - t_amt)
            date_diff = abs((s_time - t_time).days)
            
            is_matched = (variance <= tolerance_threshold) and (date_diff <= 3)
            status = "MATCHED" if is_matched else "VALUE_MISMATCH" if variance > tolerance_threshold else "DATE_MISMATCH"
            
            matched_records.append({
                "transaction_id": s_id,
                "source_amount": s_amt,
                "target_amount": t_amt,
                "variance": variance,
                "status": status,
                "source_timestamp": s_time,
                "target_timestamp": t_time,
                "matching_checksum": compute_checksum(s_id, s_amt, s_time)
            })
            
            s_df.at[idx, "_matched"] = True
            t_df.loc[t_df["_clean_id"] == s_id, "_matched"] = True

    # Second Pass: Fallback Fuzzy Matching for unmatched elements (±3 day window, absolute amt <= 0.001)
    unmatched_s = s_df[~s_df["_matched"]]
    unmatched_t = t_df[~t_df["_matched"]].copy()

    for idx, s_row in unmatched_s.iterrows():
        s_amt = s_row["_clean_amt"]
        s_time = s_row["_clean_time"]
        s_id = s_row["_clean_id"]

        # Search in target DataFrame for matching records
        for t_idx, t_row in unmatched_t[~unmatched_t["_matched"]].iterrows():
            t_amt = t_row["_clean_amt"]
            t_time = t_row["_clean_time"]
            t_id = t_row["_clean_id"]
            
            variance = abs(s_amt - t_amt)
            date_diff = abs((s_time - t_time).days)
            
            if variance <= tolerance_threshold and date_diff <= 3:
                # Fallback match found!
                matched_records.append({
                    "transaction_id": f"FUZZY_{s_id if s_id else 'SRC'}_{t_id if t_id else 'TGT'}",
                    "source_amount": s_amt,
                    "target_amount": t_amt,
                    "variance": variance,
                    "status": "FUZZY_MATCHED",
                    "source_timestamp": s_time,
                    "target_timestamp": t_time,
                    "matching_checksum": compute_checksum(s_id or "F", s_amt, s_time)
                })
                s_df.at[idx, "_matched"] = True
                t_df.at[t_idx, "_matched"] = True
                unmatched_t.at[t_idx, "_matched"] = True
                break

    # Extract final unmatched dataframes
    unmatched_source_final = s_df[~s_df["_matched"]].drop(columns=["_clean_id", "_clean_amt", "_clean_time", "_matched"])
    unmatched_target_final = t_df[~t_df["_matched"]].drop(columns=["_clean_id", "_clean_amt", "_clean_time", "_matched"])
    
    # Render matches DataFrame
    matched_df = pd.DataFrame(matched_records) if matched_records else pd.DataFrame(columns=[
        "transaction_id", "source_amount", "target_amount", "variance", "status", "source_timestamp", "target_timestamp", "matching_checksum"
    ])

    return matched_df, unmatched_source_final, unmatched_target_final


def reconcile_three_party_ledgers(
    df1: pd.DataFrame,  # Internal Ledger
    df2: pd.DataFrame,  # Payment Gateway
    df3: pd.DataFrame,  # Bank Statement
    mappings: Dict[str, Dict[str, str]],  # {"file1": {...}, "file2": {...}, "file3": {...}}
    tolerance_threshold: Decimal = Decimal("0.001")
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Executes a high-precision 3-way reconciliation with a multi-conditional variance matrix.
    Computes delta comparisons and categorizes forensic root causes.
    """
    # Standardize column mappings
    map1 = mappings.get("file1", {})
    map2 = mappings.get("file2", {})
    map3 = mappings.get("file3", {})

    # Extract and clean datasets
    d1 = df1.copy()
    d1["_id"] = d1[map1.get("transaction_id", "transaction_id")].astype(str).str.strip()
    d1["_amt"] = d1[map1.get("amount", "amount")].apply(clean_decimal)
    d1["_time"] = d1[map1.get("timestamp", "timestamp")].apply(clean_datetime)

    d2 = df2.copy()
    d2["_id"] = d2[map2.get("transaction_id", "transaction_id")].astype(str).str.strip()
    d2["_amt"] = d2[map2.get("amount", "amount")].apply(clean_decimal)
    d2["_time"] = d2[map2.get("timestamp", "timestamp")].apply(clean_datetime)

    d3 = df3.copy()
    d3["_id"] = d3[map3.get("transaction_id", "transaction_id")].astype(str).str.strip()
    d3["_amt"] = d3[map3.get("amount", "amount")].apply(clean_decimal)
    d3["_time"] = d3[map3.get("timestamp", "timestamp")].apply(clean_datetime)

    # Collect unique transaction IDs across all parties
    all_ids = set(d1["_id"].dropna().unique()) | set(d2["_id"].dropna().unique()) | set(d3["_id"].dropna().unique())
    # Remove empty or nan string keys
    all_ids = {x for x in all_ids if x and x != "nan" and x != "None" and x != ""}

    # Group datasets for fast lookup
    d1_lookup = d1.set_index("_id", drop=False)
    d2_lookup = d2.set_index("_id", drop=False)
    d3_lookup = d3.set_index("_id", drop=False)

    reconciled_results = []
    audit_trail = []

    for tx_id in all_ids:
        # Check presence
        has_1 = tx_id in d1_lookup.index
        has_2 = tx_id in d2_lookup.index
        has_3 = tx_id in d3_lookup.index

        v1 = d1_lookup.loc[tx_id]["_amt"] if has_1 else None
        v2 = d2_lookup.loc[tx_id]["_amt"] if has_2 else None
        v3 = d3_lookup.loc[tx_id]["_amt"] if has_3 else None

        # Resolve duplicate records in lookup
        if isinstance(v1, pd.Series): v1 = v1.iloc[0]
        if isinstance(v2, pd.Series): v2 = v2.iloc[0]
        if isinstance(v3, pd.Series): v3 = v3.iloc[0]

        # Extract timestamps
        t1 = d1_lookup.loc[tx_id]["_time"] if has_1 else None
        t2 = d2_lookup.loc[tx_id]["_time"] if has_2 else None
        t3 = d3_lookup.loc[tx_id]["_time"] if has_3 else None

        if isinstance(t1, pd.Series): t1 = t1.iloc[0]
        if isinstance(t2, pd.Series): t2 = t2.iloc[0]
        if isinstance(t3, pd.Series): t3 = t3.iloc[0]

        # Determine variances
        d12 = abs(v1 - v2) if (has_1 and has_2) else None
        d23 = abs(v2 - v3) if (has_2 and has_3) else None
        d13 = abs(v1 - v3) if (has_1 and has_3) else None

        # Build reconciliation status & forensic analysis
        status = "UNRESOLVED"
        root_cause = "Unknown anomaly"
        correction_path = "Investigate record lifecycle"

        if has_1 and has_2 and has_3:
            # Check 3-way variance matching bounds
            all_match = (d12 <= tolerance_threshold) and (d23 <= tolerance_threshold) and (d13 <= tolerance_threshold)
            if all_match:
                status = "MATCHED"
                root_cause = "Perfect reconciliation"
                correction_path = "None required"
            else:
                status = "DISCREPANCY"
                if d12 > tolerance_threshold and d23 > tolerance_threshold:
                    root_cause = "Processor Discrepancy"
                    correction_path = "Query the gateway API to verify processing status; update processing logs."
                elif d13 > tolerance_threshold and d23 > tolerance_threshold:
                    root_cause = "Bank Settlement Variance"
                    correction_path = "Review bank transaction details; flag variance for manual audit adjustment."
                else:
                    root_cause = "Value variance mismatch"
                    correction_path = "Perform dual ledger manual audit"
        elif has_1 and not has_2 and not has_3:
            status = "UNRECONCILED_SOURCE"
            root_cause = "Unreconciled Internal Ledger"
            correction_path = "Verify system transaction logs; check for internal connection dropouts or system lag."
        elif not has_1 and (has_2 or has_3):
            status = "UNKNOWN_TRANSACTION"
            root_cause = "Unknown Transaction"
            correction_path = "Investigate payment capture flow; run internal systems audit to detect lost entries."
        elif has_1 and has_2 and not has_3:
            status = "MISSING_BANK_STATEMENT"
            root_cause = "Settlement Delay"
            correction_path = "Flags a settlement deposit delay. Check clearing cycle next business day."
        elif has_1 and has_3 and not has_2:
            status = "MISSING_PAYMENT_GATEWAY"
            root_cause = "Clearing Anomaly"
            correction_path = "Completed payment has no payment gateway clearing record. Investigate API logs."

        net_variance = max(
            [v for v in [d12, d23, d13] if v is not None] or [Decimal("0.0")]
        )

        record = {
            "transaction_id": tx_id,
            "internal_amount": v1,
            "gateway_amount": v2,
            "bank_amount": v3,
            "variance_12": d12,
            "variance_23": d23,
            "variance_13": d13,
            "max_variance": net_variance,
            "status": status,
            "root_cause": root_cause,
            "correction_path": correction_path,
            "timestamp": t1 or t2 or t3,
            "matching_checksum": compute_checksum(tx_id, v1 or v2 or v3, t1 or t2 or t3)
        }
        reconciled_results.append(record)
        
    return pd.DataFrame(reconciled_results), audit_trail
