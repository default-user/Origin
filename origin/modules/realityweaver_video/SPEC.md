# RealityWeaverVideo Specification (RWV-VIDEO-V1)

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0
**Status**: Skeleton (TODO items for production)

## 1. Overview

RealityWeaverVideo is a video processing pipeline that:
- Segments video for parallel processing
- Races multiple encoders to find optimal compression
- Enforces perceptual quality gates
- Packages results with full decision provenance

## 2. Pipeline Architecture

### 2.1 Stages

```
Decode → Segment → WeaveRace → Gate → Select → Package
```

| Stage | Description | Invariants |
|-------|-------------|------------|
| Decode | Extract frames from input | Deterministic output |
| Segment | Split into processable units | Segment independence |
| WeaveRace | Encode with multiple codecs | Parallel execution |
| Gate | Verify perceptual quality | Fail-closed on metrics |
| Select | Choose best encoder result | Smallest passing result |
| Package | Combine into container | Lossless concatenation |

### 2.2 Invariants

1. **Deterministic decode**: Same input always produces same frames
2. **Segment independence**: Each segment processable independently
3. **Visually lossless default**: Output meets perceptual thresholds

## 3. Segmentation

### 3.1 Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| FIXED_DURATION | Fixed time intervals | General purpose |
| SCENE_CUT | Cut at scene boundaries | High quality |
| MOTION_ADAPTIVE | Adapt to content complexity | Bandwidth optimization |

### 3.2 Parameters

| Parameter | Default | Range | Description |
|-----------|---------|-------|-------------|
| segment_duration | 4.0s | 1-10s | Duration for FIXED_DURATION |
| min_segment_duration | 1.0s | 0.5-5s | Minimum segment length |
| max_segment_duration | 10.0s | 5-60s | Maximum segment length |

## 4. Perceptual Quality Gates

### 4.1 Metrics

| Metric | Description | Range |
|--------|-------------|-------|
| VMAF | Video Multimethod Assessment Fusion | 0-100 |
| PSNR | Peak Signal-to-Noise Ratio | 0-∞ dB |
| SSIM | Structural Similarity Index | 0-1 |

### 4.2 Visually Lossless Definition

```
VISUALLY_LOSSLESS ≡ (VMAF ≥ 95) OR (PSNR ≥ 45 AND SSIM ≥ 0.995)
```

### 4.3 Threshold Tiers

| Tier | VMAF | PSNR | SSIM | Use Case |
|------|------|------|------|----------|
| Lossless | ≥95 | ≥45dB | ≥0.995 | Archival |
| High | ≥90 | ≥40dB | ≥0.99 | Premium |
| Acceptable | ≥85 | ≥35dB | ≥0.98 | Standard |

### 4.4 Gate Behavior

- **Pass**: Output segment to Package stage
- **Fail + escalate_on_gate_fail**: Re-encode with lower CRF
- **Fail + !escalate_on_gate_fail**: Warn and continue

## 5. Encoder Racing

### 5.1 Supported Encoders

| ID | Encoder | Codec |
|----|---------|-------|
| x264 | libx264 | H.264/AVC |
| x265 | libx265 | H.265/HEVC |
| svt-av1 | SVT-AV1 | AV1 |
| vp9 | libvpx-vp9 | VP9 |
| nvenc-h264 | NVENC | H.264 (GPU) |
| nvenc-hevc | NVENC | H.265 (GPU) |

### 5.2 Race Algorithm

```
for segment in segments:
    candidates = []
    for encoder in enabled_encoders:
        result = encode(segment, encoder)
        metrics = compute_metrics(segment.source, result)
        if passes_gate(metrics):
            candidates.append((result, metrics, size))

    if candidates:
        winner = min(candidates, key=lambda x: x.size)
    else:
        # Fail-soft: escalate quality
        winner = encode_with_escalation(segment)

    output.append(winner)
```

## 6. Container Format (RWV-VIDEO-V1)

### 6.1 Structure (Interim)

