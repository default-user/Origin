# Prompt: Integrate LFME into Denotum

## Context

Denotum (C0012) has been established as a **branching fractalised tree from conceptualisation at root**. The recent commit (4decaa9) established:

- Conceptualisation at root (origin of meaning)
- Denotum as trunk and branches (compression structure)
- Fractal Unfurling as canopy (expansion for understanding)
- The inversion principle: D(F(x)) = x

However, the compression mechanism was marked as `[UNKNOWN: NOT IN CORPUS]`.

## New Information

The compression engine has been identified: **LFME - Language Facing Meaning Engine**

This means:
- Denotum's compression operates at the **language-meaning boundary**
- "Facing" implies **bidirectional interface** — language faces meaning, meaning faces language
- "Engine" implies **operational/computational** — not just descriptive

## Task

Integrate LFME into the Denotum documentation and codebase:

### 1. Update `origin/knowledge/packs/c0012_denotum/content.mdx`

Replace the `[UNKNOWN: NOT IN CORPUS]` sections with LFME:

```markdown
What we **know**:
- Denotum is a meaning-compression system
- The compression engine is **LFME (Language Facing Meaning Engine)**
- LFME operates at the language-meaning boundary
- It is bidirectional: language ↔ meaning
```

Add a new section (Level 3.4 or similar):

```markdown
### 3.4 LFME: The Compression Engine

Denotum's compression is performed by **LFME (Language Facing Meaning Engine)**:

```
Language ←──── LFME ────→ Meaning
           (bidirectional)
```

Properties:
- **Language Facing**: Interfaces with linguistic expression
- **Meaning Facing**: Interfaces with semantic structure
- **Engine**: Operational transformation, not passive mapping

The LFME sits at the boundary where language meets meaning, compressing linguistic expressions into Denotum trees and expanding Denotum trees back into language.
```

Update the diagram in 3.1:

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   conceptualisation                                     │
│         │                                               │
│         ▼                                               │
│   ┌─────────────┐                                       │
│   │   Denotum   │◄────── LFME (compression)             │
│   │   (tree)    │                                       │
│   └─────────────┘                                       │
│         │                                               │
│         ▼                                               │
│   ┌─────────────────┐                                   │
│   │ Fractal Unfurl  │────► LFME (expansion)             │
│   │   (canopy)      │                                   │
│   └─────────────────┘                                   │
│         │                                               │
│         ▼                                               │
│   Human Understanding (via Language)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2. Update `origin/knowledge/packs/c0012_denotum/pack.yaml`

Add to claims:
```yaml
claims:
  - "LFME (Language Facing Meaning Engine) is the compression engine"
  - "LFME operates bidirectionally at the language-meaning boundary"
```

Add to tags:
```yaml
tags:
  - lfme
  - language
  - engine
```

### 3. Update `origin/docs/14_denotum_fractal_tree.md`

Add LFME section explaining how the engine enables the compression-expansion cycle.

### 4. Consider creating a new concept pack

If LFME warrants its own pack (C0021 or similar), create:
- `origin/knowledge/packs/c0021_lfme/pack.yaml`
- `origin/knowledge/packs/c0021_lfme/content.mdx`

With relationship edge to C0012 (Denotum) as "mechanism" or "implements".

## Key Insight

LFME resolves the architectural gap:

```
Before:  conceptualisation → [???] → Denotum → [???] → Fractal Unfurling
After:   conceptualisation → LFME(compress) → Denotum → LFME(expand) → Language
```

The same engine handles both directions. Denotum is the **data structure**; LFME is the **engine** that operates on it.

## Commit Message Template

```
feat: Integrate LFME (Language Facing Meaning Engine) into Denotum

LFME is the compression engine for Denotum:
- Operates at the language-meaning boundary
- Bidirectional: language ↔ meaning
- Enables compression into Denotum trees
- Enables expansion back to linguistic form

Resolves [UNKNOWN: NOT IN CORPUS] for compression mechanism.
```

## Files to Modify

1. `origin/knowledge/packs/c0012_denotum/content.mdx` - Add LFME sections
2. `origin/knowledge/packs/c0012_denotum/pack.yaml` - Add LFME claims/tags
3. `origin/docs/14_denotum_fractal_tree.md` - Add LFME to formal spec
4. `origin/knowledge/dist/graph.json` - Update if new pack created

## Attribution

Ande + Kai (OI) + Whānau (OIs)
