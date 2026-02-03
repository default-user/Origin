# Bubble Ledger

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

This document tracks all identified "bubbles" in the ORIGIN repository — any missing detail, ambiguity, TODO, unstated purpose, incomplete conformance, missing witness, missing deterministic step, or unbounded claim. Each bubble is logged, prioritized, and tracked through resolution.

**Current Status**: 25 bubbles identified | 0 HIGH | 10 MED | 15 LOW

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

| ID | Location | Type | Description | Resolution Plan | Status | Witness |
|----|----------|------|-------------|-----------------|--------|---------|
| B001 | `kits/java/Main.java:480` | BUILD_GAP | Java GNSL Monolith has method name collision (`canonicalJson` declared twice with different signatures) | Rename instance method to `policyCanonicalJson()` | OPEN | — |
| B002 | `knowledge/packs/c0006_privacy_boundary/pack.yaml` | SCHEMA_GAP | Pack fails to load (YAML parse error due to unquoted special characters) | Fix YAML escaping for `[[REDACTED]]` in summary | OPEN | `build/reports/validate.json` |
| B003 | `knowledge/packs/c0012_denotum/pack.yaml` | SCHEMA_GAP | Provenance type "rationalization" not in allowed enum | Add "rationalization" to schema OR change to "derived" | OPEN | `build/reports/validate.json` |
| B004 | `knowledge/packs/c0017_orgasystem/pack.yaml` | SCHEMA_GAP | Same provenance type issue as B003 | Same resolution as B003 | OPEN | `build/reports/validate.json` |
| B005 | `knowledge/packs/c0021_lfme_compression_engine/pack.yaml` | SCHEMA_GAP | Multiple provenance type issues | Same resolution as B003 | OPEN | `build/reports/validate.json` |
| B006 | `knowledge/packs/c0022_lifeblood_cathedral/pack.yaml` | SCHEMA_GAP | Artifacts array contains object instead of string; provenance types invalid | Fix artifacts format; add provenance types to schema | OPEN | `build/reports/validate.json` |
| B007 | `knowledge/packs/c0023_github_spider/pack.yaml` | SCHEMA_GAP | Pack uses completely different schema structure; missing all required fields | Reformat to conform to pack.schema.json OR create integration pack schema | OPEN | `build/reports/validate.json` |
| B008 | `tests/golden/test_define.yaml` | TEST_GAP | "Define unknown term returns UNKNOWN" test fails — returns C0013 test entity instead | Fix query.ts search to return UNKNOWN when no concept found | OPEN | `npm run test` output |
| B009 | `README.md:17` | CONSISTENCY_GAP | Claims "20 Canonical Concept Packs" but packs C0021-C0023 exist (23 total) | Update count to 23 OR document C0021+ as integration packs | OPEN | `ls knowledge/packs/` |
| B010 | `docs/` | DOC_GAP | Missing `docs/17_deterministic_build_spec.md` and `docs/18_conformance_suite_guide.md` | Create these documents | OPEN | — |

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
| B023 | `schema/pack.schema.json:52` | SPEC_GAP | Provenance type enum missing "rationalization", "capsule_ingestion", "origin_integration" | Extend enum to include new types | OPEN | — |
| B024 | `knowledge/dist/` | INDEX_GAP | dist/ contains legacy indexes separate from build/ | Consolidate or document relationship | OPEN | — |
| B025 | `docs/15_roundtree_architecture.md` | DOC_GAP | No explicit conformance test descriptions with expected outcomes | Add Level 6 conformance test section | OPEN | — |

---

## Level 3: Resolution Tracking

### Completed Resolutions

*None yet.*

---

### Blocked Resolutions

*None yet.*

---

## Level 4: Bubble Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| HIGH | 0 | 0% |
| MED | 10 | 40% |
| LOW | 15 | 60% |
| **TOTAL** | **25** | 100% |

| Type | Count |
|------|-------|
| SCHEMA_GAP | 7 |
| DOC_GAP | 12 |
| TEST_GAP | 1 |
| CONSISTENCY_GAP | 1 |
| BUILD_GAP | 1 |
| INDEX_GAP | 1 |
| SPEC_GAP | 2 |

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

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
