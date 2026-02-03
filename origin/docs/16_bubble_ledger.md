# Bubble Ledger

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

This document tracks all identified "bubbles" in the ORIGIN repository — any missing detail, ambiguity, TODO, unstated purpose, incomplete conformance, missing witness, missing deterministic step, or unbounded claim. Each bubble is logged, prioritized, and tracked through resolution.

**Current Status**: 25 bubbles identified | 0 HIGH | 0 MED | 14 LOW | 11 RESOLVED

---

## Level 1: Bubble Types

| Type | Description |
|------|-------------|
| DOC_GAP | Documentation missing or incomplete |
| BUILD_GAP | Build process missing or broken |
| TEST_GAP | Test coverage missing or failing |
| SPEC_GAP | Specification incomplete or ambiguous |
| GOVERNANCE_GAP | Governance enforcement incomplete |
| INDEX_GAP | Index or search incomplete |
| CONSISTENCY_GAP | Inconsistency between claims and reality |
| SCHEMA_GAP | Schema validation issues |

---

## Level 2: Active Bubbles

### HIGH Priority (Blocks Determinism/Safety)

*No HIGH priority bubbles remaining.*

---

### MED Priority (Functional Gaps)

*All MED priority bubbles resolved.*

---

### LOW Priority (Documentation/Polish)

| ID | Location | Type | Description | Resolution Plan | Status | Witness |
|----|----------|------|-------------|-----------------|--------|---------|
| B011 | `docs/03_holodeck_spec.md:199` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - Hardware specs | Mark as rationalized unknown (not fabricatable) | OPEN | — |
| B012 | `docs/04_mcl_spec.md:227` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - Reference implementation details | Mark as rationalized (repl.py is reference) | OPEN | — |
| B013 | `docs/05_o2c.md:147-149` | DOC_GAP | [PLACEHOLDER] and [UNKNOWN] markers | Review if resolvable from corpus | OPEN | — |
| B014 | `docs/09_privacy_boundary.md:202-204` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - PII patterns and redaction tool | Mark as rationalized unknown | OPEN | — |
| B015 | `docs/07_kati.md:200` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - Production implementation | Mark as rationalized (roundtree is reference) | OPEN | — |
| B016 | `docs/12_roadmap.md:145` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - v2.0.0 details | Mark as future/TBD | OPEN | — |
| B017 | `knowledge/packs/c0011_stangraphics/content.mdx` | DOC_GAP | Multiple [UNKNOWN] markers (7 total) | Acknowledge as rationalized unknowns | OPEN | — |
| B018 | `knowledge/packs/c0010_h_haiku_oi/content.mdx` | DOC_GAP | 4 [UNKNOWN] markers for H specifications | Acknowledge as rationalized unknowns | OPEN | — |
| B019 | `knowledge/packs/c0009_kati_architecture/content.mdx` | DOC_GAP | 3 [UNKNOWN] markers | Acknowledge as rationalized unknowns | OPEN | — |
| B020 | `knowledge/packs/c0016_pacman_bifurcation/content.mdx:100` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - Bifurcation theory | Acknowledge as rationalized unknown | OPEN | — |
| B021 | `knowledge/packs/c0018_mrc/content.mdx:118` | DOC_GAP | [UNKNOWN: NOT IN CORPUS] - Prior art differentiators | Acknowledge as rationalized unknown | OPEN | — |
| B022 | `docs/01_origin_overview.md:104` | DOC_GAP | Trailing [UNKNOWN: NOT IN CORPUS] marker | Remove or explain | OPEN | — |
| B024 | `knowledge/dist/` | INDEX_GAP | dist/ contains legacy indexes separate from build/ | Consolidate or document relationship | OPEN | — |

---

## Level 3: Resolution Tracking

### Completed Resolutions

