"""
Receipt emitter for all RealityWeaver operations.

Every operation emits a receipt conforming to receipt_schema_v0.
Receipts are the audit trail for replay verification (RW-C7).
"""

from __future__ import annotations

import json

from .primitives import canonical_json_pretty, generate_id, now_iso


def emit_receipt(
    operation: str,
    operator_id: str,
    inputs: dict,
    outputs: dict,
    gates: list[dict],
    invariants_checked: list[str],
    error: str | None = None,
) -> dict:
    """
    Emit a receipt for a RealityWeaver operation.

    passed = True only if no gate has status "fail".
    """
    passed = all(g.get("status") != "fail" for g in gates)
    if error:
        passed = False

    return {
        "schema_version": "0.1.0",
        "receipt_id": generate_id("RWRC"),
        "operation": operation,
        "timestamp": now_iso(),
        "operator_id": operator_id,
        "inputs": inputs,
        "outputs": outputs,
        "gates": gates,
        "passed": passed,
        "invariants_checked": invariants_checked,
        "error": error,
    }


def gate(name: str, status: str, detail: str) -> dict:
    """Create a gate check result."""
    if status not in ("pass", "fail", "skip"):
        raise ValueError(f"Invalid gate status: {status}")
    return {"gate": name, "status": status, "detail": detail}


def write_receipt(receipt: dict, path: str) -> None:
    """Write a receipt to a JSON file."""
    data = canonical_json_pretty(receipt)
    with open(path, "wb") as f:
        f.write(data)


def load_receipt(path: str) -> dict:
    """Load a receipt from a JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_receipt_schema(receipt: dict) -> list[str]:
    """Verify a receipt has all required fields. Returns list of errors."""
    errors = []
    required = [
        "schema_version", "receipt_id", "operation", "timestamp",
        "operator_id", "inputs", "outputs", "gates", "passed",
        "invariants_checked",
    ]
    for field_name in required:
        if field_name not in receipt:
            errors.append(f"Missing required field: {field_name}")
    if "gates" in receipt:
        for i, g in enumerate(receipt["gates"]):
            for gf in ("gate", "status", "detail"):
                if gf not in g:
                    errors.append(f"Gate {i} missing field: {gf}")
    return errors
