"""Tests for RW-5 (redact) and RW-6 (seal)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import compute_pack_hash, sha256_bytes
from origin.utilities.realityweaver.redact import (
    redact_bytes,
    redact_manifest,
    verify_redaction_lineage,
    REDACTION_TOKEN,
)
from origin.utilities.realityweaver.seal import (
    compute_commitment_hash,
    seal,
    verify_commitment,
)


def _make_manifest():
    content = b"Hello secret-key-12345 world"
    files = {
        "doc.txt": {"sha256": sha256_bytes(content), "size": len(content)},
    }
    return {
        "schema_version": "0.1.0",
        "manifest_id": "RWMF-0000000000000001",
        "created_at": "2026-02-10T00:00:00Z",
        "weaverpack_id": "RWPK-0000000000000001",
        "authorship": "test",
        "license": "WCL-1.0",
        "files": files,
        "pack_hash": compute_pack_hash(files),
        "invariants_declared": ["RW-C1", "RW-C4"],
    }, {"doc.txt": content}


class TestRedaction:
    """RW-C4: Redaction lineage tests."""

    def test_c4_t1_redaction_preserves_lineage(self):
        """C4-T1: Redacted manifest has lineage entry."""
        manifest, contents = _make_manifest()
        result = redact_manifest(manifest, [r"secret-key-\d+"], contents)
        assert len(result.manifest["lineage"]) == 1
        assert result.manifest["lineage"][0]["operation"] == "redact"
        assert result.manifest["lineage"][0]["source_manifest_id"] == "RWMF-0000000000000001"

    def test_c4_t2_redaction_non_destructive(self):
        """C4-T2: Original manifest is not modified."""
        manifest, contents = _make_manifest()
        original_hash = manifest["pack_hash"]
        redact_manifest(manifest, [r"secret-key-\d+"], contents)
        assert manifest["pack_hash"] == original_hash

    def test_c4_t3_redaction_without_patterns_fails(self):
        """C4-T3: Redaction without patterns raises."""
        manifest, contents = _make_manifest()
        try:
            redact_manifest(manifest, [], contents)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_redact_bytes_replaces(self):
        data = b"my password is hunter2"
        redacted, applied = redact_bytes(data, [r"hunter2"])
        assert REDACTION_TOKEN.encode() in redacted
        assert len(applied) == 1
        assert applied[0][1] == 1  # 1 occurrence

    def test_verify_redaction_lineage_valid(self):
        manifest, contents = _make_manifest()
        result = redact_manifest(manifest, [r"secret"], contents)
        errors = verify_redaction_lineage(result.manifest)
        assert errors == []

    def test_verify_redaction_lineage_missing(self):
        manifest = {"sensitivity": {"redacted": True}, "lineage": []}
        errors = verify_redaction_lineage(manifest)
        assert any("RW-C4" in e for e in errors)


class TestSeal:
    """RW-C1 + seal commitment tests."""

    def test_seal_valid_manifest(self):
        manifest, _ = _make_manifest()
        result = seal(manifest)
        assert result.commitment.sealed
        assert result.commitment.manifest_id == manifest["manifest_id"]
        assert result.commitment.pack_hash == manifest["pack_hash"]

    def test_seal_tampered_manifest_fails(self):
        manifest, _ = _make_manifest()
        manifest["pack_hash"] = "0" * 64
        try:
            seal(manifest)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "mismatch" in str(e)

    def test_commitment_hash_deterministic(self):
        manifest, _ = _make_manifest()
        h1 = compute_commitment_hash(manifest)
        h2 = compute_commitment_hash(manifest)
        assert h1 == h2

    def test_verify_commitment_valid(self):
        manifest, _ = _make_manifest()
        result = seal(manifest)
        errors = verify_commitment(manifest, result.commitment)
        assert errors == []

    def test_verify_commitment_tampered(self):
        manifest, _ = _make_manifest()
        result = seal(manifest)
        result.commitment.commitment_hash = "bad"
        errors = verify_commitment(manifest, result.commitment)
        assert len(errors) > 0