| ID | Location | Type | Description | Resolution | Witness |
|----|----------|------|-------------|------------|---------|
| B001 | `kits/java/Main.java:480` | BUILD_GAP | Java GNSL Monolith method name collision | Renamed `canonicalJson()` to `toCanonicalJson()` | `kits/java/Main.java` compiles and runs |
| B002 | `c0006_privacy_boundary/pack.yaml` | SCHEMA_GAP | YAML parse error with `[[REDACTED]]` | Quoted string in description field | `npm run validate` passes |
| B003 | `c0012_denotum/pack.yaml` | SCHEMA_GAP | Provenance type "rationalization" not in enum | Extended schema enum | `npm run validate` passes |
| B004 | `c0017_orgasystem/pack.yaml` | SCHEMA_GAP | Same provenance type issue | Fixed by B023 | `npm run validate` passes |
| B005 | `c0021_lfme/pack.yaml` | SCHEMA_GAP | Multiple provenance type issues | Fixed by B023 | `npm run validate` passes |
| B006 | `c0022_lifeblood_cathedral/pack.yaml` | SCHEMA_GAP | Artifacts format + provenance types | Fixed artifacts to strings, B023 fixed types | `npm run validate` passes |
| B007 | `c0023_github_spider/pack.yaml` | SCHEMA_GAP | Non-conforming schema structure | Complete reformat to pack.schema.json | `npm run validate` passes |
| B008 | `tools/query.ts` | TEST_GAP | Unknown term query returns match | Added token coverage threshold (50%) | `npm run test` passes 4/4 |
| B009 | `README.md:17` | CONSISTENCY_GAP | Pack count claimed 20, actual 23 | Updated to 23 packs with table | `README.md` |
| B010 | `docs/` | DOC_GAP | Missing build spec and conformance guide | Created docs/17 and docs/18 | `docs/17_deterministic_build_spec.md`, `docs/18_conformance_suite_guide.md` |
| B023 | `schema/pack.schema.json:52` | SPEC_GAP | Provenance enum incomplete | Added rationalization, capsule_ingestion, origin_integration | `schema/pack.schema.json` |
| B025 | `docs/15_roundtree_architecture.md` | DOC_GAP | No conformance test descriptions | Added Level 6 with test cases and expected outcomes | `docs/15_roundtree_architecture.md` |

---

### Blocked Resolutions

*None.*

---

## Level 4: Bubble Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| HIGH | 0 | 0% |
| MED | 0 | 0% |
| LOW | 13 | 52% |
| RESOLVED | 12 | 48% |
| **TOTAL** | **25** | 100% |

| Type | Total | Resolved | Remaining |
|------|-------|----------|-----------|
| SCHEMA_GAP | 7 | 7 | 0 |
| DOC_GAP | 13 | 2 | 11 |
| TEST_GAP | 1 | 1 | 0 |
| CONSISTENCY_GAP | 1 | 1 | 0 |
| BUILD_GAP | 1 | 1 | 0 |
| INDEX_GAP | 1 | 0 | 1 |
| SPEC_GAP | 1 | 1 | 0 |

---

## Level 5: Governance

### Bubble Addition Protocol

1. Identify bubble through search, build, test, or review
2. Assign unique ID (B###)
3. Classify type and priority
4. Document location and description
5. Define resolution plan
6. Set status to OPEN

### Bubble Resolution Protocol

1. Implement resolution per plan
2. Run validation (`npm run validate && npm run build && npm run test`)
3. Update status to RESOLVED
4. Add witness (file changed, test output, etc.)
5. Commit with bubble ID in message

### Priority Definitions

- **HIGH**: Blocks deterministic build, safety violation, or system integrity failure
- **MED**: Functional gap — validation fails, tests fail, or specification incomplete
- **LOW**: Documentation polish, minor inconsistency, or acknowledged unknown

---

## Level 6: Rationalized Unknowns

The remaining LOW priority bubbles (B011-B022, excluding resolved ones) are **rationalized unknowns** — information that:

1. Is not present in the original corpus
2. Cannot be fabricated without invention
3. Must be acknowledged rather than guessed

These are documented per the "prefer omission over inference" governance principle. They do not block determinism, safety, or runtime operation.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
