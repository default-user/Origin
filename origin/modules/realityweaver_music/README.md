# RealityWeaverMusic (RXM1)

Reality Weaver Music container format for musical score data with optional
synchronized audio.

## Attribution: Ande → Kai
## License: WCL-1.0

## Features

- **RXM1 container** with META, SCOR, SYNC, and AUDI chunks
- **Score-only mode**: MIDI data compressed with RWV1
- **Score+audio mode**: Score + audio + monotonic sync map
- **RWV1 codec racing**: zlib, MO+zlib, bz2, lzma compression
- **SHA-256 integrity** verification
- **Forward compatibility**: unknown chunks preserved during roundtrip
- **Fail-closed**: invalid inputs produce errors, never silent corruption

## Quick Start

```bash
# Pack a score-only container
rxm pack --score piece.mid -o piece.rxm

# Pack with audio and sync
rxm pack --score piece.mid --audio recording.wav --sync sync.json -o piece.rxm

# Validate a container
rxm validate piece.rxm

# Show container info
rxm info piece.rxm

# Unpack to directory
rxm unpack piece.rxm -o output/

# Run self-tests
rxm selftest
```

## Architecture

RXM1 reuses the RealityWeaver (RWV1) compression library for SCOR and AUDI
chunk payloads. This provides block-based codec racing without duplicating
compression infrastructure.

See [SPEC.md](SPEC.md) for the full binary format specification.
