import io
import unittest
import pandas as pd
from decimal import Decimal
from datetime import datetime

from app.controllers.parser import parse_structured_xml_payload
from app.controllers.engine import reconcile_two_party_ledgers, reconcile_three_party_ledgers
from app.controllers.aligner import get_deterministic_fallback_alignment

class TestReconIQ(unittest.TestCase):

    def test_xml_hierarchical_flattening(self):
        """Verifies that our custom XML flattener strips namespaces and resolves nesting collisions."""
        xml_data = """<transactions xmlns="http://schemas.recon-iq.com/ledger">
            <transaction>
                <id>TX_99211</id>
                <value type="primary_charge">150.00</value>
                <value type="tax_offset">12.50</value>
            </transaction>
            <transaction>
                <id>TX_99212</id>
                <value type="primary_charge">200.00</value>
                <value type="tax_offset">0.00</value>
            </transaction>
        </transactions>"""
        
        stream = io.BytesIO(xml_data.encode("utf-8"))
        df = parse_structured_xml_payload(stream)
        
        self.assertEqual(len(df), 2)
        
        id_col = "transaction_id" if "transaction_id" in df.columns else "id"
        val_col = "transaction_value_primary_charge" if "transaction_value_primary_charge" in df.columns else "value_primary_charge"
        
        self.assertEqual(df.loc[0, id_col], "TX_99211")
        self.assertEqual(df.loc[0, val_col], "150.00")

    def test_precise_decimal_two_way_matching(self):
        """Ensures two-way matching uses precise base-10 math and handles the ±3 days window fallback."""
        source_records = [
            {"tx_id": "TX_A", "val": "100.100", "dt": "2026-06-01"},
            {"tx_id": "TX_B", "val": "200.505", "dt": "2026-06-02"},
            {"tx_id": "TX_C", "val": "300.000", "dt": "2026-06-03"}
        ]
        
        target_records = [
            {"gateway_id": "TX_A", "posted_val": "100.100", "posted_dt": "2026-06-01"},
            {"gateway_id": "TX_B", "posted_val": "200.510", "posted_dt": "2026-06-02"},
            {"gateway_id": "TX_D", "posted_val": "300.000", "posted_dt": "2026-06-05"}
        ]
        
        s_df = pd.DataFrame(source_records)
        t_df = pd.DataFrame(target_records)
        
        mapping = {
            "source_id": "tx_id",
            "source_amount": "val",
            "source_time": "dt",
            "target_id": "gateway_id",
            "target_amount": "posted_val",
            "target_time": "posted_dt"
        }
        
        matched_df, unmatched_s, unmatched_t = reconcile_two_party_ledgers(
            s_df, t_df, mapping, Decimal("0.001")
        )
        
        self.assertEqual(len(matched_df), 3)
        
        tx_a_res = matched_df[matched_df["transaction_id"] == "TX_A"].iloc[0]
        self.assertEqual(tx_a_res["status"], "MATCHED")
        
        tx_b_res = matched_df[matched_df["transaction_id"] == "TX_B"].iloc[0]
        self.assertEqual(tx_b_res["status"], "VALUE_MISMATCH")
        
        fuzzy_res = matched_df[matched_df["status"] == "FUZZY_MATCHED"].iloc[0]
        self.assertEqual(fuzzy_res["source_amount"], Decimal("300.000"))
        self.assertEqual(fuzzy_res["target_amount"], Decimal("300.000"))

    def test_three_way_variance_forensic_matrix(self):
        """Validates the tri-directional matching algorithm and root-cause classification."""
        df1 = pd.DataFrame([
            {"id": "TX_01", "amt": "1000.00", "ts": "2026-06-01"},
            {"id": "TX_02", "amt": "2000.00", "ts": "2026-06-01"},
            {"id": "TX_03", "amt": "3000.00", "ts": "2026-06-01"}
        ])
        df2 = pd.DataFrame([
            {"id": "TX_01", "amt": "1000.00", "ts": "2026-06-01"},
            {"id": "TX_02", "amt": "2000.01", "ts": "2026-06-01"},
            {"id": "TX_04", "amt": "4000.00", "ts": "2026-06-01"}
        ])
        df3 = pd.DataFrame([
            {"id": "TX_01", "amt": "1000.00", "ts": "2026-06-01"},
            {"id": "TX_02", "amt": "2000.00", "ts": "2026-06-01"},
            {"id": "TX_04", "amt": "4000.00", "ts": "2026-06-01"}
        ])
        
        mappings = {
            "file1": {"transaction_id": "id", "amount": "amt", "timestamp": "ts"},
            "file2": {"transaction_id": "id", "amount": "amt", "timestamp": "ts"},
            "file3": {"transaction_id": "id", "amount": "amt", "timestamp": "ts"}
        }
        
        results, _ = reconcile_three_party_ledgers(df1, df2, df3, mappings, Decimal("0.001"))
        
        tx01 = results[results["transaction_id"] == "TX_01"].iloc[0]
        self.assertEqual(tx01["status"], "MATCHED")
        
        tx02 = results[results["transaction_id"] == "TX_02"].iloc[0]
        self.assertEqual(tx02["status"], "DISCREPANCY")
        self.assertEqual(tx02["root_cause"], "Processor Discrepancy")
        
        tx03 = results[results["transaction_id"] == "TX_03"].iloc[0]
        self.assertEqual(tx03["status"], "UNRECONCILED_SOURCE")
        self.assertEqual(tx03["root_cause"], "Unreconciled Internal Ledger")
        
        tx04 = results[results["transaction_id"] == "TX_04"].iloc[0]
        self.assertEqual(tx04["status"], "UNKNOWN_TRANSACTION")
        self.assertEqual(tx04["root_cause"], "Unknown Transaction")

    def test_deterministic_alignment_rules(self):
        """Tests the regex-based schema-mapper fallback is robust and covers all primitives."""
        metadata = {
            "columns": {
                "Transaction_ID_Reference": {"inferred_type": "object", "samples": ["TX_1"]},
                "posted_amount_val": {"inferred_type": "float64", "samples": ["120.50"]},
                "Event_Timestamp_UTC": {"inferred_type": "object", "samples": ["2026-06-07T12:00:00Z"]},
                "reconciliation_memo_notes": {"inferred_type": "object", "samples": ["Direct deposit"]}
            }
        }
        
        alignment = get_deterministic_fallback_alignment(metadata)
        
        self.assertEqual(alignment.overall_confidence, 0.75)
        
        mappings_dict = {m.target_primitive: m.raw_field_name for m in alignment.mappings}
        self.assertEqual(mappings_dict["transaction_id"], "Transaction_ID_Reference")
        self.assertEqual(mappings_dict["amount"], "posted_amount_val")
        self.assertEqual(mappings_dict["timestamp"], "Event_Timestamp_UTC")
        self.assertEqual(mappings_dict["metadata"], "reconciliation_memo_notes")

if __name__ == "__main__":
    unittest.main()
