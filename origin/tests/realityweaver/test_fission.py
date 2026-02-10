"""Tests for RW-9: Fission operator (rw_fission_suite)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import compute_pack_hash, sha256_bytes
from origin.utilities.realityweaver.fission import (
    SplitDirective,
    SplitPlan,
    fission,
)


def _make_source_manifest():
    """Build a valid source manifest for testing."""
    files = {
        "audio.rwv1": {"sha256": sha256_bytes(b"audio data"), "size": 10},
        "video.rwv1": {"sha256": sha256_bytes(b"video data"), "size": 10},
        "metadata.json": {"sha256": sha256_bytes(b"metadata"), "size": 8},
    }
    return {
        "schema_version": "0.1.0",
        "manifest_id": "RWMF-0000000000000001",
        "created_at": "2026-02-10T00:00:00Z",
        "weaverpack_id": "RWPK-0000000000000001",
        "authorship": "test",
        "license": "WCL-1.0",
        "disclosure_tier": "internal",
        "sensitivity": {"pii_risk": "none", "contains_personal": False, "redacted": False},
        "timebase": {"epoch": "2026-02-10T00:00:00Z", "resolution_ns": 1000000, "alignment_map_ref": None},
        "files": files,
        "pack_hash": compute_pack_hash(files),
        "invariants_declared": ["RW-C1", "RW-C9", "RW-C10", "RW-C11"],
    }


class TestFissionSuite:
    """F-T1..F-T5: Fission operator tests."""

    def test_f_t1_fission_produces_lineage_map(self):
        """F-T1: Fission output includes valid lineage_map."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["audio_child", "video_child"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="metadata.json", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
            ],
        )
        result = fission(source, plan)
        assert result.passed
        assert result.lineage_map["lineage_map_id"].startswith("RWLM-")
        assert len(result.lineage_map["children"]) == 2
        assert len(result.lineage_map["file_mappings"]) == 3

    def test_f_t2_fission_with_loss_produces_loss_ledger(self):
        """F-T2: Lossy fission declares loss in lineage_map.loss_summary."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["audio_only", "video_only"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
                SplitDirective(source_path="metadata.json", child_index=0, transform="drop"),
            ],
        )
        result = fission(source, plan)
        assert result.passed
        loss = result.lineage_map["loss_summary"]
        assert loss["has_loss"]
        assert "metadata.json" in loss["dropped_files"]
        assert loss["total_bytes_lost"] == 8

    def test_f_t3_silent_split_rejected(self):
        """F-T3: Fission without accounting for all files fails."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["partial", "also_partial"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                # metadata.json and video.rwv1 are NOT accounted for
            ],
        )
        result = fission(source, plan)
        assert not result.passed
        assert any("Silent split" in e for e in result.errors)

    def test_f_t4_all_source_files_accounted(self):
        """F-T4: Every source file appears in a child or loss ledger."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["child_a", "child_b"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
                SplitDirective(source_path="metadata.json", child_index=0),
            ],
        )
        result = fission(source, plan)
        assert result.passed
        loss = result.lineage_map["loss_summary"]
        assert not loss["has_loss"]
        assert loss["dropped_files"] == []

    def test_f_t5_child_manifests_verify(self):
        """F-T5: Each child has valid pack_hash."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["child_a", "child_b"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="metadata.json", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
            ],
        )
        result = fission(source, plan)
        assert result.passed
        for child in result.child_manifests:
            expected = compute_pack_hash(child["files"])
            assert child["pack_hash"] == expected

    def test_fission_requires_min_2_children(self):
        """Fission with fewer than 2 children fails."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["only_child"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
            ],
        )
        result = fission(source, plan)
        assert not result.passed

    def test_fission_integrity_failure(self):
        """Fission with tampered source manifest fails (RW-C1)."""
        source = _make_source_manifest()
        source["pack_hash"] = "0" * 64
        plan = SplitPlan(
            child_labels=["a", "b"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
                SplitDirective(source_path="metadata.json", child_index=0),
            ],
        )
        result = fission(source, plan)
        assert not result.passed
        assert any("integrity" in e.lower() for e in result.errors)

    def test_dt_t1_fission_determinism(self):
        """DT-T1: Same fission inputs produce same lineage map structure."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["a", "b"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
                SplitDirective(source_path="metadata.json", child_index=0),
            ],
        )
        r1 = fission(source, plan)
        r2 = fission(source, plan)
        # Lineage map structure is deterministic (IDs differ due to random generation)
        assert r1.lineage_map["loss_summary"] == r2.lineage_map["loss_summary"]
        assert len(r1.child_manifests) == len(r2.child_manifests)
        for c1, c2 in zip(r1.child_manifests, r2.child_manifests):
            assert c1["pack_hash"] == c2["pack_hash"]

    def test_license_carry_forward(self):
        """LC-T1: Fission carries source license."""
        source = _make_source_manifest()
        plan = SplitPlan(
            child_labels=["a", "b"],
            directives=[
                SplitDirective(source_path="audio.rwv1", child_index=0),
                SplitDirective(source_path="video.rwv1", child_index=1),
                SplitDirective(source_path="metadata.json", child_index=0),
            ],
        )
        result = fission(source, plan)
        assert result.passed
        lc = result.lineage_map["license_carry_forward"]
        assert lc["source_license"] == "WCL-1.0"
        assert lc["attribution_preserved"] is True
        for child_lic in lc["children_licenses"]:
            assert child_lic["license"] == "WCL-1.0"
