# ORIGIN Nth-Level Refinement Report

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

**Date**: 2026-02-03
**Branch**: `claude/origin-nth-level-refinement-KG3hX`

---

## Executive Summary

This report documents the Nth-Level Refinement Push for the ORIGIN repository. All HIGH and MED priority bubbles have been resolved. The repository now has:

- **23/23 packs validated** against schema
- **4/4 golden tests passing**
- **GNSL Monolith compiles and runs** with conformance suite
- **12 bubbles resolved** out of 25 identified
- **13 remaining bubbles** are LOW priority rationalized unknowns

---

## 1. What Changed

### 1.1 Java GNSL Monolith Fixes (B001)

**File**: `kits/java/Main.java`

- Renamed instance method `canonicalJson()` to `toCanonicalJson()` to resolve name collision
- Updated all call sites to use new method name
- Fixed Denotum `renderCanonical()` to include terminal period for MRT fidelity

**Result**: Monolith compiles and runs. Conformance suite passes.

### 1.2 Schema and Pack Validation Fixes (B002-B007, B023)

**Files**: `schema/pack.schema.json`, multiple pack.yaml files

- Extended provenance type enum to include: `rationalization`, `capsule_ingestion`, `origin_integration`
- Fixed C0006 YAML syntax (quoted `[[REDACTED]]`)
- Fixed C0022 artifacts format (object → string)
- Reformatted C0023 to conform to pack.schema.json

**Result**: All 23 packs validate successfully.

### 1.3 Query Token Coverage Fix (B008)

**File**: `tools/query.ts`

- Added token coverage threshold (50%) for search matches
- Prevents false positives from single-token partial matches
- Unknown terms now correctly return UNKNOWN

**Result**: All 4 golden tests pass.

### 1.4 Consistency Updates (B009)

**File**: `README.md`

- Updated pack count from 20 to 23
- Added C0021, C0022, C0023 to pack table

### 1.5 New Documentation (B010, B025)

**New Files**:
- `docs/16_bubble_ledger.md` — Exhaustive bubble tracking
- `docs/17_deterministic_build_spec.md` — Build commands and reproducibility
- `docs/18_conformance_suite_guide.md` — Test categories and running guide

**Updated Files**:
- `docs/02_corpus_map.md` — Added C0022, C0023, Integration cluster
- `docs/15_roundtree_architecture.md` — Added Level 6 conformance test section

---

## 2. Bubble Ledger Snapshot

### 2.1 By Status

| Status | Count |
|--------|-------|
| RESOLVED | 12 |
| OPEN (LOW) | 13 |
| **TOTAL** | 25 |

### 2.2 By Type

| Type | Total | Resolved | Remaining |
|------|-------|----------|-----------|
| SCHEMA_GAP | 7 | 7 | 0 |
| DOC_GAP | 13 | 2 | 11 |
| TEST_GAP | 1 | 1 | 0 |
| CONSISTENCY_GAP | 1 | 1 | 0 |
| BUILD_GAP | 1 | 1 | 0 |
| INDEX_GAP | 1 | 0 | 1 |
| SPEC_GAP | 1 | 1 | 0 |

### 2.3 Remaining Bubbles (All LOW Priority)

All remaining bubbles are **rationalized unknowns** — information not present in the original corpus that cannot be fabricated. They do not block determinism, safety, or runtime operation.

| ID | Description |
|----|-------------|
| B011-B016 | [UNKNOWN: NOT IN CORPUS] markers in various docs |
| B017-B021 | [UNKNOWN] markers in pack content.mdx files |
| B022 | Trailing marker in docs/01_origin_overview.md |
| B024 | knowledge/dist/ legacy index documentation |

---

## 3. How to Run

### 3.1 Prerequisites

```bash
cd origin
npm install
```

### 3.2 Deterministic Build

```bash
# Full validation + build + test
npm run validate && npm run build && npm run test

# Expected output:
# Valid: 23/23
# Passed: 4/4
```

### 3.3 GNSL Monolith Demo

```bash
cd kits/java
javac Main.java
java Main

# Expected output:
# ORIGIN Roundtree - Governed Neuro-Symbolic Loop
# ...
# === VERIFY RECEIPTS (TAIL) ===
# ok=true
```

### 3.4 Conformance Suite

The GNSL monolith runs conformance tests automatically on startup:

- Empty input denial (CDI_PRE)
- Anti-phishing denial (CDI_PRE)
- Valid request processing (full pipeline)
- Receipt tail verification

Any failure throws `AssertionError`.

---

## 4. Build Outputs

After successful build:

```
build/
├── index.json        # 307 entities, 369 edges, 517 facts
├── graph.json        # 307 nodes, 369 edges
├── search.json       # 1058 tokens indexed
└── reports/
    └── validate.json # 23/23 valid
```

### 4.1 Seal Handles (QED-Ready)

| Handle | Value |
|--------|-------|
| validate_hash | `35f2fd1f8586eff9` |
| index_hash | `31ba56bd353fe73e` |
| graph_hash | `a9be7b2cc54422c0` |
| search_hash | `eb6cd3889408e1cb` |

---

## 5. What Remains Unresolved

### 5.1 Rationalized Unknowns

The 13 remaining LOW priority bubbles are **acknowledged unknowns** that:

1. Are not present in the original corpus
2. Cannot be fabricated without invention
3. Are documented per "prefer omission over inference" governance

**Examples**:
- Hardware specifications for Holodeck (B011)
- MCL reference implementation details beyond repl.py (B012)
- PII pattern specifics (B014)
- Bifurcation theory mathematics (B020)

These are NOT bugs — they are explicit acknowledgments of corpus boundaries.

### 5.2 Legacy Index Consolidation (B024)

`knowledge/dist/` contains legacy indexes separate from `build/`. Both are maintained for backwards compatibility. Future work may consolidate these.

---

## 6. Governance Compliance

### 6.1 Hard Governance Rules Followed

- ✅ Prefer omission over inference
- ✅ Mark missing evidence explicitly
- ✅ Add detail only as faithful unfurling
- ✅ No new primitives invented
- ✅ No architecture renamed

### 6.2 Non-Overrideable Invariants Enforced

- ✅ ANTI_BYPASS — Capability tokens required
- ✅ POLICY_BEAMS_ENFORCED — Inline policy shards
- ✅ SIGNED_RECEIPTS — Ed25519 signed chain
- ✅ NO_SECRET_EGRESS — Pattern deny/redact
- ✅ ANTI_PHISHING — Input pattern blocking
- ✅ MRT_FIDELITY_MIN — Meaning round-trip gate

---

## 7. Commits

| Commit | Description |
|--------|-------------|
| `a48f573` | Phase 1: Fix B001-B010, B023 — All MED bubbles resolved |
| `9707d27` | Phase 2-4: Documentation expansion, build verification |

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
