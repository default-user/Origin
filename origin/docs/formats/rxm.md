# RXM (Reality Weaver Music) Format Documentation

## Attribution: Ande → Kai
## License: WCL-1.0

---

## Overview

RXM1 is a chunk-based binary container for musical score data with optional
synchronized audio. It is part of the RealityX Weaver suite and reuses the
RealityWeaver (RWV1) compression library for payload compression.

## Format Identifier

| Property | Value |
|----------|-------|
| Magic | `RXM1` (0x52 0x58 0x4D 0x31) |
| Version | 1 |
| Extension | `.rxm` |
| MIME type | `application/x-realityweaver-music` |

## Modes

### Score-Only

Contains musical score data (MIDI) compressed with RWV1 codec racing.
Requires: `META` + `SCOR` chunks.

### Score + Synced Audio

Contains score, compressed audio, and a synchronization map linking
score ticks to audio frames.
Requires: `META` + `SCOR` + `SYNC` + `AUDI` chunks.

## Chunk Summary

| Chunk | FourCC | Compression | Description |
|-------|--------|-------------|-------------|
| Metadata | `META` | None (JSON) | Title, composer, tempo, time signature |
| Score | `SCOR` | RWV1 | MIDI score data |
| Sync | `SYNC` | None (binary) | Monotonic (tick, frame) anchor pairs |
| Audio | `AUDI` | RWV1 | Raw audio data |

## Compression

SCOR and AUDI chunks are compressed using the RealityWeaver (RWV1) container
format, which provides block-based codec racing across:
- zlib (deflate)
- MO+zlib (middle-out dictionary rewrite + zlib)
- bz2 (optional)
- lzma (optional)

The smallest result wins per block, providing adaptive compression without
manual codec selection.

## Integrity

Optional SHA-256 hash covers all concatenated chunk data. When present,
the hash is verified during unpacking and validation, providing
tamper/corruption detection.

## CLI Usage

```
rxm validate <file.rxm>       # Validate container
rxm info <file.rxm>           # Show metadata and chunk summary
rxm pack --score <f> -o <f>   # Create score-only container
rxm pack --score <f> --audio <f> --sync <f> -o <f>  # With audio
rxm unpack <file.rxm> -o <dir>  # Extract to directory
rxm selftest                   # Built-in self-tests
```

## Relationship to Other Formats

| Format | Relationship |
|--------|-------------|
| RWV1 | RXM uses RWV1 for SCOR and AUDI chunk compression |
| PWV1 | Independent (PhraseWeave for text encoding) |
| PWOF | Independent (ProofWeave for formal proofs) |
| RWVV | Sibling (RealityWeaverVideo for video segments) |

## See Also

- [RXM Specification](../../modules/realityweaver_music/SPEC.md)
- [RXM Implementation Plan](rxm_plan.md)
- [RWV1 Container Spec](../../modules/realityweaver/SPEC.md)
