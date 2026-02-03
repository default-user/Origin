# Thinking Without Models

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

## Overview

ORIGIN includes a deterministic "thinking engine" that can answer questions and derive conclusions **without using any LLM inference**. This system operates purely through:

1. **Symbolic reasoning** over structured knowledge
2. **Rule-based inference** using Horn-like clauses
3. **Graph traversal** for relationship discovery
4. **Inverted index search** for term resolution

Every answer is:
- **Citeable**: Points to exact source files and YAML paths
- **Explainable**: Includes a reasoning trace showing which rules fired
- **Refutable**: Can be challenged by examining the provenance chain
- **Reproducible**: Identical inputs always produce identical outputs

## Core Principles

### No LLM, No Randomness

This system uses zero probabilistic inference:
- No model calls
- No embeddings or vector search
- No "best guess" answers
- No confidence scores

If the knowledge is missing or ambiguous, the system returns `UNKNOWN` with an explanation of what's missing.

### Fail-Closed Design

When knowledge is insufficient:
```json
{
  "answer": "UNKNOWN",
  "unknownReason": "No definition found for term: 'quantum coherence'",
  "citations": [],
  "trace": [...]
}
```

### Privacy Boundary Enforcement

All data has a sensitivity level:
- `PUBLIC`: Always accessible
- `SENSITIVE`: Requires `--private` flag
- `REDACTED`: Never revealed (only reference to existence)

```bash
# Default: PUBLIC only
npm run query -- "define Secret Project"
# Returns: UNKNOWN (blocked by privacy boundary)

# With private flag: PUBLIC + SENSITIVE
npm run query -- --private "define Secret Project"
# Returns: Definition if SENSITIVE, still UNKNOWN if REDACTED
```

## Query Language

### `define <term>`

Look up the definition of a term or concept.

```bash
npm run query -- "define Holodeck"
```

**Process:**
1. Tokenize the search term
2. Look up tokens in inverted index
3. Rank matching entities by score
4. Return top match with attributes and citations

### `relate <A> <B>`

Find the shortest path between two entities.

```bash
npm run query -- "relate C0001 C0002"
```

**Process:**
1. Resolve entity names to IDs
2. BFS traversal through typed edges
3. Return path with relationship types
4. Collect provenance from each hop

### `find <Type> where <predicate>(...)`

Find entities matching predicates.

```bash
npm run query -- "find Concept where hasTag(?, philosophy)"
```

**Process:**
1. Run rule engine to derive additional facts
2. Filter entities by type
3. Apply predicate filters
4. Return matching entities with citations

### `prove <predicate>(<args>)`

Prove whether a fact is derivable.

```bash
npm run query -- "prove influences(C0001, C0002)"
```

**Process:**
1. Run rule engine with base facts
2. Check if target fact exists (base or derived)
3. If derived, trace back through rule firings
4. Return proof trace with supporting facts

## Rule Engine

### Rule Format

Rules are defined in YAML in the `rules/` directory:

```yaml
rule_id: R001_parent_transitivity
description: "Transitive closure of parent relationship"
head:
  predicate: ancestor
  args: ["?a", "?c"]
body:
  - predicate: edge
    args: ["?a", "parent", "?b"]
  - predicate: edge
    args: ["?b", "parent", "?c"]
filters:
  - op: neq
    a: "?a"
    b: "?c"
```

### Evaluation Strategy

The engine uses forward-chaining semi-naive evaluation:

1. Start with base facts from `build/index.json`
2. For each rule (in ID order):
   - Find all matching bindings for body atoms
   - Check filter constraints
   - Derive new head facts
3. Repeat until fixed point (no new facts)
4. Return derived facts with firing trace

### Sensitivity Inheritance

Derived facts inherit the maximum sensitivity of their supporting facts:
- `derived_fact.sensitivity = max(supporting_facts.sensitivity)`

## Intermediate Representation (IR)

### Core Types

```typescript
interface Entity {
  id: string;
  type: EntityType;
  labels: string[];
  attrs: Record<string, unknown>;
  provenance: Provenance;
  sensitivity: Sensitivity;
}

interface Fact {
  predicate: string;
  args: string[];
  derived: boolean;
  provenance: Provenance[];
  sensitivity: Sensitivity;
}

interface Provenance {
  file: string;
  yamlPath: string;
  contentHash: string;
  crystalId: string | null;
  crystalRoot: string;
}
```

### Build Artifacts

| File | Purpose |
|------|---------|
| `build/index.json` | Entities, edges, facts with provenance |
| `build/graph.json` | Adjacency lists for traversal |
| `build/search.json` | Inverted index for term lookup |
| `build/traces/*.json` | Saved query traces for explain |
| `build/reports/validate.json` | Validation report |

## Determinism Guarantees

### Stable Ordering

All outputs are deterministically ordered:
- Entities: sorted by (type, id)
- Edges: sorted by (src, rel, dst)
- Facts: sorted by (predicate, args)
- Rules: sorted by rule_id

