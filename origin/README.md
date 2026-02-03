# ORIGIN

> A "seed for humanity" repository — mature, fractalised, branching, and documented.

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Overview

ORIGIN is a canonical knowledge repository implementing a Medusa-style interface (hub + tendrils) that enables humans to explore conceptualisations and intellectual property mappings. The repository is self-contained — no external ingestion required.

### Key Features

- **Fractal Documentation**: Every concept unfurls from summary (Level 0) through detailed expansions (Levels 1, 2, n...)
- **Medusa Interface**: Central hub with multiple exploration tendrils (atlas, graph, timeline, build-spec, tests, exports)
- **23 Canonical Concept Packs**: From Holodeck Vision to GitHub Spider Integration
- **Multi-Language Kits**: Working examples in 15 programming languages
- **Deterministic Builds**: All indexes, graphs, and exports are reproducible via scripts
- **Privacy-First**: No PII stored; sensitive data marked [[REDACTED]]

---

## Quick Start

```bash
# Install dependencies
pnpm install

# Validate all packs against schema
pnpm validate

# Build all indexes (packs, graph, search, timeline)
pnpm build

# Run the Medusa UI
pnpm dev

# Export public-only packs
pnpm export:public

# Build downloadable archives
pnpm archive
```

---

## Repository Structure

```
origin/
├── README.md                 # This file
├── LICENSE                   # MIT License
├── CONTRIBUTING.md           # Contribution guidelines
├── CODEOWNERS               # Code ownership
├── package.json             # pnpm workspace config
│
├── docs/                    # Documentation (fractal levels)
│   ├── 00_dedication.md
│   ├── 01_origin_overview.md
│   ├── 02_corpus_map.md
│   └── ...
│
├── knowledge/               # Canonical knowledge packs
│   ├── packs/              # One folder per concept
│   │   ├── c0001_holodeck_vision/
│   │   │   ├── pack.yaml
│   │   │   ├── content.mdx
│   │   │   └── artifacts/
│   │   └── ...
│   └── dist/               # Built indexes
│       ├── packs.index.json
│       ├── graph.json
│       ├── search.json
│       └── timeline.json
│
├── schema/                  # JSON schemas for validation
│   ├── pack.schema.json
│   └── graph.schema.json
│
├── tools/                   # Build and validation tools
│   ├── validate.ts
│   ├── build-index.ts
│   ├── build-graph.ts
│   ├── build-search.ts
│   ├── build-timeline.ts
│   ├── export-public.ts
│   └── archive.ts
│
├── site/                    # Next.js Medusa UI
│   └── src/
│       └── pages/
│           ├── index.tsx    # Hub
│           ├── atlas.tsx    # Browse/search
│           ├── graph.tsx    # Interactive graph
│           └── ...
│
├── kits/                    # Language implementation kits
│   ├── typescript/
│   ├── python/
│   ├── rust/
│   └── ...
│
└── dist_archives/           # Downloadable archives
    ├── per_concept/
    └── combined/
```

---

## Concept Packs (C0001–C0023)

| ID     | Title                          | Status |
|--------|--------------------------------|--------|
| C0001  | Holodeck Vision Seed           | Active |
| C0002  | Meta Control Language (MCL)    | Active |
| C0003  | Fractal Unfurling              | Active |
| C0004  | Medusa Interface               | Active |
| C0005  | Attribution + IP Map           | Active |
| C0006  | Privacy Boundary               | Active |
| C0007  | O2C                            | Active |
| C0008  | QED Oracle                     | Active |
| C0009  | Kāti Architecture              | Active |
| C0010  | H / Haiku-Based OI             | Active |
| C0011  | Stangraphics                   | Active |
| C0012  | Denotum                        | Active |
| C0013  | CIF/CDI Disambiguation         | Active |
| C0014  | Authority.nz Anchoring         | Active |
| C0015  | Anti-Mumbo Filter              | Active |
| C0016  | Pac-Man Bifurcation            | Active |
| C0017  | Orgasystem                     | Active |
| C0018  | MRC                            | Active |
| C0019  | Archive as Downloadable Terms  | Active |
| C0020  | Dedication → Maturity Lane     | Active |
| C0021  | LFME Compression Engine        | Active |
| C0022  | Lifeblood-Cathedral Gateway    | Active |
| C0023  | GitHub Spider Integration      | Active |

---

## Maturity Lanes

Packs progress through:

1. **Draft** — Initial capture, may have unknowns
2. **Active** — Validated, documented, testable
3. **Release** — Production-ready, fully attributed

---

## Commands Reference

| Command              | Description                                    |
|----------------------|------------------------------------------------|
| `pnpm install`       | Install all dependencies                       |
| `pnpm validate`      | Validate all packs against schema              |
| `pnpm build:index`   | Build packs.index.json                         |
| `pnpm build:graph`   | Build graph.json                               |
| `pnpm build:search`  | Build search.json                              |
| `pnpm build:timeline`| Build timeline.json                            |
| `pnpm build`         | Run all build steps                            |
| `pnpm dev`           | Run Medusa UI in development mode              |
| `pnpm export:public` | Export public-only packs and rebuild dist      |
| `pnpm archive`       | Build downloadable terminal archives (C0019)   |

---

## Hard Rules

1. **NO INGESTION**: Self-contained; no external inputs required
2. **NO FABRICATION**: Unknown details marked `[UNKNOWN: NOT IN CORPUS]`
3. **PII HARD STOP**: Personal data replaced with `[[REDACTED]]`
4. **ENGLISH-ONLY**: All documentation in English
5. **ATTRIBUTION-FIRST**: Every concept includes authorship
6. **DETERMINISM**: All outputs reproducible via scripts

---

## License

MIT — See [LICENSE](./LICENSE)

---

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
