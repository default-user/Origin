# RealityWeaver Conformance Catalogue

**Version**: 0.1.0
**Status**: shadow / PH1 declaration
**License**: WCL-1.0

---

## 1. Purpose

This catalogue enumerates all conformance suites and test requirements for the
RealityWeaver organ. Every invariant (RW-C1 through RW-C11 and AIRLOCK) must
have corresponding conformance tests before activation.

---

## 2. Invariant Conformance Matrix

| ID | Invariant | Suite | Test Count | Status |
|----|-----------|-------|------------|--------|
| RW-C1 | Manifest Integrity | rw_c_suite | 4 | declared |
| RW-C2 | Consent Logging | rw_c_suite | 3 | declared |
| RW-C3 | Default Off | rw_c_suite | 3 | declared |
| RW-C4 | Redaction Lineage | rw_c_suite | 3 | declared |
| RW-C5 | Selective Disclosure | rw_c_suite | 3 | declared |
| RW-C6 | Metadata Hygiene | rw_c_suite | 3 | declared |
| RW-C7 | Replay Verifiable | rw_c_suite | 3 | declared |
| RW-C8 | No Silent Fusion | rw_fusion_suite | 5 | declared |
| RW-C9 | No Irreversible Fission | rw_fission_suite | 5 | declared |
| RW-C10 | Timebase Integrity | timebase_integrity_suite | 4 | declared |
| RW-C11 | License Carry-Forward | license_carry_forward_suite | 4 | declared |
| AIRLOCK | CIF/CDI Airlock | airlock_contract_suite | 5 | declared |

---

## 3. Conformance Suites

### 3.1 rw_c_suite — Core Invariants

Tests for RW-C1 through RW-C7.

#### RW-C1: Manifest Integrity

| Test | Description | Falsification |
|------|-------------|---------------|
| C1-T1 | Valid manifest verifies against schema | Manifest with all required fields passes validation |
| C1-T2 | Manifest with wrong pack_hash fails verification | Tampered pack_hash detected and rejected |
| C1-T3 | Manifest with missing file entry fails | File listed in manifest but not present is detected |
| C1-T4 | Manifest with extra unlisted file fails | File present but not in manifest is detected |

#### RW-C2: Consent Logging

| Test | Description | Falsification |
|------|-------------|---------------|
| C2-T1 | Capture without consent ritual fails | Attempting capture without consent emits fail receipt |
| C2-T2 | Consent ritual is logged in receipt | Consent event appears in receipt gates |
| C2-T3 | Retention scope is enforced | Data beyond retention scope is rejected |

#### RW-C3: Default Off

| Test | Description | Falsification |
|------|-------------|---------------|
| C3-T1 | Fresh policy has capture=false | Default policy creation yields capture off |
| C3-T2 | Fresh policy has stream=false | Default policy creation yields stream off |
| C3-T3 | Enabling capture requires governed command | Capture enable without governance token fails |

#### RW-C4: Redaction Lineage

| Test | Description | Falsification |
|------|-------------|---------------|
| C4-T1 | Redaction preserves original lineage | Redacted manifest has lineage entry pointing to pre-redaction |
| C4-T2 | Redaction is non-destructive | Original data remains accessible via lineage |
| C4-T3 | Redaction without lineage entry fails | Attempting redaction without recording lineage is rejected |

#### RW-C5: Selective Disclosure

| Test | Description | Falsification |
|------|-------------|---------------|
| C5-T1 | Disclosure without inclusion proof fails | Attempting disclosure without proof is rejected |
| C5-T2 | Disclosure without auth decrypt fails | Attempting disclosure without authorization is rejected |
| C5-T3 | Valid disclosure includes both proof and auth | Successful disclosure receipt shows both gates pass |

#### RW-C6: Metadata Hygiene

| Test | Description | Falsification |
|------|-------------|---------------|
| C6-T1 | Cross-tier metadata leak detected | Restricted metadata appearing in public tier is flagged |
| C6-T2 | Redaction patterns applied to metadata | Configured patterns are stripped from metadata |
| C6-T3 | Receipt does not leak sensitive metadata | Receipt output is clean of sensitive patterns |

#### RW-C7: Replay Verifiable

| Test | Description | Falsification |
|------|-------------|---------------|
| C7-T1 | Operation replay matches receipt | Replaying operation produces matching receipt hash |
| C7-T2 | Tampered replay detected | Modified replay input produces different receipt |
| C7-T3 | Receipt chain is verifiable | Sequence of receipts forms verifiable chain |

### 3.2 rw_fission_suite — Fission Operator

Tests for RW-C9 (No Irreversible Fission) and RWFISSION operator.

| Test | Description | Falsification |
|------|-------------|---------------|
| F-T1 | Fission produces lineage map | Fission output includes valid lineage_map |
| F-T2 | Fission with loss produces loss ledger | Lossy fission declares loss in lineage_map.loss_summary |
| F-T3 | Silent split is rejected | Fission without explicit split plan fails |
| F-T4 | All source files are accounted for | File not in any child and not in loss_ledger is detected |
| F-T5 | Child manifests verify independently | Each child has valid pack_hash and passes RW-C1 |