```
┌─────────────────────────────────────────────┐
│ Magic: "RWVV" (4 bytes)                     │
│ Version: 1 (1 byte)                         │
│ Reserved: 0 (3 bytes)                       │
│ Segment Count (4 bytes, big-endian)         │
│ Index Length (8 bytes, big-endian)          │
│ Source Info Length (4 bytes, big-endian)    │
│ Source Info JSON                            │
├─────────────────────────────────────────────┤
│ Index (JSONL)                               │
│   {"segment_id":0, "time_range":[0,4], ...} │
│   {"segment_id":1, "time_range":[4,8], ...} │
│   ...                                       │
├─────────────────────────────────────────────┤
│ Payload Blob                                │
│   [segment 0 data][segment 1 data]...       │
└─────────────────────────────────────────────┘
```

TODO: Define stable binary layout for production.

### 6.2 Segment Record Schema

```json
{
  "segment_id": 0,
  "time_range": [0.0, 4.0],
  "encoder_id": "x265",
  "encoder_params": {
    "preset": "medium",
    "crf": 20
  },
  "metrics": {
    "vmaf": 96.5,
    "psnr": 47.2,
    "ssim": 0.997
  },
  "payload_offset": 0,
  "payload_size": 1234567
}
```

## 7. Failure Modes

### 7.1 Fail-Soft Design

| Failure | Response |
|---------|----------|
| Encoder timeout | Use fallback branch |
| Metric failure | Escalate quality (reduce CRF) |
| Realtime overrun | Use fast preset |
| All encoders fail | Error with diagnostic |

### 7.2 Always Produce Output

The pipeline should never fail silently. Either:
1. Produce valid output, or
2. Return explicit error with diagnostic info

## 8. Threat Model

### 8.1 Identified Risks

1. **Hallucinated detail**: Upscaling introduces false information
2. **Temporal inconsistency**: Independent segment processing causes flicker
3. **Over-sharpening**: Enhancement artifacts
4. **Metric gaming**: Encoder optimizes for metrics, not visual quality

### 8.2 Mitigations

1. Conservative default thresholds (VMAF ≥ 95)
2. Multi-metric gates (VMAF OR PSNR+SSIM)
3. Segment-level verification
4. Deterministic decode verification
5. Full provenance for audit

## 9. Test Scenarios

### 9.1 SD → 4K Archival

```json
{
  "input_resolution": [720, 480],
  "output_resolution": [3840, 2160],
  "quality_preset": "archival",
  "expected_vmaf": 95
}
```

### 9.2 HD → 8K Premium

```json
{
  "input_resolution": [1920, 1080],
  "output_resolution": [7680, 4320],
  "quality_preset": "premium",
  "expected_vmaf": 93
}
```

### 9.3 Realtime Broadcast

```json
{
  "input_resolution": [1920, 1080],
  "output_resolution": [3840, 2160],
  "quality_preset": "realtime",
  "expected_vmaf": 88,
  "max_latency_ms": 100
}
```

## 10. Configuration

### 10.1 PipelineConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| segmentation_strategy | enum | FIXED_DURATION | How to segment |
| segment_duration | float | 4.0 | Duration in seconds |
| enabled_encoders | list | [x264, x265] | Encoders to race |
| vmaf_threshold | float | 95.0 | VMAF gate threshold |
| psnr_threshold | float | 45.0 | PSNR gate threshold |
| ssim_threshold | float | 0.995 | SSIM gate threshold |
| escalate_on_gate_fail | bool | true | Re-encode on failure |
| fallback_crf_reduction | int | 4 | CRF reduction for escalation |
| max_parallel_segments | int | 4 | Parallelism level |

## 11. Plugin Interfaces

### 11.1 FFmpeg Filter

```c
// Filter registration
AVFilter ff_vf_rw_upscale = {
    .name = "rw_upscale",
    .description = "RealityWeaver video upscale",
    // ...
};
```

TODO: Full implementation.

### 11.2 GStreamer Element

```c
// Element registration
gst_element_register(plugin, "rwupscale", GST_RANK_NONE, TYPE);
```

TODO: Full implementation.

## 12. Attribution

Original design: Ande → Kai
Licensed under Weaver Commons License (WCL-1.0)
