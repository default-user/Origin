"""
RW-10: Fusion operator with merge plan and conflict ledger.

Merge multiple WeaverPacks into one coherent artefact with explicit
resolution and conflicts preserved. No silent merge (RW-C8).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field

from .primitives import compute_pack_hash, generate_id, now_iso


@dataclass
class FusionResult:
    """Result of a fusion operation."""

    target_manifest: dict | None = None
    conflict_ledger: dict | None = None
    receipt: dict | None = None
    errors: list[str] = field(default_factory=list)
    passed: bool = False


def _detect_conflicts(
    source_manifests: list[dict],
    merge_plan: dict,
) -> list[dict]:
    """Detect conflicts across source manifests."""
    conflicts = []
    conflict_counter = 0

    # Collect all files from all sources
    all_paths: dict[str, list[tuple[str, dict]]] = {}
    for mf in source_manifests:
        mf_id = mf["manifest_id"]
        for path, entry in mf.get("files", {}).items():
            if path not in all_paths:
                all_paths[path] = []
            all_paths[path].append((mf_id, entry))

    # Find conflicts: same path, different hashes
    for path, sources in all_paths.items():
        if len(sources) < 2:
            continue
        hashes = set(entry["sha256"] for _, entry in sources)
        if len(hashes) > 1:
            conflict_counter += 1
            conflict = {
                "conflict_id": f"RWCF-{conflict_counter:04d}",
                "path": path,
                "conflict_type": "content_divergence",
                "sources": [
                    {
                        "manifest_id": mf_id,
                        "sha256": entry["sha256"],
                        "size": entry.get("size"),
                    }
                    for mf_id, entry in sources
                ],
                "resolution": "unresolved",
                "resolved": False,
                "resolution_detail": "",
                "resulting_sha256": None,
            }
            conflicts.append(conflict)

    return conflicts


def _resolve_conflicts(
    conflicts: list[dict],
    merge_plan: dict,
    source_manifests: list[dict],
) -> list[dict]:
    """Apply resolution directives from merge plan to conflicts."""
    # Build a resolution map from the merge plan
    resolution_map: dict[str, dict] = {}
    for res in merge_plan.get("file_resolutions", []):
        resolution_map[res["path"]] = res

    primary_id = None
    secondary_id = None
    for src in merge_plan.get("source_manifests", []):
        if src.get("role") == "primary":
            primary_id = src["manifest_id"]
        elif src.get("role") == "secondary":
            secondary_id = src["manifest_id"]

    # Build manifest lookup
    mf_lookup = {mf["manifest_id"]: mf for mf in source_manifests}

    for conflict in conflicts:
        path = conflict["path"]
        if path in resolution_map:
            directive = resolution_map[path]
            resolution = directive.get("resolution", "unresolved")
            conflict["resolution"] = resolution
            conflict["resolution_detail"] = directive.get("note", "")

            if resolution == "take_primary" and primary_id:
                # Find the primary source's entry
                for src in conflict["sources"]:
                    if src["manifest_id"] == primary_id:
                        conflict["resulting_sha256"] = src["sha256"]
                        conflict["resolved"] = True
                        break
            elif resolution == "take_secondary" and secondary_id:
                for src in conflict["sources"]:
                    if src["manifest_id"] == secondary_id:
                        conflict["resulting_sha256"] = src["sha256"]
                        conflict["resolved"] = True
                        break
            elif resolution == "skip":
                conflict["resolved"] = True
                conflict["resulting_sha256"] = None
            else:
                conflict["resolved"] = resolution != "unresolved"

    return conflicts


def _build_target_files(
    source_manifests: list[dict],
    conflicts: list[dict],
    merge_plan: dict,
) -> dict[str, dict]:
    """Build the target file set from sources and resolved conflicts."""
    target_files: dict[str, dict] = {}
    conflict_paths = {c["path"] for c in conflicts}

    # Determine primary source
    primary_id = None
    for src in merge_plan.get("source_manifests", []):
        if src.get("role") == "primary":
            primary_id = src["manifest_id"]

    # Add non-conflicting files from all sources
    for mf in source_manifests:
        for path, entry in mf.get("files", {}).items():
            if path not in conflict_paths and path not in target_files:
                target_files[path] = copy.deepcopy(entry)

    # Add resolved conflict files
    for conflict in conflicts:
        if conflict["resolved"] and conflict["resulting_sha256"]:
            path = conflict["path"]
            # Find the matching source entry
            for src in conflict["sources"]:
                if src["sha256"] == conflict["resulting_sha256"]:
                    target_files[path] = {
                        "sha256": src["sha256"],
                        "size": src.get("size", 0),
                    }
                    break

    return target_files


def validate_merge_plan(merge_plan: dict) -> list[str]:
    """
    Validate a merge plan. Returns list of errors.

    Enforces: merge plan must exist and be explicit (RW-C8).
    """
    errors = []
    if not merge_plan:
        errors.append("Merge plan is required (RW-C8: no silent fusion).")
        return errors
    for req in ("merge_plan_id", "source_manifests", "target_weaverpack_id",
                "strategy", "file_resolutions", "timebase_alignment", "license_resolution"):
        if req not in merge_plan:
            errors.append(f"Merge plan missing required field: {req}")
    sources = merge_plan.get("source_manifests", [])
    if len(sources) < 2:
        errors.append("Merge plan must reference at least 2 source manifests.")
    return errors


def fusion(
    source_manifests: list[dict],
    merge_plan: dict,
) -> FusionResult:
    """
    Execute RWFUSION: merge multiple WeaverPacks into one (RW-C8).

    1. Verify all source manifests (RW-C1)
    2. Validate merge plan (RW-C8)
    3. Detect conflicts
    4. Resolve conflicts per merge plan
    5. Build target manifest
    6. Emit conflict ledger and receipt

    Fail-closed on: silent merge, invalid plan, integrity failure.
    """
    result = FusionResult()

    # Validate merge plan (RW-C8)
    plan_errors = validate_merge_plan(merge_plan)
    if plan_errors:
        result.errors.extend(plan_errors)
        return result

    # Verify source manifests (RW-C1)
    for mf in source_manifests:
        expected = compute_pack_hash(mf.get("files", {}))
        if expected != mf.get("pack_hash"):
            result.errors.append(
                f"Source manifest {mf.get('manifest_id', '?')} integrity failure (RW-C1): "
                f"expected {expected}, got {mf.get('pack_hash')}"
            )
    if result.errors:
        return result

    # Detect conflicts
    conflicts = _detect_conflicts(source_manifests, merge_plan)

    # Resolve conflicts
    conflicts = _resolve_conflicts(conflicts, merge_plan, source_manifests)

    # Check for unresolved conflicts
    unresolved = [c for c in conflicts if not c["resolved"]]
    resolved = [c for c in conflicts if c["resolved"]]

    # Build conflict ledger (RW-C8: always emitted)
    ledger_id = generate_id("RWCL")
    result.conflict_ledger = {
        "schema_version": "0.1.0",
        "ledger_id": ledger_id,
        "created_at": now_iso(),
        "merge_plan_id": merge_plan["merge_plan_id"],
        "source_manifests": [mf["manifest_id"] for mf in source_manifests],
        "conflicts": conflicts,
        "summary": {
            "total_conflicts": len(conflicts),
            "resolved_count": len(resolved),
            "unresolved_count": len(unresolved),
            "all_resolved": len(unresolved) == 0,
        },
    }

    # Build target files
    target_files = _build_target_files(source_manifests, conflicts, merge_plan)
    target_pack_hash = compute_pack_hash(target_files)

    # License resolution (RW-C11)
    license_res = merge_plan.get("license_resolution", {})
    resolved_license = license_res.get("resolved_license", "WCL-1.0")

    # Timebase (RW-C10)
    tb_alignment = merge_plan.get("timebase_alignment", {})

    # Build lineage entries from all sources
    lineage = []
    for mf in source_manifests:
        lineage.append({
            "operation": "fusion",
            "source_manifest_id": mf["manifest_id"],
            "timestamp": now_iso(),
            "receipt_ref": None,
        })

    target_manifest_id = generate_id("RWMF")
    result.target_manifest = {
        "schema_version": "0.1.0",
        "manifest_id": target_manifest_id,
        "created_at": now_iso(),
        "weaverpack_id": merge_plan["target_weaverpack_id"],
        "parent_manifest_id": None,
        "lineage": lineage,
        "authorship": source_manifests[0].get("authorship", ""),
        "license": resolved_license,
        "disclosure_tier": source_manifests[0].get("disclosure_tier", "internal"),
        "sensitivity": copy.deepcopy(source_manifests[0].get("sensitivity", {
            "pii_risk": "none", "contains_personal": False, "redacted": False,
        })),
        "timebase": {
            "epoch": tb_alignment.get("canonical_epoch", now_iso()),
            "resolution_ns": tb_alignment.get("resolution_ns", 1000000),
            "alignment_map_ref": None,
        },
        "files": target_files,
        "pack_hash": target_pack_hash,
        "invariants_declared": source_manifests[0].get("invariants_declared", []),
    }

    result.passed = len(unresolved) == 0
    return result
