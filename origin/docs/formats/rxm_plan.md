# RXM (Reality Weaver Music) - Discovery Report & Implementation Plan

## Attribution: Ande → Kai
## License: WCL-1.0

---

## 1. Discovery Summary

### 1.1 Existing Format Implementations Found

| Module | Path | Magic | Status |
|--------|------|-------|--------|
| RealityWeaver | `modules/realityweaver/` | `RWV1` | Production |
| PhraseWeave | `modules/phraseweave/` | `PWV1` / `PWDC` | Production |
| ProofWeave | `modules/proofweave/` | `PWOF` | Production |
| RealityWeaverVideo | `modules/realityweaver_video/` | `RWVV` | Skeleton |

### 1.2 RXA Status

**No `.rxa` format was found in the repository.** The closest audio-related code is
RealityWeaverVideo, which handles video segments but not standalone audio. The RWV1
container provides the best reusable compression infrastructure.

### 1.3 Reusable Container Primitives (from RWV1)

| Primitive | Location | Reuse Strategy |
|-----------|----------|----------------|
| 4-byte magic + version + flags header | `realityweaver/src/types.py` | Adopt pattern: `RXM1` magic |
| Block-based codec racing | `realityweaver/src/container.py` | Use `compress_bytes`/`decompress_bytes` for SCOR and AUDI chunk payloads |
| SHA-256 integrity | `realityweaver/src/container.py` | Whole-container SHA-256 option |
| BranchID codec selection | `realityweaver/src/types.py` | Inherited via RWV1 compression |
| MO+zlib dictionary rewrite | `realityweaver/src/mo_zlib.py` | Inherited via RWV1 compression |
| Fail-closed error pattern | All modules | Adopt same pattern |
| CLI argparse subcommands | `realityweaver/src/cli.py` | Mirror structure |
| Module structure | `src/`, `tests/`, `setup.py` | Mirror exactly |

### 1.4 Integration Points

- **`modules/weaver.py`**: Central module registry - will add `realityweaver_music` entry
- **`WEAVER_MODULES`**: Format registration dict - will add `RXM1` format

---

## 2. RXM Container Specification (RXM1)

### 2.1 Format Overview

RXM1 is a chunk-based music container supporting two modes:
- **SCORE_ONLY**: Musical score data (MIDI) compressed with RWV1
- **SCORE_PLUS_SYNCED_AUDIO**: Score + compressed audio + synchronization map

### 2.2 Binary Layout

```
HEADER (8 bytes):
  Offset  Size  Field
  ------  ----  -----
  0       4     Magic: "RXM1" (0x52 0x58 0x4D 0x31)
  4       1     Version: 1
  5       1     Flags: bit0=has_sha256, bit1=has_audio, bit2=has_sync
  6       2     Chunk count (u16 big-endian)

  [SHA-256: 32 bytes, present if flags & 0x01]

CHUNK TABLE (repeated chunk_count times):
  Offset  Size  Field
  ------  ----  -----
  0       4     Chunk type (FourCC: META, SCOR, SYNC, AUDI)
  4       4     Chunk data size (u32 big-endian)
  8       var   Chunk data (bytes[size])
```

### 2.3 Chunk Types

| FourCC | Required | Description |
|--------|----------|-------------|
| `META` | Yes | JSON metadata (title, composer, tempo, time signature, etc.) |
| `SCOR` | Yes | Score payload - raw MIDI bytes compressed via RWV1 |
| `SYNC` | If AUDI | Synchronization map: array of (score_tick, audio_frame) pairs |
| `AUDI` | No | Audio payload - raw audio bytes compressed via RWV1 |

### 2.4 Sync Model

The SYNC chunk contains an array of anchor pairs:
```
SYNC_ENTRY_COUNT: u32 big-endian
For each entry:
  SCORE_TICK:  u32 big-endian
  AUDIO_FRAME: u32 big-endian
```

**Constraint**: Both score_tick and audio_frame sequences must be strictly
monotonically increasing. Validation rejects non-monotonic maps.

### 2.5 Compression Strategy

- `SCOR` chunk: Raw MIDI bytes → `realityweaver.compress_bytes()` → stored
- `AUDI` chunk: Raw audio bytes → `realityweaver.compress_bytes()` → stored
- `META` chunk: JSON bytes stored uncompressed (small, human-inspectable)
- `SYNC` chunk: Binary pairs stored uncompressed (small, fixed-size)

This directly reuses RWV1's codec racing (zlib vs MO+zlib vs bz2 vs lzma).

---

## 3. Minimal Diff Plan

### Files to ADD:

```
modules/realityweaver_music/
├── README.md
├── SPEC.md
├── setup.py
├── src/
│   ├── __init__.py
│   ├── types.py          # RXM1 constants, config, chunk types
│   ├── container.py      # Pack/unpack/validate/info using RWV1 compression
│   └── cli.py            # CLI: validate, info, pack, unpack
└── tests/
    └── test_rxm.py       # Roundtrip, sync validation, error handling

docs/formats/
├── rxm_plan.md           # This file (discovery report)
└── rxm.md                # Format documentation

samples/rxm/
├── score_only_example.rxm
└── score_plus_audio_example.rxm
```

### Files to MODIFY:

```
modules/weaver.py          # Add realityweaver_music to WEAVER_MODULES registry
```

### Files NOT modified:

All existing modules remain untouched. RXM depends on RWV1's `compress_bytes`
and `decompress_bytes` as a library - no changes to RWV1 source required.

---

## 4. Acceptance Criteria

1. RXM uses existing RWV1 container compression (proved by import chain)
2. RXA remains unchanged (it does not exist; no files modified)
3. Unknown chunks are preserved during pack/unpack (forward compatibility)
4. Score-only mode roundtrips correctly
5. Score+audio mode roundtrips correctly with sync validation
6. Non-monotonic sync maps are rejected (fail-closed)
7. Invalid magic / truncated data / missing required chunks → error
8. All tests pass
9. Build succeeds
