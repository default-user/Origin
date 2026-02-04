# PWV1 Woven Format Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## Overview

PWV1 is PhraseWeave's reversible byte transformation format using dictionary-based encoding.

## Core Invariant

```
unweave(weave(x)) == x for all valid x
```

## Binary Layout

### Header (38 bytes fixed)

| Offset | Size | Type | Field | Description |
|--------|------|------|-------|-------------|
| 0 | 4 | bytes | magic | "PWV1" (0x50 0x57 0x56 0x31) |
| 4 | 1 | u8 | version | Format version (1) |
| 5 | 1 | u8 | flags | Reserved (0x00 for v1) |
| 6 | 32 | bytes | dict_id | SHA-256 of canonical dictionary |

### Token Stream

Following the header until EOF:

| Token Type | Value | Format | Description |
|------------|-------|--------|-------------|
| LITERAL | 0x00 | `[0x00][byte]` | Single literal byte |
| STAN | 0x01 | `[0x01][varint]` | Dictionary entry reference |
| PHRASE | 0x02 | `[0x02][varint][varint]` | Multi-Stan phrase |
| REPEAT | 0x03 | `[0x03][varint]` | Repeat previous expansion |

### Varint Encoding

Unsigned LEB128 (Little-Endian Base 128):
- 7 bits per byte, high bit indicates continuation
- Example: 300 = [0xAC, 0x02]

## Dictionary ID Computation

The 32-byte dictionary ID is computed as:

```python
hasher = sha256()
for stan_id in sorted(entries.keys()):
    hasher.update(pack(">I", stan_id))      # 4 bytes, big-endian
    hasher.update(pack(">I", len(raw_form))) # 4 bytes, big-endian
    hasher.update(raw_form)
return hasher.digest()
```

## Decoding Algorithm

```
1. Verify len(data) >= 38
2. Verify magic == "PWV1"
3. Verify version == 1
4. Read dict_id from bytes 6-38
5. Compute expected_dict_id from provided dictionary
6. FAIL if dict_id != expected_dict_id
7. output = []
8. last_expansion = None
9. pos = 38
10. While pos < len(data):
    a. token_type = data[pos]; pos += 1
    b. Switch token_type:
       - LITERAL: output.append(data[pos]); pos += 1; last_expansion = [data[pos-1]]
       - STAN: id = read_varint(); output.extend(dictionary[id]); last_expansion = dictionary[id]
       - PHRASE: id, len = read_varints(); expand phrase; last_expansion = expansion
       - REPEAT: count = read_varint(); output.extend(last_expansion * count)
11. Return bytes(output)
```

## Test Vector

### Vector 1: Empty Input, Empty Dictionary

**Input**: empty bytes
**Dictionary**: empty (dict_id = sha256(""))

**Expected Output** (38 bytes):
```
50 57 56 31                                   # "PWV1"
01                                            # version 1
00                                            # flags 0
e3 b0 c4 42 98 fc 1c 14 9a fb f4 c8 99 6f b9 24
27 ae 41 e4 64 9b 93 4c a4 95 99 1b 78 52 b8 55  # sha256(empty)
```

## Error Handling

All errors are fail-closed:
- Invalid magic → error
- Version mismatch → error
- Dictionary ID mismatch → error
- Unknown stan_id → error
- REPEAT with no previous → error
- Output exceeds max_output_size → error

## Reference

See `origin/modules/phraseweave/` for implementation.
