"""Tests for receipt emission and validation (receipt_schema_suite)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.receipts import (
    emit_receipt,
    gate,
    load_receipt,
    verify_receipt_schema,
    write_receipt,
)


class TestReceiptSchema:
    """RS-T1..RS-T3: Receipt schema tests."""

    def test_rs_t1_receipt_conforms_to_schema(self):
        """RS-T1: Generated receipt validates against schema."""
        receipt = emit_receipt(
            operation="verify",
            operator_id="RW-2",
            inputs={"manifest_path": "test.json"},
            outputs={"passed": True},
            gates=[gate("integrity", "pass", "ok")],
            invariants_checked=["RW-C1"],
        )
        errors = verify_receipt_schema(receipt)
        assert errors == []

    def test_rs_t2_missing_field_fails(self):
        """RS-T2: Missing field causes validation failure."""
        receipt = {"schema_version": "0.1.0"}
        errors = verify_receipt_schema(receipt)
        assert len(errors) > 0

    def test_rs_t3_gates_populated(self):
        """RS-T3: Gates are populated with proper structure."""
        receipt = emit_receipt(
            operation="seal",
            operator_id="RW-6",
            inputs={},
            outputs={},
            gates=[
                gate("integrity", "pass", "hash matches"),
                gate("consent", "skip", "not applicable"),
            ],
            invariants_checked=["RW-C1"],
        )
        assert len(receipt["gates"]) == 2
        for g in receipt["gates"]:
            assert "gate" in g
            assert "status" in g
            assert "detail" in g

    def test_receipt_passed_logic(self):
        """passed = True only if no gate fails."""
        receipt_pass = emit_receipt(
            operation="verify", operator_id="test",
            inputs={}, outputs={},
            gates=[gate("g1", "pass", "ok"), gate("g2", "skip", "na")],
            invariants_checked=[],
        )
        assert receipt_pass["passed"]

        receipt_fail = emit_receipt(
            operation="verify", operator_id="test",
            inputs={}, outputs={},
            gates=[gate("g1", "pass", "ok"), gate("g2", "fail", "bad")],
            invariants_checked=[],
        )
        assert not receipt_fail["passed"]

    def test_receipt_write_and_load(self):
        """Receipt can be written and loaded."""
        receipt = emit_receipt(
            operation="verify", operator_id="test",
            inputs={}, outputs={},
            gates=[gate("g1", "pass", "ok")],
            invariants_checked=["RW-C1"],
        )
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            write_receipt(receipt, path)
            loaded = load_receipt(path)
            assert loaded["operation"] == "verify"
            assert loaded["passed"]
        finally:
            os.unlink(path)

    def test_gate_invalid_status_raises(self):
        """Invalid gate status raises ValueError."""
        try:
            gate("test", "invalid", "detail")
            assert False, "Should have raised"
        except ValueError:
            pass
