"""Tests for RW-2: WeaverPack verify (rw_c_suite: RW-C1)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import compute_pack_hash, sha256_bytes
from origin.utilities.realityweaver.weaverpack import (
    verify,
    verify_manifest_schema,
    verify_pack_integrity,
)


def _make_manifest(files=None, extra_fields=None):
    """Helper to build a valid manifest dict."""
    if files is None:
        files = {
            "test.txt": {"sha256": sha256_bytes(b"hello"), "size": 5},
        }
    mf = {
        "schema_version": "0.1.0",
        "manifest_id": "RWMF-0000000000000001",
        "created_at": "2026-02-10T00:00:00Z",
        "weaverpack_id": "RWPK-0000000000000001",
        "authorship": "test",
        "license": "WCL-1.0",
        "files": files,
        "pack_hash": compute_pack_hash(files),
        "invariants_declared": ["RW-C1"],
    }
    if extra_fields:
        mf.update(extra_fields)
    return mf


class TestC1ManifestIntegrity:
    """C1-T1..C1-T4: Manifest integrity tests."""

    def test_c1_t1_valid_manifest_passes(self):
        """C1-T1: Valid manifest verifies against schema."""
        mf = _make_manifest()
        errors = verify_manifest_schema(mf)
        assert errors == []

    def test_c1_t2_wrong_pack_hash_fails(self):
        """C1-T2: Manifest with wrong pack_hash fails."""
        mf = _make_manifest()
        mf["pack_hash"] = "0" * 64
        errors = verify_pack_integrity(mf)
        assert len(errors) == 1
        assert "pack_hash mismatch" in errors[0]

    def test_c1_t3_missing_field_fails(self):
        """C1-T3: Missing required field detected."""
        mf = _make_manifest()
        del mf["manifest_id"]
        errors = verify_manifest_schema(mf)
        assert any("manifest_id" in e for e in errors)

    def test_c1_t4_file_on_disk_verification(self):
        """C1-T4: Verify files actually exist and match."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = b"hello"
            filepath = os.path.join(tmpdir, "test.txt")
            with open(filepath, "wb") as f:
                f.write(content)

            files = {
                "test.txt": {"sha256": sha256_bytes(content), "size": len(content)},
            }
            mf = _make_manifest(files=files)
            mf_path = os.path.join(tmpdir, "manifest.json")
            with open(mf_path, "w") as f:
                json.dump(mf, f)

            result = verify(mf_path, tmpdir)
            assert result.passed
            assert result.files_checked == 1

    def test_c1_t4_missing_file_detected(self):
        """C1-T4: File listed in manifest but not on disk is detected."""
        with tempfile.TemporaryDirectory() as tmpdir:
            files = {
                "missing.txt": {"sha256": "a" * 64, "size": 10},
            }
            mf = _make_manifest(files=files)
            mf_path = os.path.join(tmpdir, "manifest.json")
            with open(mf_path, "w") as f:
                json.dump(mf, f)

            result = verify(mf_path, tmpdir)
            assert not result.passed
            assert any("not found" in e for e in result.errors)
