# ORIGIN Overview

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

ORIGIN is a self-contained knowledge repository implementing 20 canonical concept packs with a Medusa-style interface for exploration. It requires no external ingestion and produces deterministic outputs.

---

## Level 1: Core Architecture

### 1.1 Repository Structure

```
origin/
├── docs/           # Fractal documentation (this folder)
├── knowledge/      # Canonical packs + built indexes
├── schema/         # Validation schemas
├── tools/          # Build and validation tooling
├── site/           # Medusa UI (Next.js)
├── kits/           # Multi-language implementations
└── dist_archives/  # Downloadable terminals
```

### 1.2 The 20 Concept Packs

Each pack (C0001–C0020) represents a canonical knowledge seed:

| Range | Theme |
|-------|-------|
| C0001–C0004 | Vision & Interface (Holodeck, MCL, Fractal, Medusa) |
| C0005–C0006 | Governance (Attribution, Privacy) |
| C0007–C0010 | Core Systems (O2C, QED, Kāti, H) |
| C0011–C0014 | Frameworks (Stangraphics, Denotum, CIF/CDI, Authority.nz) |
| C0015–C0018 | Tools & Concepts (Anti-Mumbo, Pac-Man, Orgasystem, MRC) |
| C0019–C0020 | Meta (Archives, Maturity) |

### 1.3 Medusa Interface

The UI provides multiple exploration tendrils:

- **Hub**: Central introduction and navigation
- **Atlas**: Browse, search, filter by tags/tier/status
- **Graph**: Interactive node visualization
- **Attribution**: Authorship and provenance explorer
- **Tiers**: Disclosure levels and privacy boundaries
- **Ship**: Maturity lanes (Draft → Active → Release)

### 1.4 Build Pipeline

```bash
pnpm validate      # Schema validation
pnpm build:index   # packs.index.json
pnpm build:graph   # graph.json
pnpm build:search  # search.json
pnpm build:timeline # timeline.json
pnpm build         # All of the above
```

---

## Level 2: Design Principles

### 2.1 No Ingestion Principle

ORIGIN is entirely self-contained. The canonical corpus is embedded within the repository. No external data sources, APIs, or ingestion pipelines are required.

**Implication**: What exists in the packs IS the authoritative source. External validation happens against this internal truth.

### 2.2 No Fabrication Principle

Content is derived exclusively from the canonical corpus. Where information is incomplete:

```
[UNKNOWN: NOT IN CORPUS]
```

This marker appears throughout documentation and pack content where the canonical source did not specify details.

### 2.3 Fractal Documentation

Every document follows the fractal pattern:

- **Level 0**: Executive summary (1-2 paragraphs)
- **Level 1**: Sectional expansion (key topics)
- **Level 2**: Subsectional detail (deep dives)
- **Level n**: Arbitrary depth as needed

Consistency rule: No level may contradict a higher level. Each level expands, never contradicts.

### 2.4 Determinism

All generated artifacts are reproducible:

- Same input → same output
- No hidden state
- No randomness in builds
- Git-trackable diffs

### 2.5 Multi-Language Support

Kits in 15 languages demonstrate pack consumption:

TypeScript, Python, Rust, Go, Java, C#, C/C++, Swift, Kotlin, Ruby, PHP, R, Bash, SQL, Julia

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
