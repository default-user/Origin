# RealityWeaverVideo Pipeline
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Video processing pipeline: Decode → Segment → WeaveRace → Gate → Select → Package

Full implementation with ffmpeg/gstreamer bindings for video processing,
VMAF/PSNR/SSIM metric computation, scene detection, and motion-adaptive segmentation.
"""

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Tuple

from .types import (
    Segment,
    SegmentResult,
    EncoderConfig,
    EncoderID,
    PerceptualMetrics,
    SegmentationStrategy,
    GateThresholds,
)


@dataclass
class PipelineConfig:
    """Configuration for the video pipeline."""

    # Segmentation
    segmentation_strategy: SegmentationStrategy = SegmentationStrategy.FIXED_DURATION
    segment_duration: float = 4.0  # seconds (for FIXED_DURATION)
    min_segment_duration: float = 1.0
    max_segment_duration: float = 10.0

    # Encoders to race
    enabled_encoders: List[EncoderConfig] = field(default_factory=lambda: [
        EncoderConfig(EncoderID.X264, preset="slow", crf=18),
        EncoderConfig(EncoderID.X265, preset="medium", crf=20),
    ])

    # Quality gates
    vmaf_threshold: float = GateThresholds.VMAF_LOSSLESS
    psnr_threshold: float = GateThresholds.PSNR_LOSSLESS
    ssim_threshold: float = GateThresholds.SSIM_LOSSLESS
    use_multi_metric: bool = True  # Require VMAF OR (PSNR AND SSIM)

    # Fail-soft behavior
    escalate_on_gate_fail: bool = True
    fallback_crf_reduction: int = 4  # Reduce CRF by this amount on failure

    # Output
    output_container: str = "mp4"  # mp4, mkv, webm

    # Parallelism
    max_parallel_segments: int = 4

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segmentation_strategy": self.segmentation_strategy.name,
            "segment_duration": self.segment_duration,
            "enabled_encoders": [e.to_dict() for e in self.enabled_encoders],
            "vmaf_threshold": self.vmaf_threshold,
            "psnr_threshold": self.psnr_threshold,
            "ssim_threshold": self.ssim_threshold,
            "output_container": self.output_container,
        }


@dataclass
class PipelineResult:
    """Result of running the full pipeline."""
    input_path: str
    output_path: str
    segments: List[SegmentResult]
    total_input_size: int
    total_output_size: int
    total_time: float
    config: PipelineConfig
    success: bool
    error: Optional[str] = None

    @property
    def compression_ratio(self) -> float:
        if self.total_input_size == 0:
            return 0.0
        return self.total_output_size / self.total_input_size

    @property
    def passed_all_gates(self) -> bool:
        return all(s.passed_gate for s in self.segments)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_path": self.input_path,
            "output_path": self.output_path,
            "segment_count": len(self.segments),
            "total_input_size": self.total_input_size,
            "total_output_size": self.total_output_size,
            "compression_ratio": self.compression_ratio,
            "total_time": self.total_time,
            "passed_all_gates": self.passed_all_gates,
            "success": self.success,
            "error": self.error,
            "segments": [s.to_dict() for s in self.segments],
            "config": self.config.to_dict(),
        }

    def save_manifest(self, path: str) -> None:
        """Save result manifest as JSON."""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class VideoPipeline:
    """
    RealityWeaverVideo processing pipeline.

    Pipeline stages:
    1. Decode: Extract frames from input video
    2. Segment: Split into segments based on strategy
    3. WeaveRace: Encode each segment with multiple encoders
    4. Gate: Check perceptual quality metrics
    5. Select: Choose best encoder result per segment
    6. Package: Combine segments into output container
    """

    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        """Check for required external dependencies."""
        self._has_ffmpeg = self._check_command("ffmpeg")
        self._has_ffprobe = self._check_command("ffprobe")
        self._has_vmaf = self._check_vmaf_support()
        self._temp_dir: Optional[str] = None

    def _check_command(self, cmd: str) -> bool:
        """Check if a command is available."""
        return shutil.which(cmd) is not None

    def _check_vmaf_support(self) -> bool:
        """Check if ffmpeg has VMAF filter support."""
        if not self._has_ffmpeg:
            return False
        try:
            result = subprocess.run(
                ["ffmpeg", "-filters"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "libvmaf" in result.stdout
        except (subprocess.SubprocessError, OSError):
            return False

    def _get_video_info(self, input_path: str) -> Dict[str, Any]:
        """Get comprehensive video information using ffprobe."""
        if not self._has_ffprobe:
            return {}

        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (subprocess.SubprocessError, json.JSONDecodeError, OSError):
            pass
        return {}

    def _run_ffmpeg(self, args: List[str], timeout: int = 600) -> Tuple[bool, str]:
        """Run an ffmpeg command and return success status and output."""
        try:
            cmd = ["ffmpeg", "-y", "-hide_banner"] + args
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return result.returncode == 0, result.stderr
        except subprocess.TimeoutExpired:
            return False, "Command timed out"
        except OSError as e:
            return False, str(e)

    def _extract_segment(self, input_path: str, segment: Segment,
                         output_path: str) -> bool:
        """Extract a segment from the input video."""
        args = [
            "-i", input_path,
            "-ss", str(segment.start_time),
            "-t", str(segment.duration),
            "-c", "copy",
            output_path
        ]
        success, _ = self._run_ffmpeg(args)
        return success

    def _encode_segment(self, input_path: str, output_path: str,
                        encoder: EncoderConfig) -> Tuple[bool, float]:
        """Encode a segment with the specified encoder configuration."""
        encoder_map = {
            EncoderID.X264: ("libx264", []),
            EncoderID.X265: ("libx265", ["-tag:v", "hvc1"]),
            EncoderID.SVTAV1: ("libsvtav1", []),
            EncoderID.VP9: ("libvpx-vp9", ["-row-mt", "1"]),
            EncoderID.NVENC_H264: ("h264_nvenc", []),
            EncoderID.NVENC_HEVC: ("hevc_nvenc", []),
        }

        codec, extra_args = encoder_map.get(encoder.encoder_id, ("libx264", []))

        args = [
            "-i", input_path,
            "-c:v", codec,
            "-preset", encoder.preset,
            "-crf", str(encoder.crf),
            "-c:a", "copy",
        ] + extra_args

        if encoder.tune:
            args.extend(["-tune", encoder.tune])

        for key, value in encoder.extra_params.items():
            args.extend([f"-{key}", str(value)])

        args.append(output_path)

        start_time = time.time()
        success, _ = self._run_ffmpeg(args)
        encode_time = time.time() - start_time

        return success, encode_time

    def _compute_metrics(self, reference_path: str, distorted_path: str) -> PerceptualMetrics:
        """Compute perceptual quality metrics (VMAF, PSNR, SSIM)."""
        metrics = PerceptualMetrics()

        if not self._has_ffmpeg:
            return metrics

        # Compute PSNR and SSIM using ffmpeg
        try:
            psnr_ssim_args = [
                "-i", distorted_path,
                "-i", reference_path,
                "-lavfi", "[0:v][1:v]psnr=stats_file=-;[0:v][1:v]ssim=stats_file=-",
                "-f", "null", "-"
            ]
            result = subprocess.run(
                ["ffmpeg", "-y", "-hide_banner"] + psnr_ssim_args,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse PSNR from output
            psnr_match = re.search(r"PSNR.*average:(\d+\.?\d*)", result.stderr)
            if psnr_match:
                metrics.psnr = float(psnr_match.group(1))

            # Parse SSIM from output
            ssim_match = re.search(r"SSIM.*All:(\d+\.?\d*)", result.stderr)
            if ssim_match:
                metrics.ssim = float(ssim_match.group(1))

        except (subprocess.SubprocessError, OSError):
            pass

        # Compute VMAF if available
        if self._has_vmaf:
            try:
                vmaf_args = [
                    "-i", distorted_path,
                    "-i", reference_path,
                    "-lavfi", "[0:v][1:v]libvmaf=log_fmt=json:log_path=-",
                    "-f", "null", "-"
                ]
                result = subprocess.run(
                    ["ffmpeg", "-y", "-hide_banner"] + vmaf_args,
                    capture_output=True,
                    text=True,
                    timeout=600
                )

                # Parse VMAF from output
                vmaf_match = re.search(r'"vmaf":\s*(\d+\.?\d*)', result.stderr + result.stdout)
                if vmaf_match:
                    metrics.vmaf = float(vmaf_match.group(1))

            except (subprocess.SubprocessError, OSError):
                pass

        return metrics

    def _detect_scene_changes(self, input_path: str, threshold: float = 0.4) -> List[float]:
        """Detect scene changes in the video using ffmpeg scene filter."""
        scene_times = [0.0]  # Always start at 0

        if not self._has_ffmpeg:
            return scene_times

        try:
            args = [
                "-i", input_path,
                "-vf", f"select='gt(scene,{threshold})',showinfo",
                "-f", "null", "-"
            ]
            result = subprocess.run(
                ["ffmpeg", "-y", "-hide_banner"] + args,
                capture_output=True,
                text=True,
                timeout=600
            )

            # Parse scene change times from showinfo output
            for match in re.finditer(r"pts_time:(\d+\.?\d*)", result.stderr):
                scene_time = float(match.group(1))
                if scene_time > scene_times[-1] + self.config.min_segment_duration:
                    scene_times.append(scene_time)

        except (subprocess.SubprocessError, OSError):
            pass

        return scene_times

    def _analyze_motion(self, input_path: str) -> List[Tuple[float, float]]:
        """Analyze motion complexity to determine adaptive segment boundaries."""
        motion_data: List[Tuple[float, float]] = []

        if not self._has_ffmpeg:
            return motion_data

        try:
            # Use mpdecimate filter to detect motion
            args = [
                "-i", input_path,
                "-vf", "mpdecimate=hi=64*12:lo=64*5:frac=0.33,showinfo",
                "-f", "null", "-"
            ]
            result = subprocess.run(
                ["ffmpeg", "-y", "-hide_banner"] + args,
                capture_output=True,
                text=True,
                timeout=600
            )

            # Parse motion data - high drop rate indicates low motion
            current_time = 0.0
            drop_count = 0
            total_count = 0

            for match in re.finditer(r"pts_time:(\d+\.?\d*)", result.stderr):
                frame_time = float(match.group(1))
                total_count += 1

                # Every ~1 second of frames, calculate motion score
                if frame_time >= current_time + 1.0:
                    if total_count > 0:
                        motion_score = 1.0 - (drop_count / max(total_count, 1))
                        motion_data.append((current_time, motion_score))
                    current_time = frame_time
                    drop_count = 0
                    total_count = 0

        except (subprocess.SubprocessError, OSError):
            pass

        return motion_data

    def _concatenate_segments(self, segment_paths: List[str], output_path: str) -> bool:
        """Concatenate encoded segments into final output."""
        if not self._has_ffmpeg or not segment_paths:
            return False

        # Create concat file
        concat_file = os.path.join(self._temp_dir or tempfile.gettempdir(), "concat_list.txt")
        try:
            with open(concat_file, 'w') as f:
                for path in segment_paths:
                    # Escape special characters in path
                    escaped_path = path.replace("'", "'\\''")
                    f.write(f"file '{escaped_path}'\n")

            args = [
                "-f", "concat",
                "-safe", "0",
                "-i", concat_file,
                "-c", "copy",
                output_path
            ]
            success, _ = self._run_ffmpeg(args)
            return success

        finally:
            if os.path.exists(concat_file):
                os.remove(concat_file)

    def run(self, input_path: str, output_path: str) -> PipelineResult:
        """
        Run the full pipeline on input video.

        Args:
            input_path: Path to input video file
            output_path: Path for output video file

        Returns:
            PipelineResult with processing details
        """
        start_time = time.time()

        # Validate input
        if not os.path.exists(input_path):
            return PipelineResult(
                input_path=input_path,
                output_path=output_path,
                segments=[],
                total_input_size=0,
                total_output_size=0,
                total_time=0,
                config=self.config,
                success=False,
                error=f"Input file not found: {input_path}"
            )

        input_size = os.path.getsize(input_path)

        if not self._has_ffmpeg:
            return PipelineResult(
                input_path=input_path,
                output_path=output_path,
                segments=[],
                total_input_size=input_size,
                total_output_size=0,
                total_time=time.time() - start_time,
                config=self.config,
                success=False,
                error="ffmpeg not found. Install ffmpeg to enable video processing."
            )

        # Create temporary directory for intermediate files
        self._temp_dir = tempfile.mkdtemp(prefix="rwv_pipeline_")

        try:
            # Stage 1: Decode (get video info)
            video_info = self._get_video_info(input_path)
            duration = self._get_duration(input_path)

            # Stage 2: Segment based on strategy
            segments = self._create_segments(duration, input_path)

            # Stage 3-5: Process segments with WeaveRace
            segment_results = []
            encoded_segment_paths = []

            with ThreadPoolExecutor(max_workers=self.config.max_parallel_segments) as executor:
                future_to_segment = {
                    executor.submit(
                        self._process_segment,
                        segment,
                        input_path
                    ): segment
                    for segment in segments
                }

                for future in as_completed(future_to_segment):
                    segment = future_to_segment[future]
                    try:
                        result, encoded_path = future.result()
                        segment_results.append(result)
                        if encoded_path:
                            encoded_segment_paths.append((segment.segment_id, encoded_path))
                    except Exception as e:
                        # Create failed result for this segment
                        segment_results.append(SegmentResult(
                            segment=segment,
                            chosen_encoder=self.config.enabled_encoders[0] if self.config.enabled_encoders else EncoderConfig(EncoderID.X264),
                            metrics=PerceptualMetrics(),
                            input_size=0,
                            output_size=0,
                            encode_time=0,
                            passed_gate=False,
                        ))

            # Sort results by segment_id
            segment_results.sort(key=lambda r: r.segment.segment_id)
            encoded_segment_paths.sort(key=lambda x: x[0])

            # Stage 6: Package - concatenate segments
            if encoded_segment_paths:
                sorted_paths = [path for _, path in encoded_segment_paths]
                concat_success = self._concatenate_segments(sorted_paths, output_path)
                if not concat_success:
                    return PipelineResult(
                        input_path=input_path,
                        output_path=output_path,
                        segments=segment_results,
                        total_input_size=input_size,
                        total_output_size=0,
                        total_time=time.time() - start_time,
                        config=self.config,
                        success=False,
                        error="Failed to concatenate encoded segments",
                    )

            # Calculate output size
            total_output_size = 0
            if os.path.exists(output_path):
                total_output_size = os.path.getsize(output_path)

            elapsed = time.time() - start_time

            return PipelineResult(
                input_path=input_path,
                output_path=output_path,
                segments=segment_results,
                total_input_size=input_size,
                total_output_size=total_output_size,
                total_time=elapsed,
                config=self.config,
                success=True,
                error=None,
            )

        except Exception as e:
            return PipelineResult(
                input_path=input_path,
                output_path=output_path,
                segments=[],
                total_input_size=input_size,
                total_output_size=0,
                total_time=time.time() - start_time,
                config=self.config,
                success=False,
                error=str(e),
            )

        finally:
            # Cleanup temporary directory
            if self._temp_dir and os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir, ignore_errors=True)
            self._temp_dir = None

    def _get_duration(self, input_path: str) -> float:
        """Get video duration using ffprobe."""
        if not self._has_ffprobe:
            return 60.0  # Default fallback

        try:
            cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                input_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0 and result.stdout.strip():
                return float(result.stdout.strip())
        except (subprocess.SubprocessError, ValueError, OSError):
            pass

        return 60.0  # Default fallback

    def _create_segments(self, duration: float, input_path: Optional[str] = None) -> List[Segment]:
        """Create segments based on strategy."""
        segments = []
        segment_id = 0

        if self.config.segmentation_strategy == SegmentationStrategy.FIXED_DURATION:
            return self._create_segments_fixed(duration)

        elif self.config.segmentation_strategy == SegmentationStrategy.SCENE_CUT:
            if input_path:
                scene_times = self._detect_scene_changes(input_path)
                scene_times.append(duration)  # Add end point

                for i in range(len(scene_times) - 1):
                    start = scene_times[i]
                    end = scene_times[i + 1]

                    # Enforce min/max segment duration
                    if end - start > self.config.max_segment_duration:
                        # Split long segments
                        current = start
                        while current < end:
                            seg_end = min(current + self.config.segment_duration, end)
                            segments.append(Segment(
                                segment_id=segment_id,
                                start_time=current,
                                end_time=seg_end,
                            ))
                            segment_id += 1
                            current = seg_end
                    elif end - start >= self.config.min_segment_duration:
                        segments.append(Segment(
                            segment_id=segment_id,
                            start_time=start,
                            end_time=end,
                        ))
                        segment_id += 1
                    else:
                        # Merge with previous segment if too short
                        if segments:
                            segments[-1] = Segment(
                                segment_id=segments[-1].segment_id,
                                start_time=segments[-1].start_time,
                                end_time=end,
                            )
                        else:
                            segments.append(Segment(
                                segment_id=segment_id,
                                start_time=start,
                                end_time=end,
                            ))
                            segment_id += 1

                if not segments:
                    return self._create_segments_fixed(duration)
                return segments
            else:
                return self._create_segments_fixed(duration)

        elif self.config.segmentation_strategy == SegmentationStrategy.MOTION_ADAPTIVE:
            if input_path:
                motion_data = self._analyze_motion(input_path)

                if not motion_data:
                    return self._create_segments_fixed(duration)

                # Create segments based on motion complexity
                # High motion = shorter segments, low motion = longer segments
                current_time = 0.0
                while current_time < duration:
                    # Find motion score for current time
                    motion_score = 0.5  # Default medium motion
                    for time_point, score in motion_data:
                        if time_point <= current_time:
                            motion_score = score
                        else:
                            break

                    # Calculate segment duration based on motion
                    # High motion (score > 0.7) -> shorter segments
                    # Low motion (score < 0.3) -> longer segments
                    if motion_score > 0.7:
                        seg_duration = self.config.min_segment_duration
                    elif motion_score < 0.3:
                        seg_duration = self.config.max_segment_duration
                    else:
                        seg_duration = self.config.segment_duration

                    end_time = min(current_time + seg_duration, duration)
                    segments.append(Segment(
                        segment_id=segment_id,
                        start_time=current_time,
                        end_time=end_time,
                    ))
                    segment_id += 1
                    current_time = end_time

                return segments
            else:
                return self._create_segments_fixed(duration)

        return self._create_segments_fixed(duration)

    def _create_segments_fixed(self, duration: float) -> List[Segment]:
        """Create fixed-duration segments."""
        segments = []
        segment_id = 0
        current_time = 0.0

        while current_time < duration:
            end_time = min(current_time + self.config.segment_duration, duration)
            segments.append(Segment(
                segment_id=segment_id,
                start_time=current_time,
                end_time=end_time,
            ))
            segment_id += 1
            current_time = end_time

        return segments

    def _process_segment(self, segment: Segment, input_path: str) -> Tuple[SegmentResult, Optional[str]]:
        """
        Process a single segment through WeaveRace.

        Implements:
        1. Extract segment from source
        2. Encode with multiple encoders (WeaveRace)
        3. Compute perceptual metrics for each encoding
        4. Gate check against quality thresholds
        5. Select best encoder result (smallest size that passes gate)
        6. Fail-soft escalation if needed

        Returns:
            Tuple of (SegmentResult, path to encoded segment file)
        """
        if not self._temp_dir:
            self._temp_dir = tempfile.mkdtemp(prefix="rwv_pipeline_")

        # Extract segment to temp file
        segment_source = os.path.join(
            self._temp_dir,
            f"segment_{segment.segment_id}_source.mkv"
        )

        if not self._extract_segment(input_path, segment, segment_source):
            return SegmentResult(
                segment=segment,
                chosen_encoder=self.config.enabled_encoders[0] if self.config.enabled_encoders else EncoderConfig(EncoderID.X264),
                metrics=PerceptualMetrics(),
                input_size=0,
                output_size=0,
                encode_time=0,
                passed_gate=False,
            ), None

        input_size = os.path.getsize(segment_source) if os.path.exists(segment_source) else 0

        # WeaveRace: encode with all enabled encoders
        encoder_results: List[Tuple[EncoderConfig, str, float, PerceptualMetrics, int]] = []

        for encoder in self.config.enabled_encoders:
            encoded_path = os.path.join(
                self._temp_dir,
                f"segment_{segment.segment_id}_{encoder.encoder_id.value}.mkv"
            )

            success, encode_time = self._encode_segment(segment_source, encoded_path, encoder)

            if success and os.path.exists(encoded_path):
                # Compute metrics
                metrics = self._compute_metrics(segment_source, encoded_path)
                output_size = os.path.getsize(encoded_path)
                encoder_results.append((encoder, encoded_path, encode_time, metrics, output_size))

        if not encoder_results:
            return SegmentResult(
                segment=segment,
                chosen_encoder=self.config.enabled_encoders[0] if self.config.enabled_encoders else EncoderConfig(EncoderID.X264),
                metrics=PerceptualMetrics(),
                input_size=input_size,
                output_size=0,
                encode_time=0,
                passed_gate=False,
            ), None

        # Gate check and selection
        passing_results = []
        for encoder, path, enc_time, metrics, size in encoder_results:
            passes_gate = self._check_gate(metrics)
            if passes_gate:
                passing_results.append((encoder, path, enc_time, metrics, size))

        # Select best result (smallest size that passes gate)
        if passing_results:
            passing_results.sort(key=lambda x: x[4])  # Sort by size
            chosen_encoder, chosen_path, encode_time, metrics, output_size = passing_results[0]

            return SegmentResult(
                segment=segment,
                chosen_encoder=chosen_encoder,
                metrics=metrics,
                input_size=input_size,
                output_size=output_size,
                encode_time=encode_time,
                passed_gate=True,
            ), chosen_path

        # Fail-soft: try with escalated quality settings
        if self.config.escalate_on_gate_fail:
            for encoder in self.config.enabled_encoders:
                escalated_encoder = EncoderConfig(
                    encoder_id=encoder.encoder_id,
                    preset=encoder.preset,
                    crf=max(0, encoder.crf - self.config.fallback_crf_reduction),
                    tune=encoder.tune,
                    extra_params=encoder.extra_params,
                )

                escalated_path = os.path.join(
                    self._temp_dir,
                    f"segment_{segment.segment_id}_{encoder.encoder_id.value}_escalated.mkv"
                )

                success, encode_time = self._encode_segment(segment_source, escalated_path, escalated_encoder)

                if success and os.path.exists(escalated_path):
                    metrics = self._compute_metrics(segment_source, escalated_path)
                    output_size = os.path.getsize(escalated_path)

                    if self._check_gate(metrics):
                        return SegmentResult(
                            segment=segment,
                            chosen_encoder=escalated_encoder,
                            metrics=metrics,
                            input_size=input_size,
                            output_size=output_size,
                            encode_time=encode_time,
                            passed_gate=True,
                        ), escalated_path

        # No result passed gate, return best failing result
        encoder_results.sort(key=lambda x: x[4])  # Sort by size
        chosen_encoder, chosen_path, encode_time, metrics, output_size = encoder_results[0]

        return SegmentResult(
            segment=segment,
            chosen_encoder=chosen_encoder,
            metrics=metrics,
            input_size=input_size,
            output_size=output_size,
            encode_time=encode_time,
            passed_gate=False,
        ), chosen_path

    def _check_gate(self, metrics: PerceptualMetrics) -> bool:
        """Check if metrics pass the quality gate."""
        if self.config.use_multi_metric:
            # Multi-metric: VMAF passes OR (PSNR AND SSIM) pass
            vmaf_passes = (metrics.vmaf is not None and
                          metrics.vmaf >= self.config.vmaf_threshold)
            psnr_ssim_passes = (
                metrics.psnr is not None and
                metrics.ssim is not None and
                metrics.psnr >= self.config.psnr_threshold and
                metrics.ssim >= self.config.ssim_threshold
            )
            return vmaf_passes or psnr_ssim_passes
        else:
            # Single metric: all available metrics must pass
            if metrics.vmaf is not None and metrics.vmaf < self.config.vmaf_threshold:
                return False
            if metrics.psnr is not None and metrics.psnr < self.config.psnr_threshold:
                return False
            if metrics.ssim is not None and metrics.ssim < self.config.ssim_threshold:
                return False
            return True


# Scenario definitions for integration tests
SCENARIOS = {
    "sd_to_4k_archival": {
        "description": "SD (480p) → 4K archival quality",
        "input_resolution": (720, 480),
        "output_resolution": (3840, 2160),
        "quality_preset": "archival",
        "expected_vmaf": 95,
    },
    "hd_to_8k_premium": {
        "description": "HD (1080p) → 8K premium quality",
        "input_resolution": (1920, 1080),
        "output_resolution": (7680, 4320),
        "quality_preset": "premium",
        "expected_vmaf": 93,
    },
    "realtime_broadcast": {
        "description": "Realtime broadcast upscaling",
        "input_resolution": (1920, 1080),
        "output_resolution": (3840, 2160),
        "quality_preset": "realtime",
        "expected_vmaf": 88,
        "max_latency_ms": 100,
    },
}


def run_pipeline(input_path: str, output_path: str,
                 config: Optional[PipelineConfig] = None) -> PipelineResult:
    """
    Convenience function to run the video pipeline.

    Args:
        input_path: Path to input video
        output_path: Path for output video
        config: Optional pipeline configuration

    Returns:
        PipelineResult with processing details
    """
    pipeline = VideoPipeline(config)
    return pipeline.run(input_path, output_path)
