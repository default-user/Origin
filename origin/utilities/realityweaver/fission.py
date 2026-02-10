"""
RW-9: Fission operator with lineage map.

Split one WeaverPack into multiple valid children with lineage,
mapping, and declared loss. No silent split (RW-C9).
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field

from .primitives import compute_pack_hash, generate_id, now_iso, sha256_bytes


@dataclass
class SplitDirective:
    """Directive for how to assign a source file to a child."""

    source_path: str
    child_index: int
    dest_path: str | None = None  # defaults to source_path
    transform: str = "copy"  # copy | slice | filter | redact | drop
    slice_offset: int | None = None
    slice_length: int | None = None
    lossy: bool = False


@dataclass
class SplitPlan:
    """Plan for splitting a WeaverPack into children."""

    child_labels: list[str]
    directives: list[SplitDirective]
    timebase_policy: str = "inherit"  # inherit | realign
    license_policy: str = "carry_forward"  # carry_forward | explicit


@dataclass
class FissionResult:
    """Result of a fission operation."""

    lineage_map: dict
    child_manifests: list[dict]
    receipt: dict | None = None
    errors: list[str] = field(default_factory=list)
    passed: bool = False


def _build_child_manifest(
    source_manifest: dict,
    child_label: str,
    child_files: dict[str, dict],
    child_index: int,
    lineage_map_id: str,
) -> dict:
    """Build a child manifest from assigned files."""
    child_manifest_id = generate_id("RWMF")
    child_weaverpack_id = generate_id("RWPK")
    child_pack_hash = compute_pack_hash(child_files)

    # Inherit timebase from source
    timebase = copy.deepcopy(source_manifest.get("timebase", {
        "epoch": now_iso(),
        "resolution_ns": 1000000,
        "alignment_map_ref": None,
    }))

    return {
        "schema_version": "0.1.0",
        "manifest_id": child_manifest_id,
        "created_at": now_iso(),
        "weaverpack_id": child_weaverpack_id,
        "parent_manifest_id": source_manifest["manifest_id"],
        "lineage": [
            {
                "operation": "fission",
                "source_manifest_id": source_manifest["manifest_id"],
                "timestamp": now_iso(),
                "receipt_ref": None,
            }
        ],
        "authorship": source_manifest.get("authorship", ""),
        "license": source_manifest.get("license", "WCL-1.0"),
        "disclosure_tier": source_manifest.get("disclosure_tier", "internal"),
        "sensitivity": copy.deepcopy(source_manifest.get("sensitivity", {
            "pii_risk": "none", "contains_personal": False, "redacted": False,
        })),
        "timebase": timebase,
        "files": child_files,
        "pack_hash": child_pack_hash,
        "invariants_declared": source_manifest.get("invariants_declared", []),
    }


def fission(
    source_manifest: dict,
    split_plan: SplitPlan,
    file_contents: dict[str, bytes] | None = None,
) -> FissionResult:
    """
    Execute RWFISSION: split one WeaverPack into multiple children (RW-C9).

    1. Verify source manifest integrity (RW-C1)
    2. Validate split plan covers all source files
    3. Create child manifests
    4. Build lineage map
    5. Compute loss summary
    6. Emit receipt

    Fail-closed on: silent split, missing files, integrity failure.
    """
    result = FissionResult(lineage_map={}, child_manifests=[])

    # Validate inputs
    if len(split_plan.child_labels) < 2:
        result.errors.append("Fission requires at least 2 children.")
        return result

    source_files = source_manifest.get("files", {})

    # Verify source pack_hash (RW-C1)
    expected_hash = compute_pack_hash(source_files)
    if expected_hash != source_manifest.get("pack_hash"):
        result.errors.append(
            f"Source manifest integrity failure (RW-C1): "
            f"expected {expected_hash}, got {source_manifest.get('pack_hash')}"
        )
        return result

    # Check that all source files are accounted for
    assigned_paths = set()
    dropped_paths = set()
    for directive in split_plan.directives:
        if directive.transform == "drop":
            dropped_paths.add(directive.source_path)
        else:
            assigned_paths.add(directive.source_path)

    unaccounted = set(source_files.keys()) - assigned_paths - dropped_paths
    if unaccounted:
        result.errors.append(
            f"Silent split detected (RW-C9 violation): files not accounted for: {sorted(unaccounted)}"
        )
        return result

    # Build child file sets
    num_children = len(split_plan.child_labels)
    child_file_sets: list[dict[str, dict]] = [{} for _ in range(num_children)]

    for directive in split_plan.directives:
        if directive.transform == "drop":
            continue
        if directive.child_index < 0 or directive.child_index >= num_children:
            result.errors.append(
                f"Invalid child_index {directive.child_index} for {directive.source_path}"
            )
            return result
        if directive.source_path not in source_files:
            result.errors.append(f"Source path not in manifest: {directive.source_path}")
            return result

        dest_path = directive.dest_path or directive.source_path
        source_entry = source_files[directive.source_path]

        if directive.transform == "copy":
            child_file_sets[directive.child_index][dest_path] = copy.deepcopy(source_entry)
        elif directive.transform == "slice" and file_contents:
            content = file_contents.get(directive.source_path, b"")
            offset = directive.slice_offset or 0
            length = directive.slice_length or (len(content) - offset)
            sliced = content[offset:offset + length]
            child_file_sets[directive.child_index][dest_path] = {
                "sha256": sha256_bytes(sliced),
                "size": len(sliced),
            }
        else:
            # For other transforms without file_contents, copy metadata
            child_file_sets[directive.child_index][dest_path] = copy.deepcopy(source_entry)

    # Build child manifests
    lineage_map_id = generate_id("RWLM")
    for i, label in enumerate(split_plan.child_labels):
        child_manifest = _build_child_manifest(
            source_manifest, label, child_file_sets[i], i, lineage_map_id,
        )
        result.child_manifests.append(child_manifest)

    # Build lineage map
    file_mappings = []
    for directive in split_plan.directives:
        destinations = []
        if directive.transform != "drop":
            child_mf = result.child_manifests[directive.child_index]
            destinations.append({
                "child_manifest_id": child_mf["manifest_id"],
                "dest_path": directive.dest_path or directive.source_path,
                "transform": directive.transform,
                "slice_range": (
                    {"offset_bytes": directive.slice_offset or 0,
                     "length_bytes": directive.slice_length or 0}
                    if directive.transform == "slice" else None
                ),
                "lossy": directive.lossy,
            })
        file_mappings.append({
            "source_path": directive.source_path,
            "destinations": destinations,
        })

    # Compute loss summary
    dropped_files_list = sorted(dropped_paths)
    truncated_files = [
        d.source_path for d in split_plan.directives
        if d.transform in ("slice", "filter") and d.lossy
    ]
    total_bytes_lost = sum(
        source_files.get(p, {}).get("size", 0) for p in dropped_files_list
    )
    has_loss = bool(dropped_files_list or truncated_files)

    # Build timebase mappings
    timebase_mappings = []
    for child_mf in result.child_manifests:
        tb = child_mf.get("timebase", {})
        timebase_mappings.append({
            "child_manifest_id": child_mf["manifest_id"],
            "epoch": tb.get("epoch", now_iso()),
            "resolution_ns": tb.get("resolution_ns", 1000000),
            "offset_from_source_ns": 0,
        })

    result.lineage_map = {
        "schema_version": "0.1.0",
        "lineage_map_id": lineage_map_id,
        "created_at": now_iso(),
        "source_manifest": {
            "manifest_id": source_manifest["manifest_id"],
            "weaverpack_id": source_manifest["weaverpack_id"],
            "pack_hash": source_manifest["pack_hash"],
        },
        "children": [
            {
                "manifest_id": cm["manifest_id"],
                "weaverpack_id": cm["weaverpack_id"],
                "label": split_plan.child_labels[i],
            }
            for i, cm in enumerate(result.child_manifests)
        ],
        "file_mappings": file_mappings,
        "timebase_mappings": timebase_mappings,
        "loss_summary": {
            "has_loss": has_loss,
            "dropped_files": dropped_files_list,
            "truncated_files": truncated_files,
            "total_bytes_lost": total_bytes_lost,
        },
        "license_carry_forward": {
            "source_license": source_manifest.get("license", "WCL-1.0"),
            "children_licenses": [
                {
                    "child_manifest_id": cm["manifest_id"],
                    "license": cm["license"],
                }
                for cm in result.child_manifests
            ],
            "attribution_preserved": True,
        },
    }

    result.passed = True
    return result
