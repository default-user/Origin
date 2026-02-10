"""
RW-2: WeaverPack verify.

Read-only verification of WeaverPack manifests against their file entries.
Deterministic. No side effects. Fail-closed on any mismatch.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from .primitives import compute_pack_hash, sha256_file


@dataclass
class VerifyResult:
    """Result of a WeaverPack verification."""

    passed: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    files_checked: int = 0
    invariants_checked: list[str] = field(default_factory=list)


def load_manifest(manifest_path: str) -> dict:
    """Load and parse a manifest JSON file."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_manifest_schema(manifest: dict) -> list[str]:
    """Check that manifest has required fields. Returns list of errors."""
    errors = []
    required = [
        "schema_version", "manifest_id", "created_at", "weaverpack_id",
        "authorship", "license", "files", "pack_hash", "invariants_declared",
    ]
    for field_name in required:
        if field_name not in manifest:
            errors.append(f"Missing required field: {field_name}")
    if "files" in manifest and not isinstance(manifest["files"], dict):
        errors.append("'files' must be an object")
    if "invariants_declared" in manifest and not isinstance(manifest["invariants_declared"], list):
        errors.append("'invariants_declared' must be an array")
    return errors


def verify_pack_integrity(manifest: dict) -> list[str]:
    """Verify pack_hash matches file entries. Returns list of errors."""
    errors = []
    if "files" not in manifest or "pack_hash" not in manifest:
        errors.append("Cannot verify integrity: missing files or pack_hash")
        return errors
    expected = compute_pack_hash(manifest["files"])
    if expected != manifest["pack_hash"]:
        errors.append(
            f"pack_hash mismatch: expected {expected}, got {manifest['pack_hash']}"
        )
    return errors


def verify_files_on_disk(manifest: dict, base_path: str) -> tuple[list[str], int]:
    """
    Verify that files listed in manifest exist on disk with correct hashes.

    Returns (errors, files_checked).
    """
    errors = []
    checked = 0
    for rel_path, entry in manifest.get("files", {}).items():
        full_path = os.path.join(base_path, rel_path)
        if not os.path.isfile(full_path):
            errors.append(f"File not found: {rel_path}")
            continue
        actual_hash = sha256_file(full_path)
        if actual_hash != entry["sha256"]:
            errors.append(
                f"Hash mismatch for {rel_path}: expected {entry['sha256']}, got {actual_hash}"
            )
        actual_size = os.path.getsize(full_path)
        if actual_size != entry["size"]:
            errors.append(
                f"Size mismatch for {rel_path}: expected {entry['size']}, got {actual_size}"
            )
        checked += 1
    return errors, checked


def verify(manifest_path: str, base_path: str | None = None) -> VerifyResult:
    """
    Full WeaverPack verification (RW-C1).

    1. Load and validate manifest schema
    2. Verify pack_hash integrity
    3. Verify files on disk (if base_path provided)

    Fail-closed: any error means verification fails.
    """
    result = VerifyResult(passed=False)
    result.invariants_checked.append("RW-C1")

    try:
        manifest = load_manifest(manifest_path)
    except (json.JSONDecodeError, OSError) as e:
        result.errors.append(f"Failed to load manifest: {e}")
        return result

    # Schema check
    schema_errors = verify_manifest_schema(manifest)
    result.errors.extend(schema_errors)

    # Integrity check
    integrity_errors = verify_pack_integrity(manifest)
    result.errors.extend(integrity_errors)

    # File-on-disk check
    if base_path is not None:
        file_errors, checked = verify_files_on_disk(manifest, base_path)
        result.errors.extend(file_errors)
        result.files_checked = checked

    result.passed = len(result.errors) == 0
    return result