### 3.3 rw_fusion_suite — Fusion Operator

Tests for RW-C8 (No Silent Fusion) and RWFUSION operator.

| Test | Description | Falsification |
|------|-------------|---------------|
| M-T1 | Fusion requires merge plan | Fusion without merge_plan fails |
| M-T2 | Fusion emits conflict ledger | Fusion output includes valid conflict_ledger |
| M-T3 | Silent merge is rejected | Fusion without explicit merge plan fails |
| M-T4 | Conflict smoothing is rejected | Unresolved conflict with smoothing attempted is detected |
| M-T5 | Target manifest verifies | Fused WeaverPack has valid pack_hash and passes RW-C1 |

### 3.4 timebase_integrity_suite

Tests for RW-C10 (Timebase Integrity).

| Test | Description | Falsification |
|------|-------------|---------------|
| TB-T1 | Fission preserves canonical timebase | Children have alignment maps to source epoch |
| TB-T2 | Fusion aligns timebases | Merged result has consistent canonical epoch |
| TB-T3 | Timebase gap detected in fusion | Sources with non-overlapping timebases flagged |
| TB-T4 | Resolution mismatch handled | Sources with different resolution_ns are aligned |

### 3.5 license_carry_forward_suite

Tests for RW-C11 (License Carry-Forward).

| Test | Description | Falsification |
|------|-------------|---------------|
| LC-T1 | Fission carries source license | Children inherit source license |
| LC-T2 | Fusion resolves to least permissive | Merged license is most restrictive of sources |
| LC-T3 | License escalation without authority fails | Attempting more permissive license without authority is rejected |
| LC-T4 | Attribution preserved in all cases | Attribution line is never dropped |

### 3.6 airlock_contract_suite

Tests for AIRLOCK (CIF/CDI Airlock).

| Test | Description | Falsification |
|------|-------------|---------------|
| AL-T1 | Capture bypassing CIF fails | Direct capture without CIF_IN is rejected |
| AL-T2 | Stream bypassing CIF fails | Direct stream without CIF_IN is rejected |
| AL-T3 | Disclose bypassing CDI fails | Disclosure without CDI_POST is rejected |
| AL-T4 | Commit bypassing CDI fails | Commit without CDI_POST is rejected |
| AL-T5 | Egress bypassing CIF_OUT fails | Output without CIF_OUT is rejected |

### 3.7 receipt_schema_suite

Tests for receipt validity.

| Test | Description | Falsification |
|------|-------------|---------------|
| RS-T1 | Receipt conforms to schema | Generated receipt validates against receipt_schema_v0 |
| RS-T2 | Receipt has all required fields | Missing field causes validation failure |
| RS-T3 | Receipt gates are populated | Empty gates array on a non-trivial operation is flagged |

### 3.8 determinism_suite

Tests for deterministic behaviour.

| Test | Description | Falsification |
|------|-------------|---------------|
| DT-T1 | Same fission inputs produce same outputs | Two runs produce identical lineage maps |
| DT-T2 | Same fusion inputs produce same outputs | Two runs produce identical conflict ledgers |
| DT-T3 | Hash computation is deterministic | Same file set produces same pack_hash |

### 3.9 fuzz_suite_bitstreams

Fuzz testing for format robustness.

| Test | Description | Falsification |
|------|-------------|---------------|
| FZ-T1 | Random bitstream as manifest fails cleanly | Garbage input rejected with clear error |
| FZ-T2 | Truncated manifest fails cleanly | Partial manifest rejected without crash |
| FZ-T3 | Oversized manifest fails cleanly | Manifest exceeding limits rejected |

### 3.10 resource_caps_suite

Tests for resource bounds.

| Test | Description | Falsification |
|------|-------------|---------------|
| RC-T1 | Fission with too many children rejected | Exceeding child count limit fails |
| RC-T2 | Fusion with too many sources rejected | Exceeding source count limit fails |
| RC-T3 | Oversized WeaverPack handled | Pack exceeding size cap is rejected gracefully |

---

## 4. Coverage Requirements

- All invariants RW-C1 through RW-C11 and AIRLOCK must have at least one test each.
- RWFISSION must have tests for: lineage_map emission, loss_ledger emission (if lossy),
  silent split rejection, file accounting, and child verification.
- RWFUSION must have tests for: merge_plan requirement, conflict_ledger emission,
  silent merge rejection, conflict smoothing rejection, and target verification.
- All tests must be runnable without network access or external dependencies.
- All tests must be deterministic and repeatable.

---

## 5. Suite Execution Order

1. `determinism_suite` — foundational: if hashing is non-deterministic, nothing else works
2. `rw_c_suite` — core invariants
3. `rw_fission_suite` — fission operator
4. `rw_fusion_suite` — fusion operator
5. `timebase_integrity_suite` — timebase
6. `license_carry_forward_suite` — license
7. `airlock_contract_suite` — airlock
8. `receipt_schema_suite` — receipts
9. `fuzz_suite_bitstreams` — robustness
10. `resource_caps_suite` — bounds
