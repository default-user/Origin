# RealityWeaver Test Vectors

Test vectors for RWV1 container format verification.

## Vector Structure

Each vector contains:
- Input data (raw bytes)
- Configuration options
- Expected output properties

## Usage

```python
from realityweaver import compress_bytes, decompress_bytes

# Roundtrip test
data = bytes.fromhex(vector['input_hex'])
compressed = compress_bytes(data)
decompressed = decompress_bytes(compressed)
assert decompressed == data
```

## Vectors

### vector1_empty.json
Empty input should produce minimal valid container.

### vector2_text.json
Simple text compression demonstrating MO+zlib branch.

## Invariants to Verify

1. Magic bytes are "RWV1"
2. Version is 1
3. Roundtrip: decompress(compress(x)) == x
4. If SHA-256 present, it matches computed hash
5. Each block decodes to exact raw_len bytes