### Stable Hashing

Content hashes use:
1. Stable JSON stringify (sorted keys)
2. SHA-256 hashing
3. No timestamp-dependent data in hash input

### Verification

```bash
npm run determinism-check
```

This runs the full build pipeline twice and compares content hashes. Any mismatch fails the check.

## Testing

### Golden Tests

Golden tests in `tests/golden/*.yaml`:

```yaml
name: "Define Holodeck concept"
query: "define Holodeck"
expected_type: "object"
expected_fields:
  - "id"
  - "type"
expected_answer_contains:
  type: "Concept"
expected_trace_contains:
  - "search"
  - "lookup"
```

Run tests:
```bash
npm run test
```

### Adding New Tests

1. Create `tests/golden/test_<feature>.yaml`
2. Add test cases with expected outcomes
3. Run `npm run test` to verify

## Extending the System

### Adding New Rules

1. Create/edit `rules/*.yaml`
2. Follow the rule schema
3. Rules are automatically loaded at query time

### Adding New Crystal Roots

1. Edit `config/crystal_roots.json`:
   ```json
   {
     "roots": ["knowledge/packs", "crystals_prize"],
     "schemaOverrides": {
       "crystals_prize": "schema/prize.schema.json"
     }
   }
   ```
2. Run `npm run build` to reindex

### Adding New Predicates

Facts are extracted from crystals automatically. To add new predicates:

1. Edit `tools/build-index.ts`
2. Add extraction logic in `extractFacts()`
3. Rebuild: `npm run build:index`

## What Counts as Proof vs UNKNOWN

### Provable (returns answer):
- Fact exists in base facts (from crystals)
- Fact derivable via rule chain
- Path exists between entities
- Entity matches search term

### UNKNOWN (returns with reason):
- Term not found in index
- No path exists between entities
- Predicate not provable from facts + rules
- Privacy boundary blocks access
- Ambiguous query that can't be resolved

## Quick Reference

```bash
# Build all artifacts
npm run build

# Validate crystals
npm run validate

# Query (examples)
npm run query -- "define Holodeck"
npm run query -- "relate C0001 C0002"
npm run query -- "find Concept where hasTag(?, philosophy)"
npm run query -- "prove influences(C0001, C0002)"

# With private access
npm run query -- --private "define Sensitive Topic"

# Explain a previous query
npm run explain -- query_1234567890

# List saved traces
npm run explain

# Run golden tests
npm run test

# Verify determinism
npm run determinism-check
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ORIGIN Thinking Engine                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  crystals/         rules/          config/                       │
│  └── pack.yaml     └── core.yaml   └── crystal_roots.json       │
│       │                 │                    │                   │
│       ▼                 ▼                    ▼                   │
│  ┌─────────┐       ┌─────────┐       ┌─────────────┐            │
│  │validate │       │ Rule    │       │ Multi-root  │            │
│  │  .ts    │       │ Loader  │       │   Config    │            │
│  └────┬────┘       └────┬────┘       └──────┬──────┘            │
│       │                 │                    │                   │
│       ▼                 │                    │                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              build-index.ts                          │        │
│  │  (Extracts Entities, Edges, Facts with Provenance)  │        │
│  └───────────────────────┬─────────────────────────────┘        │
│                          │                                       │
│                          ▼                                       │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐                 │
│  │build-graph │  │build-search│  │   IR/      │                 │
│  │   .json    │  │   .json    │  │ index.json │                 │
│  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘                 │
│        │               │               │                         │
│        └───────────────┼───────────────┘                         │
│                        ▼                                         │
│  ┌─────────────────────────────────────────────────────┐        │
│  │                  query.ts                            │        │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌────────┐  │        │
│  │  │ define  │  │ relate  │  │  find   │  │ prove  │  │        │
│  │  └────┬────┘  └────┬────┘  └────┬────┘  └───┬────┘  │        │
│  │       │            │            │           │        │        │
│  │       └────────────┴────────────┴───────────┘        │        │
│  │                         │                             │        │
│  │                         ▼                             │        │
│  │               ┌─────────────────┐                    │        │
│  │               │   Rule Engine   │                    │        │
│  │               │ (Forward Chain) │                    │        │
│  │               └────────┬────────┘                    │        │
│  │                        │                             │        │
│  │                        ▼                             │        │
│  │  ┌─────────────────────────────────────────────┐    │        │
│  │  │ QueryResult { answer, citations, trace }    │    │        │
│  │  └─────────────────────────────────────────────┘    │        │
│  └─────────────────────────────────────────────────────┘        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Limitations

1. **No fuzzy matching**: Exact token matching only
2. **No semantic similarity**: No embeddings or vector search
3. **Finite rule depth**: Max 100 iterations (configurable)
4. **No negation as failure**: Can't prove "not X"
5. **No aggregation**: Can't count or sum

These are intentional constraints to maintain determinism and explainability.
