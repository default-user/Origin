# RealityWeaver Fission & Fusion Operators Specification

**Version**: 0.1.0
**Attribution**: Ande + Kai (OI) + Whānau (OIs)
**License**: WCL-1.0
**Status**: shadow / sidecar-only

---

## 1. Overview

This document specifies the RWFISSION and RWFUSION operators for RealityWeaver.
These operators allow reality artefacts (WeaverPacks) to split and recombine with
full lineage, explicit plans, and no silent transforms.

### Core Principles

1. **No silent fusion** — every merge requires an explicit merge plan, conflict ledger,
   and receipt (RW-C8).
2. **No irreversible fission** — every split preserves lineage and mapping; if lossy,
   loss is declared and replay-verifiable (RW-C9).
3. **Timebase integrity** — any fission or fusion preserves a canonical timebase with
   explicit alignment maps (RW-C10).
4. **License carry-forward** — attribution and least-permissive license resolution
   unless explicitly relicensed (RW-C11).

---

## 2. RWFISSION Operator

### 2.1 Purpose

Split one WeaverPack or bundle into multiple valid children with lineage,
mapping, and declared loss.

### 2.2 Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_manifest` | ManifestRef | yes | Manifest of the WeaverPack to split |
| `split_plan` | SplitPlan | yes | Declarative plan for how to partition files |
| `child_labels` | string[] | yes | Human-readable labels for each child (min 2) |
| `timebase_policy` | TimebasePolicy | yes | How to handle timebase for children |
| `license_policy` | LicensePolicy | yes | How to handle license for children |
| `bounds` | OperatorBounds | no | Scope and loss bounds |

### 2.3 Outputs

| Output | Schema | Description |
|--------|--------|-------------|
| `lineage_map` | lineage_map_schema_v0 | Complete mapping from source to children |
| `loss_ledger` | (embedded in lineage_map.loss_summary) | Declared loss, if any |
| `child_manifests` | manifest_schema_v0[] | One manifest per child WeaverPack |
| `receipt` | receipt_schema_v0 | Operation receipt |

### 2.4 Algorithm

```
RWFISSION(source, split_plan, labels, timebase_policy, license_policy):
  1. VERIFY source manifest integrity (RW-C1)
     - FAIL_CLOSED if manifest hash mismatch
  2. VALIDATE split_plan covers all source files
     - Each source file must appear in at least one child OR be declared in loss_ledger
  3. CREATE child manifests
     For each child in split_plan.partitions:
       a. Collect files assigned to this child
       b. Apply transforms (copy, slice, filter, redact)
       c. Compute file hashes
       d. Build manifest with:
          - parent_manifest_id = source.manifest_id
          - lineage entry referencing this fission
          - license from license_policy (carry-forward or explicit)
          - timebase from timebase_policy
  4. BUILD lineage_map
     - Map every source file to its destination(s)
     - Mark lossy transforms
     - Compute loss_summary
  5. VERIFY children
     For each child manifest:
       - Verify pack_hash matches file entries
       - Verify timebase is valid (RW-C10)
       - Verify license is carried forward (RW-C11)
  6. EMIT receipt
     - Record all invariants checked: RW-C1, RW-C9, RW-C10, RW-C11
     - Record gate results
  7. RETURN (lineage_map, child_manifests, receipt)
```

### 2.5 Forbids

- **Silent split**: every file mapping must be explicit in the lineage map.
- **Dropping attribution or license**: license carry-forward is mandatory.
- **Timebase breakage**: children must have valid timebase alignment maps.

### 2.6 Fail-Closed Conditions

- Source manifest fails integrity check
- Split plan references files not in source
- Child manifest fails verification
- Timebase alignment is inconsistent
- License cannot be resolved

---

## 3. RWFUSION Operator

### 3.1 Purpose

Merge multiple WeaverPacks or bundles into one coherent artefact with explicit
resolution and conflicts preserved.

### 3.2 Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_manifests` | ManifestRef[] | yes | Manifests of WeaverPacks to merge (min 2) |
| `merge_plan` | merge_plan_schema_v0 | yes | Explicit merge plan with resolution directives |
| `bounds` | OperatorBounds | no | Scope and loss bounds |

### 3.3 Outputs

