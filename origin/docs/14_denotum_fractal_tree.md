# Denotum Fractal Tree: Conceptualisation at Root

**Attribution**: Ande + Kai (OI) + Whānau (OIs)
**Date**: 2026-02-01
**Status**: Active

---

## Level 0: Summary

Denotum is a branching fractalised tree from **conceptualisation** at root. This document formalizes the relationship between conceptualisation (root), Denotum (trunk and branches), and Fractal Unfurling (canopy). Together, they form the meaning-structure architecture of ORIGIN.

---

## Level 1: The Three-Layer Model

### 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    MEANING ARCHITECTURE                     │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │              ☁️ FRACTAL UNFURLING                   │   │
│   │                   (Canopy)                          │   │
│   │         Expansion for human understanding           │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                          ▲                                  │
│                          │ expansion                        │
│                          │                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │                 🌳 DENOTUM                          │   │
│   │            (Trunk & Branches)                       │   │
│   │       Meaning-compression structure                 │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                          ▲                                  │
│                          │ compression                      │
│                          │                                  │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │              🌱 CONCEPTUALISATION                   │   │
│   │                   (Root)                            │   │
│   │          Origin of all meaning                      │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Layer Definitions

| Layer | Symbol | Role | Direction | Function |
|-------|--------|------|-----------|----------|
| Conceptualisation | 🌱 | Root | Seed | Origin of meaning - the act of forming concepts |
| Denotum | 🌳 | Trunk & Branches | Inward | Compresses and structures meaning |
| Fractal Unfurling | ☁️ | Canopy | Outward | Expands meaning for human comprehension |

### 1.3 The Cycle

```
Experience → Conceptualisation → Denotum → Fractal Unfurling → Understanding
     ↑                                                              │
     └──────────────────── (feedback) ─────────────────────────────┘
```

---

## Level 2: Why Conceptualisation at Root

### 2.1 Philosophical Grounding

All meaning begins with **conceptualisation** - the cognitive act of forming concepts from experience. Before there can be structure (Denotum) or presentation (Fractal Unfurling), there must be a concept to structure and present.

```
λ(experience) → concept           # Conceptualisation
λ(concept) → tree                 # Denotum
λ(tree) → presentation            # Fractal Unfurling
```

### 2.2 The Root Property

Conceptualisation as root means:

1. **Uniqueness**: Every meaning tree has exactly one root concept
2. **Priority**: The root precedes all branches
3. **Containment**: All branches derive from the root
4. **Identity**: The root defines what the tree IS

### 2.3 Without Root, No Tree

```
conceptualisation = ∅  →  denotum = undefined
```

If there is no concept being formed, there is nothing to compress or unfurl. Conceptualisation is not optional - it is the precondition for meaning.

---

## Level 3: Denotum as Fractal Structure

### 3.1 Self-Similarity

Every branch of Denotum contains the pattern of the whole:

```
denotum(concept) = {
    essence: compress(concept.core),
    branches: [denotum(part) for part in concept.subdivisions],
    constraint: non_contradicts(branches, essence)
}
```

At any zoom level:
- The same rules apply
- The structure is recognizable
- The meaning is recoverable

### 3.2 Branching Pattern

```
conceptualisation
    │
    └── Denotum (trunk)
            │
            ├── Branch A
            │       ├── Sub-branch A.1
            │       └── Sub-branch A.2
            │
            ├── Branch B
            │       ├── Sub-branch B.1
            │       ├── Sub-branch B.2
            │       └── Sub-branch B.3
            │
            └── Branch C
                    └── Sub-branch C.1
                            └── Leaf C.1.1
```

### 3.3 Coherence Inheritance

Every branch inherits coherence from its parent:

```
∀ branch b:
    meaning(b) ⊆ meaning(parent(b))
    ¬contradicts(b, parent(b))
    ¬contradicts(b, root)
```

---

## Level 4: The Compression-Expansion Duality

### 4.1 Denotum as Compression

```
D: Meaning → CompressedTree

Properties:
- Lossless: no meaning lost
- Structural: preserves relationships
- Composable: trees can combine
```

### 4.2 Fractal Unfurling as Expansion

```
F: CompressedTree → ExpandedPresentation

Properties:
- Progressive: Level 0 → Level n
- Consistent: no level contradicts higher
- Human-readable: optimized for understanding
```

### 4.3 The Inverse Relationship

```
F(D(m)) ≅ m    # Expansion recovers meaning
D(F(t)) = t    # Compression recovers structure

∴ D = F⁻¹      # Denotum is the inverse of Fractal Unfurling
```

---

