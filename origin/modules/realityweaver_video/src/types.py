# RealityWeaverVideo Types
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Core types for RealityWeaverVideo pipeline.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple


class SegmentationStrategy(Enum):
    """Strategies for segmenting video."""
    SCENE_CUT = auto()       # Cut on scene changes
    FIXED_DURATION = auto()  # Fixed time intervals
    MOTION_ADAPTIVE = auto() # Adapt to motion complexity


class EncoderID(str, Enum):
    """Supported encoder identifiers."""
    X264 = "x264"
    X265 = "x265"
    SVTAV1 = "svt-av1"
    VP9 = "vp9"
    NVENC_H264 = "nvenc-h264"
    NVENC_HEVC = "nvenc-hevc"


@dataclass
class PerceptualMetrics:
    """Perceptual quality metrics for a segment."""
    vmaf: Optional[float] = None
    psnr: Optional[float] = None
    ssim: Optional[float] = None

    @property
    def is_visually_lossless(self) -> bool:
        """
        Check if metrics indicate visually lossless quality.

        Definition (default gates):
          VMAF >= 95
          OR (PSNR >= 45 dB AND SSIM >= 0.995)
        """
        if self.vmaf is not None and self.vmaf >= 95:
            return True
        if (self.psnr is not None and self.ssim is not None and
            self.psnr >= 45 and self.ssim >= 0.995):
            return True
        return False


@dataclass
class EncoderConfig:
    """Configuration for a video encoder."""
    encoder_id: EncoderID
    preset: str = "medium"
    crf: int = 23
    tune: Optional[str] = None
    extra_params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "encoder_id": self.encoder_id.value,
            "preset": self.preset,
            "crf": self.crf,
            "tune": self.tune,
            "extra_params": self.extra_params,
        }


@dataclass
class Segment:
    """A video segment for processing."""
    segment_id: int
    start_time: float  # seconds
    end_time: float    # seconds
    keyframe_start: bool = True

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "keyframe_start": self.keyframe_start,
        }


@dataclass
class SegmentResult:
    """Result of processing a single segment."""
    segment: Segment
    chosen_encoder: EncoderConfig
    metrics: PerceptualMetrics
    input_size: int      # bytes
    output_size: int     # bytes
    encode_time: float   # seconds
    passed_gate: bool

    @property
    def compression_ratio(self) -> float:
        if self.input_size == 0:
            return 0.0
        return self.output_size / self.input_size

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment": self.segment.to_dict(),
            "encoder": self.chosen_encoder.to_dict(),
            "metrics": {
                "vmaf": self.metrics.vmaf,
                "psnr": self.metrics.psnr,
                "ssim": self.metrics.ssim,
                "visually_lossless": self.metrics.is_visually_lossless,
            },
            "input_size": self.input_size,
            "output_size": self.output_size,
            "compression_ratio": self.compression_ratio,
            "encode_time": self.encode_time,
            "passed_gate": self.passed_gate,
        }


# Threat model risks (documented)
THREAT_MODEL = """
RealityWeaverVideo Threat Model:

Risks:
1. Hallucinated detail: Upscaling may introduce false details
2. Temporal inconsistency: Frame-to-frame artifacts from independent processing
3. Over-sharpening: Excessive enhancement degrading natural appearance
4. Metric gaming: Encoders optimized for metrics rather than visual quality

Mitigations:
1. Conservative defaults (high quality targets)
2. Multi-metric gates (VMAF AND/OR PSNR+SSIM)
3. Segment-level autonomy (each segment independently verified)
4. Deterministic decode verification
5. Fail-soft: always produce output, escalate quality on gate failure
"""


# Perceptual gate thresholds
class GateThresholds:
    """Default perceptual quality gate thresholds."""
    VMAF_LOSSLESS = 95.0
    PSNR_LOSSLESS = 45.0   # dB
    SSIM_LOSSLESS = 0.995

    VMAF_HIGH = 90.0
    PSNR_HIGH = 40.0
    SSIM_HIGH = 0.99

    VMAF_ACCEPTABLE = 85.0
    PSNR_ACCEPTABLE = 35.0
    SSIM_ACCEPTABLE = 0.98
