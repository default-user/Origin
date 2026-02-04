# RealityWeaver (RWV1)

**Attribution: Ande → Kai**
**License: WCL-1.0**

RealityWeaver is a block-based compression container with adaptive codec racing.

## Core Invariant

```
decompress(compress(x)) == x for all valid x
```

## Features

- **RWV1 Container Format**: Binary format with per-block codec selection
- **Race Compressor**: Runs multiple codecs in parallel, picks smallest result
- **MO+zlib Branch**: Middle-out dictionary rewrite for text-heavy data
- **Multiple Branches**: zlib, MO+zlib, bz2, lzma
- **SHA-256 Verification**: Optional integrity checking
- **Deterministic**: Same input always produces same output

## Installation

```bash
cd origin/modules/realityweaver
pip install -e .
```

## Usage

### Python API

```python
from realityweaver import (
    compress_bytes,
    decompress_bytes,
    RWV1Config,
)

# Simple compression
data = b"Hello, World! " * 1000
compressed = compress_bytes(data)
original = decompress_bytes(compressed)

# With configuration
config = RWV1Config(
    block_size=64 * 1024,      # 64 KiB blocks
    allow_bz2=True,            # Enable bz2 branch
    include_sha256=True,       # Add integrity check
)
compressed = compress_bytes(data, config)
```

### CLI

```bash
# Compress
realityweaver compress input.txt output.rwv --sha256

# Decompress
realityweaver decompress output.rwv restored.txt

# Benchmark
realityweaver bench input.txt

# Show container info
realityweaver info output.rwv

# Run self-tests
realityweaver selftest
```

## Container Format

### Header

| Field | Size | Description |
|-------|------|-------------|
| Magic | 4 | "RWV1" |
| Version | 1 | 1 |
| Flags | 1 | bit0 = has SHA-256 |
| Block Size | 4 | Big-endian u32 |
| Block Count | 4 | Big-endian u32 |
| SHA-256 | 32 | Optional, if flags & 1 |

### Block Records

Each block:
| Field | Size | Description |
|-------|------|-------------|
| Branch ID | 1 | Codec identifier |
| Raw Length | 4 | Original block size |
| Payload Length | 4 | Compressed size |
| Payload | var | Compressed data |

### Branch IDs

| ID | Name | Description |
|----|------|-------------|
| 0 | ZLIB | Standard zlib/deflate |
| 1 | MO_ZLIB | Middle-out + zlib |
| 2 | BZ2 | bzip2 |
| 3 | LZMA | lzma/xz |

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `block_size` | 1 MiB | Block size for splitting |
| `allow_zlib` | true | Enable zlib branch |
| `allow_mo_zlib` | true | Enable MO+zlib branch |
| `allow_bz2` | false | Enable bz2 branch |
| `allow_lzma` | false | Enable lzma branch |
| `zlib_level` | 9 | zlib compression level |
| `bz2_level` | 9 | bz2 compression level |
| `lzma_preset` | 6 | lzma preset |
| `mo_max_entries` | 200 | MO dictionary entries |
| `probe` | false | Enable probe gating |
| `include_sha256` | false | Store integrity hash |

## MO+zlib Branch

The Middle-Out branch builds a per-block phrase dictionary, rewrites data to tokens, then zlib compresses. Effective for repetitive text.

Token stream rules:
- `0x00` followed by byte = literal
- Non-zero byte = dictionary token

See [SPEC.md](SPEC.md) for payload format details.

## Determinism

All operations are fully deterministic:
- No RNG
- No timestamps
- Sorted dictionary building
- Race winner is smallest payload (ties broken by branch ID order)