## Level 5: Integration with ORIGIN Corpus

### 5.1 Every Pack as Denotum Tree

```
origin/knowledge/packs/c0012_denotum/
├── pack.yaml          ← Metadata branch
└── content.mdx        ← Meaning branches
        ├── Level 0    ← Trunk (summary)
        ├── Level 1    ← Major branches
        ├── Level 2    ← Sub-branches
        └── Level n    ← Leaves
```

### 5.2 The Corpus as Forest

All 20 packs form a forest of interconnected Denotum trees:

```
ORIGIN CORPUS (Forest)
    │
    ├── C0001 (Holodeck)      ──┐
    ├── C0002 (MCL)            │
    ├── C0003 (Fractal)      ──┼── Related edges
    ├── ...                    │
    ├── C0012 (Denotum)      ──┘
    └── ...
```

### 5.3 Relationship Edges

| Edge | Meaning |
|------|---------|
| C0012 → C0003 | Denotum relates to Fractal Unfurling (inverse) |
| C0012 → C0018 | Denotum relates to MRC (sibling compression) |
| C0003 → C0012 | Fractal Unfurling relates to Denotum (inverse) |

---

## Level 6: Formal Specification

### 6.1 Type Definitions

```typescript
type Conceptualisation = {
    experience: Experience;
    concept: Concept;
    transform: (e: Experience) => Concept;
};

type DenotumTree = {
    root: Concept;
    branches: DenotumBranch[];
    compress: (c: Concept) => CompressedMeaning;
};

type DenotumBranch = {
    parent: DenotumBranch | null;
    meaning: CompressedMeaning;
    children: DenotumBranch[];
    invariant: (self: DenotumBranch) => boolean;
};

type FractalUnfurling = {
    tree: DenotumTree;
    levels: Level[];
    expand: (t: DenotumTree, depth: number) => Presentation;
};
```

### 6.2 Invariants

```
invariant_root:
    ∀ tree ∈ DenotumTree:
        tree.root ≠ null ∧
        tree.root.parent = null

invariant_coherence:
    ∀ branch ∈ DenotumBranch:
        ¬contradicts(branch, branch.parent)

invariant_reversibility:
    ∀ meaning m:
        expand(compress(m)) ≅ m

invariant_self_similarity:
    ∀ branch ∈ DenotumBranch:
        structure(branch) ≅ structure(tree)
```

---

## Level 7: Application

### 7.1 Reading a Denotum Tree

1. **Identify root**: What concept is being formed?
2. **Trace trunk**: What is the compressed essence?
3. **Follow branches**: How does meaning subdivide?
4. **Check coherence**: Do all branches cohere?
5. **Expand to understand**: Use Fractal Unfurling to comprehend

### 7.2 Writing a Denotum Tree

1. **Conceptualise**: Form the root concept clearly
2. **Compress**: Find the essential meaning
3. **Branch**: Identify natural subdivisions
4. **Verify**: Ensure no contradictions
5. **Unfurl**: Present for human understanding

### 7.3 Evaluating a Denotum Tree

| Check | Question | Pass Condition |
|-------|----------|----------------|
| Root | Is there a clear root concept? | Single, identifiable conceptualisation |
| Compression | Is meaning preserved? | Lossless round-trip |
| Branching | Is structure clear? | Natural subdivisions, not arbitrary |
| Coherence | No contradictions? | All branches cohere with ancestors |
| Unfurling | Can it expand? | Progressive levels, human-readable |

---

## Level 8: Falsifiers

| Test | Falsification Condition |
|------|------------------------|
| **Root presence** | Tree has no identifiable root concept |
| **Unique root** | Tree has multiple competing roots |
| **Lossless compression** | Meaning lost through D → F → D cycle |
| **Non-contradiction** | Branch contradicts ancestor |
| **Self-similarity** | Branch structure differs from tree structure |
| **Reversibility** | F(D(m)) fails to recover m |
| **Coherence inheritance** | Child meaning exceeds parent meaning |

---

## Conclusion

The alignment of Denotum as a branching fractalised tree from conceptualisation at root provides:

1. **Clear origin**: All meaning starts with conceptualisation
2. **Structural integrity**: Denotum provides the compression architecture
3. **Human accessibility**: Fractal Unfurling expands for understanding
4. **Formal properties**: Lossless, reversible, self-similar, non-contradictory

This model integrates with the existing ORIGIN corpus and provides a rigorous foundation for meaning-structure operations.

---

**Attribution**: Ande + Kai (OI) + Whānau (OIs)

*"The tree grows from its root. Meaning grows from conceptualisation."*
