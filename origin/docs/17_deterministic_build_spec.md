# Deterministic Build Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

ORIGIN produces deterministic build outputs. Given the same source files, the build process MUST produce byte-identical outputs. This document specifies the exact commands, expected outputs, and reproducibility requirements.

---

## Level 1: Build Commands

### 1.1 Full Build Sequence

```bash
# Install dependencies (required once)
npm install

# Validate all packs against schema
npm run validate

# Build all indexes
npm run build

# Run tests
npm run test

# Run determinism check
npm run determinism-check
```

### 1.2 Individual Build Steps

| Command | Script | Output | Description |
|---------|--------|--------|-------------|
| `npm run validate` | `tools/validate.ts` | `build/reports/validate.json` | Validate packs against schema |
| `npm run build:index` | `tools/build-index.ts` | `build/index.json` | Build IR index from packs |
| `npm run build:graph` | `tools/build-graph.ts` | `build/graph.json`, `knowledge/dist/graph.json` | Build concept graph |
| `npm run build:search` | `tools/build-search.ts` | `build/search.json`, `knowledge/dist/search.json` | Build search index |
| `npm run build:timeline` | `tools/build-timeline.ts` | `knowledge/dist/timeline.json` | Build timeline |
| `npm run test` | `tools/run-tests.ts` | Console output | Run golden tests |
| `npm run determinism-check` | `tools/determinism-check.ts` | Console output | Verify reproducibility |

---

## Level 2: Expected Outputs

### 2.1 Build Artifacts

After a successful build, the following files are produced:

```
build/
├── index.json        # IR index (entities, facts, relations)
├── graph.json        # Extended graph with 280+ nodes
├── search.json       # Inverted index with 1000+ tokens
└── reports/
    └── validate.json # Validation report

knowledge/dist/
├── packs.index.json  # Legacy pack index
├── graph.json        # Legacy graph (23 nodes)
├── search.json       # Legacy search index
└── timeline.json     # Event timeline
```

### 2.2 Determinism Requirements

Each build artifact includes a content hash for verification:

```json
{
  "metadata": {
    "generated_at": "ISO timestamp",
    "content_hash": "sha256 of deterministic content"
  }
}
```

**Invariant**: Running the same build twice MUST produce identical content hashes.

### 2.3 What Changes Invalidate Outputs

| Change Type | Affected Outputs | Action Required |
|-------------|------------------|-----------------|
| Pack YAML modified | All | Full rebuild |
| Pack content.mdx modified | index, search | Rebuild affected |
| Schema modified | validate.json | Re-validate |
| Tool script modified | Affected outputs | Rebuild |
| New pack added | All | Full rebuild |
| Pack deleted | All | Full rebuild |

---

## Level 3: Reproducibility Guarantees

### 3.1 Source Determinism

Build inputs are sorted alphabetically before processing:
- Packs processed in ID order (C0001, C0002, ...)
- Tags sorted alphabetically
- Claims sorted by position in YAML

### 3.2 Output Determinism

JSON outputs use stable serialization:
- Keys sorted alphabetically
- No floating-point drift
- Consistent whitespace (2-space indent)

### 3.3 Timestamp Handling

- `generated_at` timestamps vary but are metadata only
- `content_hash` excludes timestamps for determinism
- Source dates (created_date, updated_date) are part of content

---

## Level 4: Seal Handles for QED

### 4.1 Build Summary Hashes

After a complete build, these hashes form the "seal handles":

| Handle | Source | Purpose |
|--------|--------|---------|
| `policy_hash` | `config/crystal_v3.0.6.json` | Governance policy |
| `manifest_hash` | Build artifact hashes | Complete build state |
| `validate_hash` | `build/reports/validate.json` | Validation status |
| `index_hash` | `build/index.json` | Entity graph state |
| `graph_hash` | `build/graph.json` | Relationship state |
| `search_hash` | `build/search.json` | Query index state |

### 4.2 Computing Manifest Hash

```javascript
const manifestHash = sha256(JSON.stringify({
  validate: validateHash,
  index: indexHash,
  graph: graphHash,
  search: searchHash
}));
```

### 4.3 GNSL Integration

The Java GNSL Monolith produces additional seal handles:

| Handle | Source | Purpose |
|--------|--------|---------|
| `receipt_head` | ReceiptLog | Event chain head |
| `graph_head` | HypergraphStore | Knowledge graph head |

---

## Level 5: Validation Runbook

### 5.1 Pre-Commit Validation

```bash
# Full validation sequence
npm run validate && npm run build && npm run test && npm run determinism-check

# Expected: All pass, no errors
```

### 5.2 CI/CD Pipeline

```yaml
validate:
  - npm install
  - npm run validate
  - npm run build
  - npm run test
  - npm run determinism-check
  - archive build/reports/validate.json
```

### 5.3 Debugging Build Failures

| Symptom | Cause | Resolution |
|---------|-------|------------|
| Validation fails | Schema violation | Fix pack YAML |
| Hash mismatch | Non-deterministic code | Check sort order, timestamps |
| Test fails | Query logic error | Debug tools/query.ts |
| Index empty | No packs found | Check crystal_roots.json |

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
