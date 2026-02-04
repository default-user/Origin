# RealityWeaverVideo (RWV-VIDEO-V1)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RealityWeaverVideo: Video processing pipeline with auditable packaging.

Pipeline stages:
  Decode → Segment → WeaveRace → Gate → Select → Package

Features:
- Segment-based processing for parallel encoding
- Perceptual quality gates (VMAF, PSNR, SSIM)
- Decision provenance for audit
- Multiple encoder support (via ffmpeg/gstreamer)

Note: This is a skeleton implementation. Full functionality requires
external dependencies (ffmpeg, gstreamer) that are marked as TODO.
"""

from .pipeline import (
    VideoPipeline,
    PipelineConfig,
    PipelineResult,
)
from .types import (
    Segment,
    SegmentResult,
    EncoderConfig,
    PerceptualMetrics,
    SegmentationStrategy,
)

__all__ = [
    'VideoPipeline',
    'PipelineConfig',
    'PipelineResult',
    'Segment',
    'SegmentResult',
    'EncoderConfig',
    'PerceptualMetrics',
    'SegmentationStrategy',
]

__version__ = '1.0.0'
