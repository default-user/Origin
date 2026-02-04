# Weaver Modules TODO

Items marked TODO in the implementation that need resolution before production use.

## Global

- [ ] **WCL-1.0 License**: Full legal text needs review by qualified counsel
- [x] **blake3 hashing**: ~~Optional dependency for ProofWeave; falls back to SHA-256~~
  - Implemented with proper fallback, warning system, and `is_blake3_available()` check

## RealityWeaver (RWV1)

- [ ] **MO dictionary scoring**: Exact scoring formula for phrase selection should be formalized
- [ ] **Probe gating heuristics**: Document or standardize text detection heuristic

## PhraseWeave (PWV1)

- [ ] **PHRASE token**: Multi-Stan phrase expansion needs phrase table in dictionary
- [ ] **REPEAT optimization**: Consider run-length encoding optimization pass

## ProofWeave (PWOF/PWK)

- [ ] **Quantifiers**: ALL and EX reserved for v1.1+; kernel must reject
- [ ] **Additional rules**: Consider adding IMP_INTRO, NOT_INTRO, OR_ELIM for completeness
- [ ] **Subproofs**: Nested proof contexts for hypothetical reasoning

## RealityWeaverVideo (RWV-VIDEO-V1)

- [x] **Full ffmpeg integration**: ~~Currently stub only~~
  - Implemented complete pipeline with ffprobe duration detection, segment extraction,
    multi-encoder WeaveRace, PSNR/SSIM metric computation, and segment concatenation
  - FFmpeg filter plugin (`rw_upscale`) implemented with bicubic/lanczos upscaling,
    quality gates, and adaptive sharpening
- [x] **Full gstreamer integration**: ~~Currently stub only~~
  - GStreamer element (`rwupscale`) implemented with bilinear/bicubic/lanczos algorithms,
    quality presets, PSNR/SSIM metrics, and fail-soft escalation
- [x] **VMAF computation**: ~~Needs external tool or library~~
  - Integrated via ffmpeg libvmaf filter when available; gracefully degrades to PSNR+SSIM
- [x] **Scene-cut detection**: ~~Algorithm not implemented~~
  - Implemented using ffmpeg scene filter with configurable threshold
- [x] **Motion-adaptive segmentation**: ~~Algorithm not implemented~~
  - Implemented using mpdecimate filter analysis; adapts segment duration based on motion
- [x] **Stable binary container format**: ~~Current format is interim JSONL + blob~~
  - Defined stable 64-byte header with CRC32 checksums, fixed 80-byte segment index entries,
    backward-compatible legacy format support
- [ ] **Hardware encoder support**: NVENC, QSV, AMF paths
  - Encoder IDs defined but hardware detection not implemented
- [ ] **Upscale algorithm**: RealityWeaverUpscale_v1 archive was empty
  - Basic upscaling via swscale (ffmpeg) or custom bilinear/bicubic/lanczos (gstreamer)

## Integration

- [ ] **Origin build integration**: Add to main build pipeline
- [ ] **CI testing**: Add module tests to GitHub Actions
- [ ] **TypeScript bindings**: For Origin site integration
- [ ] **Concept pack**: Create C#### concept pack for Weaver framework

## Documentation

- [ ] **API reference**: Generate from docstrings
- [ ] **Tutorial**: Step-by-step usage guide
- [ ] **Architecture diagram**: Visual pipeline overview

---

## Changelog

### 2026-02-04
- Implemented full video processing pipeline in `pipeline.py`
- Implemented stable binary container format in `container.py`
- Implemented FFmpeg filter plugin (`ffmpeg_stub.c` → full `rw_upscale` filter)
- Implemented GStreamer element plugin (`gstreamer_stub.c` → full `rwupscale` element)
- Enhanced blake3 support in ProofWeave with proper fallback and `is_blake3_available()`
