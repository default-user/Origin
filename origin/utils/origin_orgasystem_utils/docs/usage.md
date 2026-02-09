# originctl Usage

## Quick Start

```bash
# One-command end-to-end: pack -> compress -> decompress -> verify
cargo run --bin originctl -- e2e --repo-root . --seed spec/seed/denotum.seed.2i.yaml

# Or with a release build:
make release
./target/release/originctl e2e --repo-root . --seed spec/seed/denotum.seed.2i.yaml
```

## Commands

### Pack

Snapshot a repository into a DPACK:

```bash
originctl pack --repo-root /path/to/repo -o /path/to/pack
```

### Compress

Compress a DPACK directory into a single .cpack file:

```bash
originctl compress /path/to/dpack -o output.cpack
```

### Decompress

Decompress a .cpack file back into a DPACK directory:

```bash
originctl decompress output.cpack -o /path/to/dpack
```

### Verify

Verify a DPACK directory or CPACK file (auto-detected):

```bash
# DPACK directory
originctl verify /path/to/dpack --seed seed.yaml

# CPACK file
originctl verify output.cpack --seed seed.yaml
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

### E2E

Run the full end-to-end pipeline (pack -> compress -> decompress -> verify):

```bash
originctl e2e --repo-root /path/to/repo --seed seed.yaml
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

## Development

```bash
make all       # fmt + clippy + test + e2e
make test      # cargo test --workspace
make clippy    # cargo clippy --workspace --all-targets -- -D warnings
make e2e       # run e2e smoke test
make release   # build release binary
```