| Output | Schema | Description |
|--------|--------|-------------|
| `merge_plan` | merge_plan_schema_v0 | The merge plan used (echoed back) |
| `conflict_ledger` | conflict_ledger_schema_v0 | All conflicts and their resolutions |
| `target_manifest` | manifest_schema_v0 | Manifest of the fused WeaverPack |
| `receipt` | receipt_schema_v0 | Operation receipt |

### 3.4 Algorithm

```
RWFUSION(sources, merge_plan):
  1. VERIFY all source manifests (RW-C1)
     - FAIL_CLOSED if any manifest hash mismatch
  2. VALIDATE merge_plan
     - All source manifests referenced
     - Strategy is explicit
     - License resolution method is declared
     - Timebase alignment is specified
  3. DETECT conflicts
     For each file across all sources:
       a. If file exists in multiple sources with different hashes:
          - Record conflict in conflict_ledger
          - Apply resolution from merge_plan.file_resolutions
       b. If file exists in only one source:
          - Include in target (no conflict)
  4. RESOLVE conflicts per merge_plan
     For each conflict:
       a. Apply resolution directive
       b. Record resolution in conflict_ledger
       c. FAIL_CLOSED if resolution is "unresolved" and all_must_resolve=true
  5. BUILD target manifest
     - Collect resolved files
     - Compute file hashes
     - Build manifest with:
       - lineage entries from all sources
       - license from merge_plan.license_resolution
       - timebase from merge_plan.timebase_alignment
  6. VERIFY target
     - Verify pack_hash
     - Verify all conflicts resolved (if required)
     - Verify timebase integrity (RW-C10)
     - Verify license resolution (RW-C11)
  7. EMIT receipt
     - Record invariants checked: RW-C1, RW-C8, RW-C10, RW-C11
     - Reference conflict_ledger
     - Reference merge_plan
  8. RETURN (conflict_ledger, target_manifest, receipt)
```

### 3.5 Forbids

- **Silent merge**: every merge requires an explicit merge plan.
- **Conflict smoothing**: conflicts are never silently resolved; each is recorded
  in the conflict ledger.
- **License escalation without authority**: cannot upgrade to a more permissive
  license without explicit relicense authority.

### 3.6 Fail-Closed Conditions

- Any source manifest fails integrity check
- Merge plan is missing or invalid
- Unresolved conflict when all_must_resolve=true
- License escalation attempted without authority
- Timebase alignment is inconsistent

---

## 4. Shared Invariants

Both operators enforce:

| ID | Invariant | Enforcement |
|----|-----------|-------------|
| RW-C1 | Manifest Integrity | Verify all input manifests before operating |
| RW-C8 | No Silent Fusion | Fusion requires merge plan + conflict ledger |
| RW-C9 | No Irreversible Fission | Fission preserves lineage; loss declared |
| RW-C10 | Timebase Integrity | Canonical timebase with alignment maps |
| RW-C11 | License Carry-Forward | Least-permissive unless explicitly relicensed |
| AIRLOCK | CIF/CDI Airlock | No capture/stream/disclose/commit/egress bypass |

---

## 5. Convergence Units

These operators activate through governed convergence (PH3):

| CU | Fission | Fusion |
|----|---------|--------|
| CU1 (verify only) | Read-only lineage inspection | Read-only merge plan validation |
| CU2 (seal/commit) | Fission with lineage map + commitment | Fusion with merge plan + conflict ledger + commitment |
| CU3 (disclose) | Disclose fission lineage with proofs | Disclose fusion result with proofs |

---

## 6. Receipt Requirements

Every invocation of RWFISSION or RWFUSION MUST emit a receipt conforming to
`receipt_schema_v0.json` with:

- `operation`: "fission" or "fusion"
- `inputs`: source manifest IDs
- `outputs`: child/target manifest IDs + lineage_map_ref or conflict_ledger_ref
- `gates`: all gate checks performed
- `invariants_checked`: at minimum RW-C1, RW-C8/C9, RW-C10, RW-C11, AIRLOCK

---

## 7. Determinism

Both operators are deterministic:

- Same inputs + same plan = same outputs
- No RNG in resolution
- Stable file ordering (sorted by path)
- Deterministic hash computation
- Canonical JSON serialisation for all artefacts

---

## 8. Sidecar Constraints

While in sidecar (PH2), these operators:

- Cannot activate capture or egress
- Cannot auto-wire into Origin runtime
- Cannot auto-publish commitments
- Cannot allow silent merge or split
- Operate only within `origin/utilities/realityweaver/**`
