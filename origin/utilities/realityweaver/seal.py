"""
RW-6: Seal and commit (commitment only).

Seal emits a commitment (hash-based) without publishing or disclosing content.
No auto-publish. No external egress. Commitment only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .primitives import (
    canonical_json,
    compute_pack_hash,
    generate_id,
    now_iso,
    sha256_bytes,
)


@dataclass
class SealCommitment:
    """A sealed commitment to a WeaverPack's state."""

    commitment_id: str
    manifest_id: str
    weaverpack_id: str
    pack_hash: str
    commitment_hash: str
    timestamp: str
    sealed: bool = True


@dataclass
class SealResult:
    """Result of a seal operation."""

    commitment: SealCommitment
    receipt: dict | None = None


def compute_commitment_hash(manifest: dict) -> str:
    """
    Compute a commitment hash over the manifest's canonical form.

    This is a hash-of-hash: SHA-256 of the canonical JSON of the manifest.
    Deterministic: same manifest -> same commitment.
    """
    canonical = canonical_json(manifest)
    return sha256_bytes(canonical)


def seal(manifest: dict) -> SealResult:
    """
    Seal a WeaverPack manifest (RW-C1 + commitment only).

    1. Verify manifest has required fields.
    2. Verify pack_hash integrity.
    3. Compute commitment hash.
    4. Return commitment (no publish, no egress).

    Fail-closed: if pack_hash doesn't match, raises ValueError.
    """
    # Verify required fields
    for field_name in ("manifest_id", "weaverpack_id", "files", "pack_hash"):
        if field_name not in manifest:
            raise ValueError(f"Cannot seal: missing {field_name}")

    # Verify pack_hash
    expected = compute_pack_hash(manifest["files"])
    if expected != manifest["pack_hash"]:
        raise ValueError(
            f"Cannot seal: pack_hash mismatch (expected {expected}, got {manifest['pack_hash']})"
        )

    commitment_hash = compute_commitment_hash(manifest)

    commitment = SealCommitment(
        commitment_id=generate_id("RWSC"),
        manifest_id=manifest["manifest_id"],
        weaverpack_id=manifest["weaverpack_id"],
        pack_hash=manifest["pack_hash"],
        commitment_hash=commitment_hash,
        timestamp=now_iso(),
    )

    return SealResult(commitment=commitment)


def verify_commitment(manifest: dict, commitment: SealCommitment) -> list[str]:
    """
    Verify a commitment against a manifest.

    Returns list of errors (empty if valid).
    """
    errors = []
    if manifest.get("manifest_id") != commitment.manifest_id:
        errors.append("manifest_id mismatch")
    if manifest.get("pack_hash") != commitment.pack_hash:
        errors.append("pack_hash mismatch")
    expected_hash = compute_commitment_hash(manifest)
    if expected_hash != commitment.commitment_hash:
        errors.append("commitment_hash mismatch")
    return errors
