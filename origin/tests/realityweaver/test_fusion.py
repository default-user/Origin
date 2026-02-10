"""Tests for RW-10: Fusion operator (rw_fusion_suite)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import compute_pack_hash, sha256_bytes
from origin.utilities.realityweaver.fusion import (
    fusion,
    validate_merge_plan,
)


def _make_manifests_and_plan():
    """Build two source manifests and a merge plan."""
    shared_hash = sha256_bytes(b"shared content")
    files_a = {
        "shared.txt": {"sha256": shared_hash, "size": 14},
        "only_a.txt": {"sha256": sha256_bytes(b"only in a"), "size": 9},
    }
    files_b = {
        "shared.txt": {"sha256": sha256_bytes(b"different content"), "size": 17},
        "only_b.txt": {"sha256": sha256_bytes(b"only in b"), "size": 9},
    }

    mf_a = {
        "schema_version": "0.1.0",
        "manifest_id": "RWMF-000000000000000a",
        "created_at": "2026-02-10T00:00:00Z",
        "weaverpack_id": "RWPK-000000000000000a",
        "authorship": "test",
        "license": "WCL-1.0",
        "disclosure_tier": "internal",
        "sensitivity": {"pii_risk": "none", "contains_personal": False, "redacted": False},
        "timebase": {"epoch": "2026-02-10T00:00:00Z", "resolution_ns": 1000000},
        "files": files_a,
        "pack_hash": compute_pack_hash(files_a),
        "invariants_declared": ["RW-C1", "RW-C8", "RW-C10", "RW-C11"],
    }
    mf_b = {
        "schema_version": "0.1.0",
        "manifest_id": "RWMF-000000000000000b",
        "created_at": "2026-02-10T00:00:00Z",
        "weaverpack_id": "RWPK-000000000000000b",
        "authorship": "test",
        "license": "WCL-1.0",
        "disclosure_tier": "internal",
        "sensitivity": {"pii_risk": "none", "contains_personal": False, "redacted": False},
        "timebase": {"epoch": "2026-02-10T00:00:00Z", "resolution_ns": 1000000},
        "files": files_b,
        "pack_hash": compute_pack_hash(files_b),
        "invariants_declared": ["RW-C1", "RW-C8", "RW-C10", "RW-C11"],
    }

    merge_plan = {
        "schema_version": "0.1.0",
        "merge_plan_id": "RWMP-0000000000000001",
        "created_at": "2026-02-10T00:00:00Z",
        "source_manifests": [
            {"manifest_id": "RWMF-000000000000000a", "weaverpack_id": "RWPK-000000000000000a", "role": "primary"},
            {"manifest_id": "RWMF-000000000000000b", "weaverpack_id": "RWPK-000000000000000b", "role": "secondary"},
        ],
        "target_weaverpack_id": "RWPK-00000000merged01",
        "strategy": "primary_wins",
        "file_resolutions": [
            {"path": "shared.txt", "resolution": "take_primary", "note": "Primary source wins."},
        ],
        "timebase_alignment": {
            "canonical_epoch": "2026-02-10T00:00:00Z",
            "resolution_ns": 1000000,
            "source_alignments": [
                {"manifest_id": "RWMF-000000000000000a", "offset_ns": 0},
                {"manifest_id": "RWMF-000000000000000b", "offset_ns": 0},
            ],
        },
        "license_resolution": {
            "resolved_license": "WCL-1.0",
            "method": "least_permissive",
            "source_licenses": [
                {"manifest_id": "RWMF-000000000000000a", "license": "WCL-1.0"},
                {"manifest_id": "RWMF-000000000000000b", "license": "WCL-1.0"},
            ],
        },
        "expected_conflicts": [
            {"path": "shared.txt", "conflict_type": "content_divergence"},
        ],
    }

    return mf_a, mf_b, merge_plan


class TestFusionSuite:
    """M-T1..M-T5: Fusion operator tests."""

    def test_m_t1_fusion_requires_merge_plan(self):
        """M-T1: Fusion without merge_plan fails."""
        mf_a, mf_b, _ = _make_manifests_and_plan()
        result = fusion([mf_a, mf_b], {})
        assert not result.passed
        assert any("RW-C8" in e for e in result.errors)

    def test_m_t2_fusion_emits_conflict_ledger(self):
        """M-T2: Fusion output includes valid conflict_ledger."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        result = fusion([mf_a, mf_b], plan)
        assert result.passed
        assert result.conflict_ledger is not None
        assert result.conflict_ledger["ledger_id"].startswith("RWCL-")
        assert result.conflict_ledger["summary"]["total_conflicts"] == 1

    def test_m_t3_silent_merge_rejected(self):
        """M-T3: Fusion without explicit merge plan fails."""
        mf_a, mf_b, _ = _make_manifests_and_plan()
        # Empty plan = no explicit merge plan
        result = fusion([mf_a, mf_b], {})
        assert not result.passed

    def test_m_t4_conflict_resolution_recorded(self):
        """M-T4: Conflicts are recorded in the ledger, not smoothed."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        result = fusion([mf_a, mf_b], plan)
        assert result.passed
        conflicts = result.conflict_ledger["conflicts"]
        assert len(conflicts) == 1
        assert conflicts[0]["path"] == "shared.txt"
        assert conflicts[0]["resolved"]
        assert conflicts[0]["resolution"] == "take_primary"

    def test_m_t5_target_manifest_verifies(self):
        """M-T5: Fused WeaverPack has valid pack_hash."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        result = fusion([mf_a, mf_b], plan)
        assert result.passed
        target = result.target_manifest
        expected = compute_pack_hash(target["files"])
        assert target["pack_hash"] == expected

    def test_fusion_integrity_failure(self):
        """Fusion with tampered source fails (RW-C1)."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        mf_a["pack_hash"] = "0" * 64
        result = fusion([mf_a, mf_b], plan)
        assert not result.passed
        assert any("integrity" in e.lower() for e in result.errors)

    def test_fusion_plan_validation(self):
        """Merge plan missing required fields is rejected."""
        errors = validate_merge_plan({"merge_plan_id": "test"})
        assert len(errors) > 0

    def test_dt_t2_fusion_determinism(self):
        """DT-T2: Same fusion inputs produce same conflict ledgers."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        r1 = fusion([mf_a, mf_b], plan)
        r2 = fusion([mf_a, mf_b], plan)
        assert r1.conflict_ledger["summary"] == r2.conflict_ledger["summary"]
        assert r1.target_manifest["pack_hash"] == r2.target_manifest["pack_hash"]

    def test_lc_t2_least_permissive_license(self):
        """LC-T2: Fusion resolves to declared license."""
        mf_a, mf_b, plan = _make_manifests_and_plan()
        result = fusion([mf_a, mf_b], plan)
        assert result.passed
        assert result.target_manifest["license"] == "WCL-1.0"

    def test_no_conflict_fusion(self):
        """Fusion with no overlapping files produces empty conflict ledger."""
        files_a = {"a.txt": {"sha256": sha256_bytes(b"a"), "size": 1}}
        files_b = {"b.txt": {"sha256": sha256_bytes(b"b"), "size": 1}}

        mf_a = {
            "schema_version": "0.1.0",
            "manifest_id": "RWMF-000000000000000a",
            "weaverpack_id": "RWPK-000000000000000a",
            "files": files_a,
            "pack_hash": compute_pack_hash(files_a),
            "invariants_declared": ["RW-C1"],
            "authorship": "test",
            "license": "WCL-1.0",
        }
        mf_b = {
            "schema_version": "0.1.0",
            "manifest_id": "RWMF-000000000000000b",
            "weaverpack_id": "RWPK-000000000000000b",
            "files": files_b,
            "pack_hash": compute_pack_hash(files_b),
            "invariants_declared": ["RW-C1"],
            "authorship": "test",
            "license": "WCL-1.0",
        }

        plan = {
            "schema_version": "0.1.0",
            "merge_plan_id": "RWMP-0000000000000002",
            "source_manifests": [
                {"manifest_id": "RWMF-000000000000000a", "weaverpack_id": "RWPK-000000000000000a", "role": "primary"},
                {"manifest_id": "RWMF-000000000000000b", "weaverpack_id": "RWPK-000000000000000b", "role": "secondary"},
            ],
            "target_weaverpack_id": "RWPK-merged00000002",
            "strategy": "union",
            "file_resolutions": [],
            "timebase_alignment": {
                "canonical_epoch": "2026-02-10T00:00:00Z",
                "resolution_ns": 1000000,
                "source_alignments": [],
            },
            "license_resolution": {
                "resolved_license": "WCL-1.0",
                "method": "least_permissive",
            },
            "expected_conflicts": [],
        }

        result = fusion([mf_a, mf_b], plan)
        assert result.passed
        assert result.conflict_ledger["summary"]["total_conflicts"] == 0
        assert len(result.target_manifest["files"]) == 2
