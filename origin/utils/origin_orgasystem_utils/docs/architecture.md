# Origin Orgasystem Architecture

## Overview

The Origin orgasystem is a deterministic knowledge infrastructure built in Rust.
Every operation is fail-closed: if a check fails, the system halts rather than
producing incorrect output.

## Crate Map

```
origin_orgasystem_utils/
├── crates/
│   ├── seed_core          # Root identity: SHA-256 fingerprint of the 2I seed
│   ├── dpack_core         # DPACK: deterministic pack/verify/unfurl
│   ├── compress           # CPACK: zstd-compressed DPACK with integrity hash
│   ├── lfme_core          # LFME/Denotum: meaning structures, parser, validator
│   ├── rag_deterministic  # Deterministic RAG: chunking, embedding stub, index
│   ├── replication_core   # Replication: R0 local clone, R1 rootball, R2 zip2repo
│   └── originctl          # CLI: the single entry point for all operations
├── fixtures/              # Test fixtures (sample_tree)
├── spec/                  # Format specifications (YAML)
└── docs/                  # This documentation
```

## Data Flow

```
Repository                    DPACK directory              CPACK file
   │                              │                            │
   ├── pack ─────────────────────>│                            │
   │   (walk + hash + manifest)   │                            │
   │                              ├── compress ───────────────>│
   │                              │   (zstd + framing)         │
   │                              │<── decompress ─────────────┤
   │                              │   (verify + restore)       │
   │<── unfurl ───────────────────┤                            │
   │   (verify + restore files)   │                            │
   │                              │                            │
   └── verify ────────────────────┤                            │
       (hashes + seed binding)    └── verify ──────────────────┘
                                      (integrity + seed)
```

## Invariants

1. **Determinism**: Same input always produces identical output (byte-for-byte).
2. **Fail-closed**: Any check failure halts the operation.
3. **Seed binding**: Every artifact binds to the root 2I seed fingerprint.
4. **Round-trip**: `decompress(compress(dpack)) == dpack` always.
5. **Stable ordering**: BTreeMap for keys, sorted file walks, fixed byte order.

## Gate System

Operations emit gate results (PASS/FAIL/SKIP):

| Gate | Description |
|------|-------------|
| G0_SCHEMA | Manifest conforms to schema |
| G1_INTEGRITY | Pack hash matches file entries |
| G3_PINNING | Every file hash matches on disk |
| G4_SEED_BINDING | Seed fingerprint matches |
| G6_ORGASYSTEM_SHAPE | File count/tree shape recorded |
| G7_RELEASE_RECEIPT | Receipt written on success |

## LFME/Denotum

The Denotum model represents the 2I seed as typed Rust structs:

- **Denotum**: Top-level seed (version, steward, posture, glossary, axioms, layers)
- **Beam**: Atomic meaning-bearing claim
- **Lattice**: Composed set of beams
- **Prism**: Behavioral refractor (tool/adapter/judge)

The parser handles the raw YAML seed format. The validator enforces invariants
(fail-closed, stop-wins, glossary non-empty, etc.). Canonical serialization
ensures stable fingerprints via sorted BTreeMap keys.

## Deterministic RAG

A toy-but-real retrieval pipeline:

1. **Chunking**: Split on paragraph boundaries, then word boundaries
2. **Embedding**: SHA-256-based hash embedding (deterministic, no external calls)
3. **Index**: BTreeMap keyed by chunk ID for stable iteration
4. **Retrieval**: Cosine similarity with deterministic tie-breaking by chunk ID
