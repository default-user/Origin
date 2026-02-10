# RXM1 Container Format Specification

## Attribution: Ande → Kai
## License: WCL-1.0

---

## 1. Overview

RXM1 (Reality Weaver Music, version 1) is a chunk-based binary container for
musical score data with optional synchronized audio. It reuses RealityWeaver's
RWV1 compression for payload chunks.

### 1.1 Modes

| Mode | Required Chunks | Description |
|------|----------------|-------------|
| SCORE_ONLY | META, SCOR | Musical score without audio |
| SCORE_PLUS_AUDIO | META, SCOR, SYNC, AUDI | Score with synchronized audio |

### 1.2 Design Principles

- **Reuse**: SCOR and AUDI chunks are compressed with RWV1 codec racing
- **Determinism**: No RNG, no timestamps, reproducible packing
- **Fail-closed**: Invalid magic, missing chunks, bad sync → error
- **Forward-compatible**: Unknown chunk types are preserved during roundtrip

---

## 2. Binary Format

### 2.1 Header (8 bytes fixed)

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0-3 | 4 | magic | "RXM1" (0x52 0x58 0x4D 0x31) |
| 4 | 1 | version | 1 |
| 5 | 1 | flags | Bitfield (see below) |
| 6-7 | 2 | chunk_count | u16 big-endian |

#### Flags

| Bit | Mask | Meaning |
|-----|------|---------|
| 0 | 0x01 | SHA-256 integrity hash present |
| 1 | 0x02 | Audio data present (AUDI chunk) |
| 2 | 0x04 | Sync map present (SYNC chunk) |

### 2.2 Optional SHA-256 (32 bytes)

Present if flags & 0x01. Contains SHA-256 hash of all concatenated chunk data
(not including chunk headers). Used for integrity verification.

### 2.3 Chunk Table

Immediately follows the header (and optional SHA-256). Repeated `chunk_count` times:

| Offset | Size | Field | Description |
|--------|------|-------|-------------|
| 0-3 | 4 | chunk_type | FourCC identifier |
| 4-7 | 4 | chunk_size | u32 big-endian, size of chunk data |
| 8+ | var | chunk_data | Raw chunk data bytes |

---

## 3. Chunk Types

### 3.1 META (Metadata)

JSON-encoded metadata. Stored uncompressed for human inspectability.

```json
{
  "title": "string",
  "composer": "string",
  "tempo_bpm": 120.0,
  "time_signature": "4/4",
  "key_signature": "C",
  "description": "string",
  "score_format": "midi",
  "audio_format": "wav"
}
```

### 3.2 SCOR (Score)

Musical score data (MIDI format recommended) compressed with RWV1.

The raw bytes are passed through `realityweaver.compress_bytes()` which applies
block-based codec racing (zlib, MO+zlib, bz2, lzma).

To decode: pass chunk data through `realityweaver.decompress_bytes()`.

### 3.3 SYNC (Synchronization Map)

Binary array of (score_tick, audio_frame) anchor pairs for synchronizing
score playback with audio.

| Offset | Size | Field |
|--------|------|-------|
| 0-3 | 4 | entry_count (u32 big-endian) |
| 4+ | 8*N | entries: (score_tick u32 BE, audio_frame u32 BE) |

**Constraint**: Both `score_tick` and `audio_frame` sequences MUST be strictly
monotonically increasing. Non-monotonic maps are rejected during both packing
and validation.

### 3.4 AUDI (Audio)

Raw audio data compressed with RWV1 (same codec racing as SCOR).

---

## 4. Validation Rules (Fail-Closed)

1. Magic must be "RXM1"
2. Version must be 1
3. META and SCOR chunks are always required
4. If flags indicate audio (bit 1), AUDI chunk must be present
5. If flags indicate sync (bit 2), SYNC chunk must be present
6. If AUDI chunk is present, SYNC chunk must also be present
7. SYNC entries must be strictly monotonically increasing
8. If SHA-256 is present, it must match computed hash of all chunk data
9. Unknown chunk types are NOT errors (forward compatibility)

---

## 5. Compression Details

Both SCOR and AUDI chunks store their data as complete RWV1 containers:
- The raw bytes are input to `compress_bytes(data, config)`
- The resulting RWV1 container bytes are stored as the chunk data
- Decompression reverses this: `decompress_bytes(chunk_data)` returns original

This means each chunk internally contains:
- RWV1 header (magic, version, flags, block_size, block_count)
- Per-block codec selections (race-compressed)
- The full RWV1 decompression pipeline is used for extraction

---

## 6. Sync Helpers

Two conversion functions are provided for tick/frame mapping:

- `tick_to_frame(sync_entries, tick)` → audio frame (linear interpolation)
- `frame_to_tick(sync_entries, frame)` → score tick (linear interpolation)

Both clamp to the first/last anchor point for out-of-range inputs.

---

## 7. CLI Commands

| Command | Description |
|---------|-------------|
| `rxm validate <file>` | Validate container structure and integrity |
| `rxm info <file>` | Display container metadata and chunk summary |
| `rxm pack --score <midi> [--audio <wav>] [--sync <json>] -o <out.rxm>` | Create container |
| `rxm unpack <file> -o <dir>` | Extract all chunks to directory |
| `rxm selftest` | Run built-in self-tests |
