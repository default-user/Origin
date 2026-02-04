# RWV1 Container Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## Overview

RWV1 is a block-based compression container format with per-block codec selection through competitive encoding (racing).

## Binary Layout

### Header

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 4 | bytes | magic | "RWV1" (0x52 0x57 0x56 0x31) |
| 4 | 1 | u8 | version | Container version (1) |
| 5 | 1 | u8 | flags | Bitfield (see below) |
| 6 | 4 | u32 BE | block_size | Size of each block in bytes |
| 10 | 4 | u32 BE | block_count | Number of blocks |

If `flags & 0x01` (raw_sha256_present):
| 14 | 32 | bytes | raw_sha256 | SHA-256 of original uncompressed data |

### Flags

| Bit | Name | Description |
|-----|------|-------------|
| 0 | raw_sha256_present | 32-byte SHA-256 hash follows header |
| 1-7 | reserved | Must be 0 |

### Block Records

Following the header (and optional SHA-256), repeated `block_count` times:

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 1 | u8 | branch_id | Codec identifier |
| 1 | 4 | u32 BE | raw_len | Original uncompressed size |
| 5 | 4 | u32 BE | payload_len | Compressed payload size |
| 9 | var | bytes | payload | Compressed block data |

### Branch IDs

| ID | Name | Description |
|----|------|-------------|
| 0 | ZLIB | Standard zlib/deflate compression |
| 1 | MO_ZLIB | Middle-out dictionary rewrite + zlib |
| 2 | BZ2 | bzip2 compression |
| 3 | LZMA | lzma/xz compression |

## MO+zlib Payload Format

When branch_id = 1, payload contains:

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 2 | u16 BE | dict_count | Number of dictionary entries |

For each dictionary entry:
| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 1 | u8 | token | Token value (1-255) |
| 1 | 2 | u16 BE | phrase_len | Phrase length |
| 3 | var | bytes | phrase | Phrase bytes |

After dictionary:
| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 4 | u32 BE | comp_len | Compressed token stream length |
| 4 | var | bytes | comp_data | zlib-compressed token stream |

### Token Stream

After zlib decompression:
- Byte 0 (TOKEN_RAW): next byte is literal
- Byte 1-255: dictionary token, expand to phrase

## Decoding Algorithm

```
1. Verify magic == "RWV1"
2. Verify version == 1
3. Read flags, block_size, block_count
4. If flags & 0x01: read expected_sha256
5. output = []
6. For i in 0..block_count:
   a. Read branch_id, raw_len, payload_len
   b. Read payload[payload_len]
   c. Decode payload using branch_id:
      - 0: zlib.decompress
      - 1: MO+zlib decode (see above)
      - 2: bz2.decompress
      - 3: lzma.decompress
   d. Verify len(decoded) == raw_len
   e. output.append(decoded)
7. result = concat(output)
8. If expected_sha256:
   Verify sha256(result) == expected_sha256
9. Return result
```

## Invariants

1. **Determinism**: Same input always produces same output
2. **Reversibility**: decompress(compress(x)) == x
3. **Integrity**: SHA-256 verification when present

## Reference

See `origin/modules/realityweaver/` for implementation.
