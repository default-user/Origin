"""
RW-5: Redact and lineage proofs.

Non-destructive redaction with lineage preservation (RW-C4).
Redacted artefacts maintain provable lineage to their originals.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field

from .primitives import canonical_json, generate_id, now_iso, sha256_bytes


REDACTION_TOKEN = "[[REDACTED]]"


@dataclass
class RedactionEntry:
    """A single redaction applied to content."""

    path: str
    pattern: str
    occurrences: int
    original_sha256: str
    redacted_sha256: str


@dataclass
class RedactionResult:
    """Result of a redaction operation."""

    manifest: dict
    redactions: list[RedactionEntry] = field(default_factory=list)
    lineage_entry: dict | None = None
    receipt: dict | None = None


def redact_bytes(data: bytes, patterns: list[str]) -> tuple[bytes, list[tuple[str, int]]]:
    """
    Apply redaction patterns to bytes content.

    Returns (redacted_bytes, list of (pattern, occurrence_count)).
    Non-destructive: original is not modified.
    """
    text = data.decode("utf-8", errors="replace")
    applied = []
    for pattern in patterns:
        count = len(re.findall(pattern, text))
        if count > 0:
            text = re.sub(pattern, REDACTION_TOKEN, text)
            applied.append((pattern, count))
    return text.encode("utf-8"), applied


def redact_manifest(
    manifest: dict,
    patterns: list[str],
    file_contents: dict[str, bytes],
) -> RedactionResult:
    """
    Create a redacted copy of a manifest and its file contents (RW-C4).

    - Original manifest is NOT modified.
    - Redacted manifest gets a new manifest_id and lineage entry.
    - Each redacted file gets new sha256 and size.
    - Lineage entry points back to original manifest.

    Requires: patterns list is non-empty.
    Fail-closed: if no patterns provided, raises ValueError.
    """
    if not patterns:
        raise ValueError("Redaction requires at least one pattern (RW-C4).")

    result = RedactionResult(manifest=copy.deepcopy(manifest))
    new_manifest = result.manifest
    old_manifest_id = manifest["manifest_id"]
    new_manifest_id = generate_id("RWMF")
    new_manifest["manifest_id"] = new_manifest_id

    # Apply redactions to file contents
    for rel_path, content in file_contents.items():
        if rel_path not in new_manifest.get("files", {}):
            continue
        original_sha = sha256_bytes(content)
        redacted_content, applied = redact_bytes(content, patterns)
        if applied:
            redacted_sha = sha256_bytes(redacted_content)
            new_manifest["files"][rel_path]["sha256"] = redacted_sha
            new_manifest["files"][rel_path]["size"] = len(redacted_content)
            total_occurrences = sum(count for _, count in applied)
            for pattern, count in applied:
                result.redactions.append(RedactionEntry(
                    path=rel_path,
                    pattern=pattern,
                    occurrences=count,
                    original_sha256=original_sha,
                    redacted_sha256=redacted_sha,
                ))

    # Mark as redacted in sensitivity
    if "sensitivity" not in new_manifest:
        new_manifest["sensitivity"] = {}
    new_manifest["sensitivity"]["redacted"] = True

    # Add lineage entry (RW-C4: lineage provable to original)
    lineage_entry = {
        "operation": "redact",
        "source_manifest_id": old_manifest_id,
        "timestamp": now_iso(),
        "receipt_ref": None,  # filled by receipt emitter
    }
    if "lineage" not in new_manifest:
        new_manifest["lineage"] = []
    new_manifest["lineage"].append(lineage_entry)
    result.lineage_entry = lineage_entry

    # Recompute pack_hash
    from .primitives import compute_pack_hash
    new_manifest["pack_hash"] = compute_pack_hash(new_manifest["files"])

    return result


def verify_redaction_lineage(redacted_manifest: dict) -> list[str]:
    """
    Verify that a redacted manifest has valid lineage (RW-C4).

    Returns list of errors (empty if valid).
    """
    errors = []
    if not redacted_manifest.get("sensitivity", {}).get("redacted", False):
        errors.append("Manifest marked as redacted but sensitivity.redacted is false.")
    lineage = redacted_manifest.get("lineage", [])
    redact_entries = [e for e in lineage if e.get("operation") == "redact"]
    if not redact_entries:
        errors.append("Redacted manifest has no redaction lineage entry (RW-C4 violation).")
    for entry in redact_entries:
        if not entry.get("source_manifest_id"):
            errors.append("Redaction lineage entry missing source_manifest_id.")
    return errors
