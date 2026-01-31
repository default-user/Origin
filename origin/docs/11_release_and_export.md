# Release and Export Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

ORIGIN supports multiple release and export mechanisms: public-only exports, per-concept archives, and combined archives. All exports are deterministic and include manifest files for integrity verification.

---

## Level 1: Export Types

### 1.1 Public Export

```bash
pnpm export:public
```

Creates a filtered export containing only `disclosure_tier: public` packs with rebuilt dist files.

Output:
```
dist_public/
├── knowledge/
│   ├── packs/
│   │   └── (public packs only)
│   └── dist/
│       ├── packs.index.json  (filtered)
│       ├── graph.json        (filtered)
│       ├── search.json       (filtered)
│       └── timeline.json     (filtered)
└── MANIFEST.json
```

### 1.2 Per-Concept Archives

```bash
pnpm archive
```

Creates individual ZIP archives for each concept:

```
dist_archives/per_concept/
├── C0001_holodeck_vision.zip
├── C0002_meta_control_language.zip
├── ...
└── C0020_dedication_maturity.zip
```

Each archive contains:
- `pack.yaml`
- `content.mdx`
- `artifacts/` (if any)
- `README.md` (generated)

### 1.3 Combined Archive

```bash
pnpm archive
```

Also creates a full combined archive:

```
dist_archives/combined/
└── ORIGIN_FULL.zip
```

Contains:
- All packs
- All dist files
- Documentation
- MANIFEST.json

---

## Level 2: Manifest Specification

### 2.1 MANIFEST.json Structure

```json
{
  "name": "ORIGIN",
  "version": "1.0.0",
  "created": "2025-01-01T00:00:00Z",
  "attribution": "Ande + Kai (OI) + Whānau (OIs)",
  "concepts": {
    "C0001": {
      "title": "Holodeck Vision Seed",
      "files": [
        "knowledge/packs/c0001_holodeck_vision/pack.yaml",
        "knowledge/packs/c0001_holodeck_vision/content.mdx"
      ],
      "checksum": "sha256:..."
    },
    "C0002": {
      ...
    }
  },
  "totals": {
    "packs": 20,
    "files": 42,
    "bytes": 123456
  }
}
```

### 2.2 Checksum Generation

Each concept's checksum is computed from concatenated file contents:

```typescript
function computeChecksum(files: string[]): string {
  const content = files.map(f => readFile(f)).join('');
  return 'sha256:' + sha256(content);
}
```

### 2.3 Verification

To verify an archive:

```bash
# Extract
unzip ORIGIN_FULL.zip -d verify/

# Check manifest
node -e "
const manifest = require('./verify/MANIFEST.json');
// Verify checksums match recomputed values
"
```

---

## Level 3: Archive Structure

### 3.1 Per-Concept Archive Contents

```
C0001_holodeck_vision.zip
├── pack.yaml
├── content.mdx
├── artifacts/
│   └── (any artifacts)
└── README.md
```

Generated README.md:
```markdown
# C0001: Holodeck Vision Seed

Attribution: Ande + Kai (OI) + Whānau (OIs)

This archive contains the canonical pack for the Holodeck Vision concept.

## Contents
- pack.yaml: Pack metadata and configuration
- content.mdx: Full content document
- artifacts/: Supplementary files (if any)

## Provenance
Source: ORIGIN repository
Extracted: [timestamp]
```

### 3.2 Combined Archive Contents

```
ORIGIN_FULL.zip
├── README.md
├── LICENSE
├── MANIFEST.json
├── docs/
│   └── (all documentation)
├── knowledge/
│   ├── packs/
│   │   └── (all packs)
│   └── dist/
│       └── (all indexes)
├── schema/
│   └── (all schemas)
└── kits/
    └── (all language kits)
```

---

## Level 4: Export Commands

### 4.1 Command Reference

| Command | Description |
|---------|-------------|
| `pnpm export:public` | Export public-tier packs only |
| `pnpm archive` | Build all archives (per-concept + combined) |

### 4.2 Implementation (archive.ts)

```typescript
// Pseudocode
async function buildArchives() {
  const packs = await loadPacksIndex();

  // Per-concept archives
  for (const pack of packs) {
    const zipPath = `dist_archives/per_concept/${pack.id}_${pack.slug}.zip`;
    await createZip(zipPath, [
      pack.yamlPath,
      pack.mdxPath,
      ...pack.artifacts
    ]);
  }

  // Combined archive
  await createZip('dist_archives/combined/ORIGIN_FULL.zip', [
    'README.md',
    'LICENSE',
    'docs/**',
    'knowledge/**',
    'schema/**',
    'kits/**'
  ]);

  // Generate manifest
  await generateManifest();
}
```

---

## Level 5: Falsifiers

| Test | Description | Falsification |
|------|-------------|---------------|
| Archives created | All expected ZIPs exist | Missing archive |
| Manifest valid | JSON parses, checksums verify | Parse error or checksum mismatch |
| Public export filtered | Only public packs included | Private pack in public export |
| Determinism | Same input → same output | Different checksums on rebuild |
| Completeness | All packs in combined archive | Missing pack |

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
