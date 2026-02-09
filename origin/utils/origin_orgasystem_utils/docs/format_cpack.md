# CPACK Format Specification

## Version

1.0

## Overview

A CPACK (Compressed Pack) is a single-file compressed representation of a DPACK.
It uses zstd compression with a deterministic binary framing protocol and
SHA-256 integrity verification.

## File Format

```
Offset  Size    Field
------  ------  -----
0       4       Magic: "CPCK" (0x43 0x50 0x43 0x4B)
4       1       Version: 1
5       1       Compression method: 1 (zstd)
6       2       Reserved: 0x0000
8       32      SHA-256 of uncompressed payload
40      8       Compressed data length (u64 little-endian)
48      ...     Zstd compressed payload
```

## Payload Format (before compression)

```
Offset  Size    Field
------  ------  -----
0       4       Manifest JSON length (u32 LE)
4       N       Manifest JSON bytes (canonical form)
4+N     4       File count (u32 LE)

For each file (sorted by relative path):
  4       Path length (u32 LE)
  P       Path bytes (UTF-8)
  8       Content length (u64 LE)
  C       Content bytes
```

## Determinism Guarantees

1. **Manifest**: Serialized as canonical JSON (BTreeMap ensures sorted keys).
2. **File ordering**: Files sorted lexicographically by relative path.
3. **Byte order**: All integers are little-endian.
4. **Compression**: zstd level 3 (deterministic for identical input).
5. **No timestamps**: The CPACK itself contains no timestamps (manifest may).

## Round-Trip Invariant

```
decompress(compress(dpack)) == dpack
```

This is verified by:
1. Payload SHA-256 match after decompression
2. Manifest pack_hash match
3. Individual file content match

## Integrity Verification

1. Read header, check magic and version.
2. Decompress zstd payload.
3. Compute SHA-256 of decompressed payload.
4. Compare against stored hash in header.
5. If mismatch: FAIL CLOSED.

## CLI Usage

```bash
# Compress a DPACK directory to a .cpack file
originctl compress <dpack_dir> -o output.cpack

# Decompress a .cpack file back to a DPACK directory
originctl decompress output.cpack -o <dpack_dir>

# Verify a .cpack file (integrity + optional seed check)
originctl verify output.cpack --seed seed.yaml

# Full end-to-end: pack -> compress -> decompress -> verify
originctl e2e --repo-root . --seed spec/seed/denotum.seed.2i.yaml
```
