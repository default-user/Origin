# RealityWeaver Specification (RWV1)

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## 1. Overview

RealityWeaver is a block-based compression container format with adaptive codec racing.

### Core Invariant

```
decompress(compress(x)) == x for all valid x
```

## 2. RWV1 Container Format

### 2.1 Header

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | bytes | Magic: "RWV1" |
| 4 | 1 | u8 | Version: 1 |
| 5 | 1 | u8 | Flags |
| 6 | 4 | u32 BE | Block size |
| 10 | 4 | u32 BE | Block count |
| 14 | 32 | bytes | Optional: raw_sha256 (if flags & 0x01) |

### 2.2 Flags

| Bit | Meaning |
|-----|---------|
| 0 | raw_sha256_present |
| 1-7 | Reserved (must be 0) |

### 2.3 Block Records

Immediately following the header, repeated `block_count` times:

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 1 | u8 | Branch ID |
| 1 | 4 | u32 BE | Raw length (original) |
| 5 | 4 | u32 BE | Payload length |
| 9 | var | bytes | Payload data |

## 3. Branch IDs

| ID | Name | Description |
|----|------|-------------|
| 0 | ZLIB | zlib (deflate) compression |
| 1 | MO_ZLIB | Middle-out dictionary + zlib |
| 2 | BZ2 | bzip2 compression |
| 3 | LZMA | lzma/xz compression |

## 4. Decoding Algorithm

```
1. Read header (magic, version, flags, block_size, block_count)
2. FAIL if magic != "RWV1" or version != 1
3. If flags & 0x01:
   - Read 32-byte expected_sha256
4. Initialize output buffer
5. For each block:
   a. Read branch_id, raw_len, payload_len
   b. Read payload bytes
   c. Dispatch to branch decoder
   d. FAIL if decoded length != raw_len
   e. Append to output
6. If expected_sha256 present:
   - Compute sha256(output)
   - FAIL if mismatch
7. Return output
```

## 5. MO+zlib Payload Format

### 5.1 Layout

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 2 | u16 BE | Dictionary entry count |
| 2 | var | entries | Dictionary entries |
| var | 4 | u32 BE | Compressed data length |
| var | var | bytes | zlib-compressed token stream |

### 5.2 Dictionary Entry

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 1 | u8 | Token (1-255) |
| 1 | 2 | u16 BE | Phrase length |
| 3 | var | bytes | Phrase bytes |

### 5.3 Token Stream Rules

After zlib decompression of the token stream:

- If byte == 0 (TOKEN_RAW): next byte is literal
- If byte != 0: byte is dictionary token, expand to phrase

### 5.4 Dictionary Building (Canonical Behavior)

```
1. Collect n-gram candidates (min_len=3 to max_len=64)
2. Score each: count * (length - 1)
3. Filter to count >= 2
4. Sort by score descending
5. Assign tokens 1..255 to top candidates
6. Limit to max_entries (default 200)
```

TODO: Exact scoring formula may vary. Implementations should be deterministic.

## 6. Race Compressor Algorithm

```
1. Split input into blocks of block_size
2. For each block:
   a. For each enabled branch:
      - Encode block
      - Record (branch_id, payload, payload_len)
   b. Select smallest payload
   c. Store winning (branch_id, raw_len, payload)
3. Build container with header + block records
```

### 6.1 Tie-Breaking

When multiple branches produce same size:
- Choose branch with lowest ID (zlib < mo_zlib < bz2 < lzma)

### 6.2 Probe Gating (Optional)

When `probe=true`:
```
1. Analyze block content (text ratio)
2. If text_ratio > 0.7:
   - Try MO_ZLIB, ZLIB (in that order)
3. Else:
   - Try ZLIB, MO_ZLIB
```

This reduces encoding time by skipping unlikely-to-win branches.

## 7. Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| block_size | int | 1048576 | Block size in bytes |
| allow_zlib | bool | true | Enable zlib branch |
| allow_mo_zlib | bool | true | Enable MO+zlib branch |
| allow_bz2 | bool | false | Enable bz2 branch |
| allow_lzma | bool | false | Enable lzma branch |
| zlib_level | int | 9 | zlib compression level (1-9) |
| bz2_level | int | 9 | bz2 compression level (1-9) |
| lzma_preset | int | 6 | lzma preset (0-9) |
| mo_max_entries | int | 200 | Max MO dictionary entries |
| probe | bool | false | Enable probe gating |
| include_sha256 | bool | false | Store integrity hash |

## 8. Error Handling

All errors are **fail-closed**:

- Invalid magic → error
- Unsupported version → error
- Block size mismatch → error
- SHA-256 mismatch → error
- Unknown branch ID → error
- Truncated data → error
- Decompression failure → error

## 9. Determinism Requirements

- No RNG in encoding
- No timestamps
- Consistent dictionary building order
- Stable race winner selection
- Same input → same output bytes

## 10. CLI Commands

| Command | Description |
|---------|-------------|
| compress | Compress file to RWV1 container |
| decompress | Decompress RWV1 container |
| bench | Benchmark against baselines |
| info | Display container information |
| selftest | Run verification tests |

## 11. Attribution

Original design: Ande → Kai
Licensed under Weaver Commons License (WCL-1.0)
