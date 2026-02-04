# PhraseWeave (PWV1)

**Attribution: Ande → Kai**
**License: WCL-1.0**

PhraseWeave is a reversible byte transformation system using dictionary-based encoding.

## Core Invariant

```
unweave(weave(x)) == x for all valid x
```

This invariant is non-negotiable and must hold for any implementation.

## Features

- **PWV1**: Woven byte stream format with deterministic encoding
- **PWDC**: Binary dictionary format with canonical ID computation
- **Reversible**: Perfect roundtrip for all valid inputs
- **Deterministic**: Same input always produces same output (no RNG, no timestamps)

## Installation

```bash
cd origin/modules/phraseweave
pip install -e .
```

## Usage

### Python API

```python
from phraseweave import (
    phraseweave_encode,
    phraseweave_decode,
    Dictionary,
    Config,
)

# Create or load a dictionary
dictionary = Dictionary()
dictionary.add_entry(1, b'hello')
dictionary.add_entry(2, b'world')

# Encode
raw = b'hello world hello'
woven, metadata = phraseweave_encode(raw, dictionary)

print(f"Original: {len(raw)} bytes")
print(f"Woven: {len(woven)} bytes")
print(f"Stan tokens: {metadata.stan_count}")

# Decode
decoded = phraseweave_decode(woven, dictionary)
assert decoded == raw  # Always true for valid inputs
```

### CLI

```bash
# Encode a file
python -m phraseweave.cli encode input.txt output.pwv1 --dict dictionary.pwdc

# Decode a file
python -m phraseweave.cli decode output.pwv1 restored.txt --dict dictionary.pwdc

# Show file info
python -m phraseweave.cli info output.pwv1

# Run self-tests
python -m phraseweave.cli selftest
```

## File Formats

### PWV1 (Woven Stream)

38-byte header followed by token stream:

| Offset | Size | Field |
|--------|------|-------|
| 0 | 4 | Magic "PWV1" |
| 4 | 1 | Version (1) |
| 5 | 1 | Flags (0x00) |
| 6 | 32 | Dictionary ID (SHA-256) |

Token types:
- `0x00 LITERAL`: Single literal byte
- `0x01 STAN`: Dictionary entry reference (varint ID)
- `0x02 PHRASE`: Multi-Stan phrase (varint ID + length)
- `0x03 REPEAT`: Repeat previous expansion (varint count)

### PWDC (Dictionary)

Binary dictionary format with canonical ID computation for verification.

See [SPEC.md](SPEC.md) for complete format specification.

## Testing

```bash
cd origin/modules/phraseweave
python -m pytest tests/
```

## Test Vectors

### Vector 1: Empty Input, Empty Dictionary

Input: empty bytes
Dictionary: empty
Config: defaults

Expected output (hex):
```
50575631 01 00 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

Total: 38 bytes

## Configuration

| Parameter | Default | Description |
|-----------|---------|-------------|
| `min_phrase_len` | 2 | Minimum phrase length for dictionary matching |
| `max_phrase_len` | 64 | Maximum phrase length for dictionary matching |
| `greedy` | true | Use greedy (longest-first) matching |
| `max_output_size` | None | Maximum decoded output size (fail-closed) |

## Security Considerations

- Dictionary ID verification prevents using wrong dictionary
- `max_output_size` prevents decompression bombs
- Fail-closed on any format errors

## Determinism Guarantees

- No RNG used in encoding
- No timestamps or host-dependent behavior
- Dictionary canonical ID uses sorted iteration
- Same bytes in → same bytes out
