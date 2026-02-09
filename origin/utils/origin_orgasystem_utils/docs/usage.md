# originctl Usage

## Overview

`originctl` is the CLI tool for managing the Origin orgasystem: packing, verifying, unfurling, auditing, and replicating.

All operations are deterministic, fail-closed, and bound to the root 2I seed fingerprint.

## Commands

### Pack

Snapshot a repository into a DPACK:

```bash
originctl pack --repo-root /path/to/repo -o /path/to/pack
```

### Verify

Verify a DPACK's integrity, hashes, and seed binding:

```bash
originctl verify /path/to/pack
```

### Unfurl

Restore a DPACK to a target directory:

```bash
originctl unfurl /path/to/pack -o /path/to/target
```

### Audit

Audit a DPACK and output gate results:

```bash
originctl audit /path/to/pack --json
```

### Replicate

#### Local Clone (R0)

```bash
originctl replicate local --repo-root /path/to/repo -o /path/to/target
```

#### Rootball (R1)

```bash
originctl replicate rootball --repo-root /path/to/repo -o /path/to/rootball
```

#### Zip to Fresh Repo (R2, v1)

```bash
originctl replicate zip2repo-v1 --source /path/to/source --out-dir /path/to/new-repo --init-git
```

## Policy Files

Control which files are included/excluded via a YAML policy:

```yaml
include: []
exclude:
  - ".git/**"
  - ".git"
  - "*.env"
  - "node_modules/**"
```

Pass to commands with `--policy policy.yaml`.

## Seed Binding

All operations require the root 2I seed. By default, `originctl` looks for it at `spec/seed/denotum.seed.2i.yaml` relative to the repo root. Override with `--seed /path/to/seed.yaml`.
