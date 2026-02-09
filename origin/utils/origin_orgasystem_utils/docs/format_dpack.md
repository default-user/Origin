# DPACK Format Specification

## Version

1.0

## Overview

A DPACK (Deterministic Pack) is a directory-based snapshot of a repository.
It captures file paths, content hashes, and seed binding in a deterministic,
verifiable format.

## Directory Structure

```
<dpack_dir>/
├── manifest.json    # Index of files, hashes, and metadata
├── receipt.json     # Audit trail from pack operation
└── data/            # File contents at their original relative paths
    ├── README.md
    ├── src/
    │   └── main.rs
    └── ...
```

## Manifest Schema (manifest.json)

```json
{
  "schema_version": "1.0",
  "root_2i_seed_fingerprint": "<SHA-256 hex of seed file>",
  "created_at": "<ISO 8601 timestamp>",
  "source_root": "<informational path>",
  "files": {
    "<relative_path>": {
      "sha256": "<SHA-256 hex of file content>",
      "size": <bytes>
    }
  },
  "pack_hash": "<SHA-256 of sorted path:hash entries>"
}
```

### Pack Hash Computation

The `pack_hash` is computed as:

```
SHA-256(concat for each (path, entry) in sorted files:
    path_bytes + ":" + sha256_hex + "\n"
)
```

Files are sorted lexicographically by path (guaranteed by BTreeMap).

## Gates

| Gate | Required | Description |
|------|----------|-------------|
| G0_SCHEMA | Yes | Manifest schema version is "1.0" |
| G1_INTEGRITY | Yes | pack_hash matches recomputed hash |
| G3_PINNING | Yes | Every file hash matches data/ content |
| G4_SEED_BINDING | Yes | Seed fingerprint matches loaded seed |
| G6_ORGASYSTEM_SHAPE | Yes | File count recorded |
| G7_RELEASE_RECEIPT | Yes | Receipt file written |

## Invariants

- File paths are preserved verbatim (no normalization).
- Unfurl restores identical directory tree shape.
- Any gate failure causes the operation to FAIL CLOSED.
- Seed binding is mandatory for all operations.
