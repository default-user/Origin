# PWDC Dictionary Format Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## Overview

PWDC (PhraseWeave Dictionary Container) is the binary format for PhraseWeave dictionaries.

## Binary Layout

### Header

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 4 | bytes | magic | "PWDC" (0x50 0x57 0x44 0x43) |
| 4 | 1 | u8 | version | Format version (1) |
| 5 | 1 | u8 | flags | Feature flags |
| 6 | 2 | u16 BE | domain | Domain type |
| 8 | 4 | u32 BE | entry_count | Number of entries |
| 12 | 32 | bytes | dict_id | Canonical dictionary ID |

### Flags

| Bit | Name | Description |
|-----|------|-------------|
| 0 | phrases_included | Multi-Stan phrase entries follow |
| 1 | weights_included | Each entry has float32 weight |
| 2 | frequency_included | Each entry has float32 frequency |
| 3-7 | reserved | Must be 0 |

### Domain Types

| Value | Name | Description |
|-------|------|-------------|
| 0 | GENERAL | General purpose |
| 1 | TEXT | Natural language text |
| 2 | CODE | Source code |
| 3 | BINARY | Binary data |
| 4 | STRUCTURED | JSON, XML, etc. |
| 255 | CUSTOM | Custom domain |

### Entry Records

Repeated `entry_count` times:

| Field | Type | Condition | Description |
|-------|------|-----------|-------------|
| stan_id | varint | always | Unique entry identifier |
| raw_len | varint | always | Length of raw form |
| raw_form | bytes | always | Raw byte form |
| weight | f32 BE | if weights_included | Entry weight |
| frequency | f32 BE | if frequency_included | Entry frequency |

### Phrase Records (if phrases_included)

After all entries:

| Field | Type | Description |
|-------|------|-------------|
| phrase_count | u32 BE | Number of phrases |

For each phrase:

| Field | Type | Description |
|-------|------|-------------|
| phrase_id | varint | Unique phrase identifier |
| stan_count | varint | Number of Stans in phrase |
| stan_ids | varint[] | Array of Stan IDs |

## Canonical ID Computation

```python
hasher = sha256()
for stan_id in sorted(entries.keys()):
    entry = entries[stan_id]
    hasher.update(struct.pack(">I", stan_id))
    hasher.update(struct.pack(">I", len(entry.raw_form)))
    hasher.update(entry.raw_form)
return hasher.digest()
```

## Varint Encoding

Unsigned LEB128 (Little-Endian Base 128).

## Verification

On load:
1. Read and parse all data
2. Compute canonical ID from entries
3. Verify computed ID matches stored dict_id
4. FAIL on mismatch

## Reference

See `origin/modules/phraseweave/` for implementation.
