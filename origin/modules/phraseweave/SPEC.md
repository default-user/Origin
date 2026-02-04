# PhraseWeave Specification (PWV1 + PWDC)

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## 1. Overview

PhraseWeave is a reversible byte transformation system. It consists of:

1. **PWV1**: Woven byte stream format
2. **PWDC**: Dictionary container format

### Core Invariant

```
unweave(weave(x)) == x for all valid x
```

This invariant is **mandatory** for all implementations.

## 2. PWV1 Woven Format

### 2.1 Header (38 bytes fixed)

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | bytes | Magic: "PWV1" (0x50 0x57 0x56 0x31) |
| 4 | 1 | u8 | Version: 1 |
| 5 | 1 | u8 | Flags: 0x00 for v1 |
| 6 | 32 | bytes | Dictionary ID (SHA-256 of canonical form) |

### 2.2 Token Stream

Following the header, tokens are emitted until EOF.

#### Token Types

| Type | Value | Format | Description |
|------|-------|--------|-------------|
| LITERAL | 0x00 | `[0x00][byte]` | Single literal byte |
| STAN | 0x01 | `[0x01][stan_id:varint]` | Dictionary entry reference |
| PHRASE | 0x02 | `[0x02][phrase_id:varint][length:varint]` | Multi-Stan phrase |
| REPEAT | 0x03 | `[0x03][count:varint]` | Repeat previous expansion |

#### Varint Encoding

Unsigned LEB128 (Little-Endian Base 128):

```
value < 128:      [value]
value < 16384:    [value & 0x7F | 0x80] [value >> 7]
...continue until high bit is 0
```

### 2.3 Decoding Algorithm

```
1. Read and verify header (magic, version, flags)
2. Read 32-byte DICT_ID
3. Compute expected DICT_ID from provided dictionary
4. FAIL if mismatch
5. Initialize output buffer
6. While not EOF:
   a. Read token_type byte
   b. Dispatch:
      - LITERAL: read next byte, append to output
      - STAN: read varint stan_id, lookup in dictionary, append raw_form
      - PHRASE: read phrase_id + length, expand phrase
      - REPEAT: repeat last expansion 'count' times
   c. Check max_output_size (fail-closed if exceeded)
7. Return output buffer
```

### 2.4 Encoding Algorithm

```
1. Write header (magic, version, flags, dictionary ID)
2. Build reverse index: raw_form -> stan_id
3. Sort patterns by length (descending) for greedy matching
4. Position = 0
5. While position < input_length:
   a. If greedy: try to match longest pattern first
   b. If matched: emit STAN token, advance by pattern length
   c. Else: emit LITERAL token, advance by 1
6. Return woven buffer
```

## 3. PWDC Dictionary Format

### 3.1 Header

| Offset | Size | Type | Description |
|--------|------|------|-------------|
| 0 | 4 | bytes | Magic: "PWDC" (0x50 0x57 0x44 0x43) |
| 4 | 1 | u8 | Version: 1 |
| 5 | 1 | u8 | Flags (see below) |
| 6 | 2 | u16 BE | Domain type |
| 8 | 4 | u32 BE | Entry count |
| 12 | 32 | bytes | Dictionary ID |

### 3.2 Flags

| Bit | Meaning |
|-----|---------|
| 0 | phrases_included |
| 1 | weights_included |
| 2 | frequency_included |

### 3.3 Entries (repeated entry_count times)

| Field | Type | Condition |
|-------|------|-----------|
| stan_id | varint | always |
| raw_len | varint | always |
| raw_form | bytes[raw_len] | always |
| weight | f32 BE | if weights_included |
| frequency | f32 BE | if frequency_included |

### 3.4 Phrase Entries (if phrases_included)

After all entries:

| Field | Type |
|-------|------|
| phrase_count | u32 BE |

For each phrase:

| Field | Type |
|-------|------|
| phrase_id | varint |
| stan_count | varint |
| stan_ids | varint[stan_count] |

### 3.5 Canonical Dictionary ID

The dictionary ID is computed as SHA-256 over:

```
for stan_id in sorted(entries.keys()):
    hash.update(pack(">I", stan_id))
    hash.update(pack(">I", len(raw_form)))
    hash.update(raw_form)
return hash.digest()
```

Note: Uses big-endian u32 for lengths (matches reference implementation).

## 4. Domain Types

| Value | Name | Description |
|-------|------|-------------|
| 0 | GENERAL | General-purpose |
| 1 | TEXT | Natural language text |
| 2 | CODE | Source code |
| 3 | BINARY | Binary data |
| 4 | STRUCTURED | Structured data (JSON, XML) |
| 255 | CUSTOM | Custom domain |

## 5. Configuration

### 5.1 Encoder Config

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| min_phrase_len | int | 2 | Minimum length for dictionary matching |
| max_phrase_len | int | 64 | Maximum length for dictionary matching |
| greedy | bool | true | Prefer longest matches |

### 5.2 Decoder Config

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| max_output_size | int? | None | Maximum output size (fail-closed) |

## 6. Error Handling

All errors are **fail-closed**:

- Invalid magic → error
- Version mismatch → error
- Dictionary ID mismatch → error
- Unknown stan_id → error
- REPEAT with no previous → error
- Output exceeds max_output_size → error
- Truncated data → error

## 7. Test Vectors

### Vector 1: Empty Input, Empty Dictionary

**Input**: `b''` (empty bytes)
**Dictionary**: empty
**Config**: defaults

**Expected Output** (38 bytes, hex):
```
50 57 56 31                                   # "PWV1"
01                                            # version
00                                            # flags
e3 b0 c4 42 98 fc 1c 14 9a fb f4 c8 99 6f b9 24
27 ae 41 e4 64 9b 93 4c a4 95 99 1b 78 52 b8 55  # sha256(empty)
```

**Explanation**: SHA-256 of empty canonical dictionary is SHA-256 of empty string.

## 8. Implementation Notes

### 8.1 Determinism Requirements

- No RNG
- No timestamps
- No host-dependent behavior
- Sorted iteration for dictionary
- Stable greedy matching order

### 8.2 Security Considerations

- Verify dictionary ID before decoding
- Enforce max_output_size to prevent bombs
- Fail-closed on all errors
- No arbitrary code execution from dictionary

## 9. Attribution

Original design: Ande → Kai
Licensed under Weaver Commons License (WCL-1.0)
