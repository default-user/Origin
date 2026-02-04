# RealityWeaverVideo (RWV-VIDEO-V1)

**Attribution: Ande → Kai**
**License: WCL-1.0**

RealityWeaverVideo is a video processing pipeline with auditable packaging and quality gates.

## Status: Skeleton Implementation

This module provides the framework and interfaces for video processing. Full functionality requires external dependencies (ffmpeg, gstreamer, VMAF) that are marked as TODO in the implementation.

## Pipeline Stages

```
Input Video
    │
    ▼
┌─────────┐
│ Decode  │  Extract frames from input
└────┬────┘
     │
     ▼
┌──────────┐
│ Segment  │  Split based on strategy
└────┬─────┘
     │
     ▼
┌───────────┐
│ WeaveRace │  Encode with multiple codecs
└────┬──────┘
     │
     ▼
┌────────┐
│  Gate  │  Check perceptual quality
└────┬───┘
     │
     ▼
┌────────┐
│ Select │  Choose best result
└────┬───┘
     │
     ▼
┌─────────┐
│ Package │  Create output container
└────┬────┘
     │
     ▼
Output Video + Manifest
```

## Features

- **Segment-based processing**: Parallel encoding of independent segments
- **Encoder racing**: Multiple encoders compete, best result wins
- **Perceptual quality gates**: VMAF, PSNR, SSIM thresholds
- **Decision provenance**: Full audit trail of encoding decisions
- **Fail-soft behavior**: Always produce output, escalate quality on failure

## Installation

```bash
cd origin/modules/realityweaver_video
pip install -e .
```

### Optional Dependencies

```bash
# For full functionality
sudo apt install ffmpeg  # or brew install ffmpeg
pip install vmaf  # if available
```

## Usage

### Python API

```python
from realityweaver_video import (
    VideoPipeline,
    PipelineConfig,
    SegmentationStrategy,
    EncoderConfig,
    EncoderID,
)

# Configure pipeline
config = PipelineConfig(
    segmentation_strategy=SegmentationStrategy.FIXED_DURATION,
    segment_duration=4.0,
    enabled_encoders=[
        EncoderConfig(EncoderID.X264, preset="slow", crf=18),
        EncoderConfig(EncoderID.X265, preset="medium", crf=20),
    ],
    vmaf_threshold=95.0,
)

# Run pipeline
pipeline = VideoPipeline(config)
result = pipeline.run("input.mp4", "output.mp4")

# Check results
if result.success:
    print(f"Processed {len(result.segments)} segments")
    print(f"Compression ratio: {result.compression_ratio:.2f}")
    result.save_manifest("manifest.json")
else:
    print(f"Error: {result.error}")
```

### Convenience Function

```python
from realityweaver_video.pipeline import run_pipeline

result = run_pipeline("input.mp4", "output.mp4")
```

## Segmentation Strategies

| Strategy | Description |
|----------|-------------|
| FIXED_DURATION | Fixed time intervals (default: 4s) |
| SCENE_CUT | Cut on scene changes (TODO) |
| MOTION_ADAPTIVE | Adapt to motion complexity (TODO) |

## Perceptual Quality Gates

Default thresholds for "visually lossless":

| Metric | Threshold |
|--------|-----------|
| VMAF | ≥ 95 |
| PSNR | ≥ 45 dB |
| SSIM | ≥ 0.995 |

Gate passes if: **VMAF ≥ 95** OR **(PSNR ≥ 45 AND SSIM ≥ 0.995)**

## Container Format (RWV-VIDEO-V1)

Stores segments with full provenance:

```
┌─────────────────────────────────┐
│ Header                          │
│   Magic: "RWVV"                 │
│   Version: 1                    │
│   Segment count                 │
│   Source info                   │
├─────────────────────────────────┤
│ Index (JSONL)                   │
│   Segment records with:         │
│   - Time range                  │
│   - Encoder used                │
│   - Parameters                  │
│   - Perceptual metrics          │
│   - Payload offset/size         │
├─────────────────────────────────┤
│ Payload Blob                    │
│   Concatenated segment data     │
└─────────────────────────────────┘
```

## Plugin Stubs

### FFmpeg Filter

Location: `src/plugins/ffmpeg_stub.c`

```bash
# Build (when implemented)
gcc -shared -fPIC -o rw_upscale.so ffmpeg_stub.c

# Use
ffmpeg -i input.mp4 -vf rw_upscale=w=3840:h=2160 output.mp4
```

### GStreamer Element

Location: `src/plugins/gstreamer_stub.c`

```bash
# Build (when implemented)
gcc -shared -fPIC $(pkg-config --cflags --libs gstreamer-1.0) -o libgstrwupscale.so gstreamer_stub.c

# Use
gst-launch-1.0 filesrc ! decodebin ! rwupscale ! encoder ! filesink
```

## Scenarios

Predefined scenarios for testing:

| Scenario | Input | Output | Quality |
|----------|-------|--------|---------|
| sd_to_4k_archival | 480p | 4K | Archival |
| hd_to_8k_premium | 1080p | 8K | Premium |
| realtime_broadcast | 1080p | 4K | Realtime |

## Threat Model

### Risks

1. **Hallucinated detail**: Upscaling may introduce false details
2. **Temporal inconsistency**: Frame-to-frame artifacts
3. **Over-sharpening**: Excessive enhancement
4. **Metric gaming**: Optimizing for metrics over visual quality

### Mitigations

1. Conservative default thresholds
2. Multi-metric gates
3. Segment-level independence
4. Deterministic decode verification
5. Fail-soft: always produce output

## TODO

- [ ] Full ffmpeg integration
- [ ] Full gstreamer integration
- [ ] VMAF metric computation
- [ ] Scene-cut segmentation
- [ ] Motion-adaptive segmentation
- [ ] Hardware encoder support
- [ ] Stable binary container format
