# RWV-VIDEO-V1 Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0
**Status**: Skeleton (TODO items for production)

## Overview

RWV-VIDEO-V1 is a video container format storing encoded segments with decision provenance for audit and re-weaving.

## Pipeline Architecture

```
Decode → Segment → WeaveRace → Gate → Select → Package
```

| Stage | Description |
|-------|-------------|
| Decode | Extract frames from input |
| Segment | Split by strategy (scene/fixed/adaptive) |
| WeaveRace | Encode with multiple codecs |
| Gate | Check perceptual quality |
| Select | Choose smallest passing result |
| Package | Combine into container |

## Container Format (Interim)

```
┌──────────────────────────────────┐
│ Magic: "RWVV" (4 bytes)          │
│ Version: 1 (1 byte)              │
│ Reserved: 0 (3 bytes)            │
│ Segment Count (4 bytes, BE)      │
│ Index Length (8 bytes, BE)       │
│ Source Info Length (4 bytes, BE) │
│ Source Info (JSON)               │
├──────────────────────────────────┤
│ Index (JSONL)                    │
│   One JSON object per line       │
├──────────────────────────────────┤
│ Payload Blob                     │
│   Concatenated segment data      │
└──────────────────────────────────┘
```

TODO: Define stable binary layout for production.

## Segment Record

```json
{
  "segment_id": 0,
  "time_range": [0.0, 4.0],
  "encoder_id": "x265",
  "encoder_params": {"preset": "medium", "crf": 20},
  "metrics": {"vmaf": 96.5, "psnr": 47.2, "ssim": 0.997},
  "payload_offset": 0,
  "payload_size": 1234567
}
```

## Perceptual Quality Gates

### Visually Lossless Definition

```
VISUALLY_LOSSLESS ≡ (VMAF ≥ 95) OR (PSNR ≥ 45 AND SSIM ≥ 0.995)
```

### Threshold Tiers

| Tier | VMAF | PSNR | SSIM |
|------|------|------|------|
| Lossless | ≥95 | ≥45dB | ≥0.995 |
| High | ≥90 | ≥40dB | ≥0.99 |
| Acceptable | ≥85 | ≥35dB | ≥0.98 |

## Segmentation Strategies

| Strategy | Description |
|----------|-------------|
| FIXED_DURATION | Fixed time intervals (default 4s) |
| SCENE_CUT | Cut at scene boundaries |
| MOTION_ADAPTIVE | Adapt to content complexity |

## Supported Encoders

| ID | Codec | Notes |
|----|-------|-------|
| x264 | H.264/AVC | Software |
| x265 | H.265/HEVC | Software |
| svt-av1 | AV1 | Software |
| vp9 | VP9 | Software |
| nvenc-h264 | H.264 | NVIDIA GPU |
| nvenc-hevc | H.265 | NVIDIA GPU |

## Fail-Soft Behavior

| Failure | Response |
|---------|----------|
| Encoder timeout | Use fallback branch |
| Metric failure | Escalate quality (reduce CRF) |
| Realtime overrun | Use fast preset |
| All fail | Error with diagnostic |

## Threat Model

### Risks
1. Hallucinated detail from upscaling
2. Temporal inconsistency
3. Over-sharpening
4. Metric gaming

### Mitigations
1. Conservative thresholds
2. Multi-metric gates
3. Segment independence
4. Full provenance

## TODO

- [ ] Stable binary container format
- [ ] Full ffmpeg integration
- [ ] Full gstreamer integration
- [ ] VMAF computation
- [ ] Scene-cut detection
- [ ] Motion-adaptive segmentation

## Reference

See `origin/modules/realityweaver_video/` for implementation.
