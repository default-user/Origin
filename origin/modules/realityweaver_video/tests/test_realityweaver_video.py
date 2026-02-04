#!/usr/bin/env python3
# RealityWeaverVideo Test Suite
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Test suite for RealityWeaverVideo pipeline.
"""

import json
import os
import tempfile
import unittest
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from types import (
    Segment,
    SegmentResult,
    EncoderConfig,
    EncoderID,
    PerceptualMetrics,
    SegmentationStrategy,
    GateThresholds,
)
from pipeline import (
    VideoPipeline,
    PipelineConfig,
    PipelineResult,
    SCENARIOS,
)
from container import (
    VideoContainer,
    SegmentRecord,
    RWV_VIDEO_MAGIC,
)


class TestPerceptualMetrics(unittest.TestCase):
    """Test perceptual metrics."""

    def test_visually_lossless_vmaf(self):
        """VMAF >= 95 is visually lossless."""
        m = PerceptualMetrics(vmaf=95.0)
        self.assertTrue(m.is_visually_lossless)

        m = PerceptualMetrics(vmaf=94.9)
        self.assertFalse(m.is_visually_lossless)

    def test_visually_lossless_psnr_ssim(self):
        """PSNR >= 45 AND SSIM >= 0.995 is visually lossless."""
        m = PerceptualMetrics(psnr=45.0, ssim=0.995)
        self.assertTrue(m.is_visually_lossless)

        m = PerceptualMetrics(psnr=45.0, ssim=0.994)
        self.assertFalse(m.is_visually_lossless)

        m = PerceptualMetrics(psnr=44.9, ssim=0.995)
        self.assertFalse(m.is_visually_lossless)

    def test_visually_lossless_either(self):
        """Either condition satisfied is visually lossless."""
        # VMAF only
        m = PerceptualMetrics(vmaf=96.0, psnr=30.0, ssim=0.9)
        self.assertTrue(m.is_visually_lossless)

        # PSNR+SSIM only
        m = PerceptualMetrics(vmaf=80.0, psnr=46.0, ssim=0.998)
        self.assertTrue(m.is_visually_lossless)


class TestSegment(unittest.TestCase):
    """Test segment type."""

    def test_duration(self):
        """Segment duration calculation."""
        s = Segment(segment_id=0, start_time=0.0, end_time=4.0)
        self.assertEqual(s.duration, 4.0)

    def test_to_dict(self):
        """Segment serialization."""
        s = Segment(segment_id=1, start_time=4.0, end_time=8.0)
        d = s.to_dict()
        self.assertEqual(d['segment_id'], 1)
        self.assertEqual(d['start_time'], 4.0)
        self.assertEqual(d['end_time'], 8.0)
        self.assertEqual(d['duration'], 4.0)


class TestEncoderConfig(unittest.TestCase):
    """Test encoder configuration."""

    def test_to_dict(self):
        """Encoder config serialization."""
        c = EncoderConfig(EncoderID.X265, preset="slow", crf=18)
        d = c.to_dict()
        self.assertEqual(d['encoder_id'], 'x265')
        self.assertEqual(d['preset'], 'slow')
        self.assertEqual(d['crf'], 18)


class TestPipelineConfig(unittest.TestCase):
    """Test pipeline configuration."""

    def test_defaults(self):
        """Default configuration values."""
        c = PipelineConfig()
        self.assertEqual(c.segmentation_strategy, SegmentationStrategy.FIXED_DURATION)
        self.assertEqual(c.segment_duration, 4.0)
        self.assertEqual(c.vmaf_threshold, GateThresholds.VMAF_LOSSLESS)

    def test_to_dict(self):
        """Configuration serialization."""
        c = PipelineConfig()
        d = c.to_dict()
        self.assertEqual(d['segmentation_strategy'], 'FIXED_DURATION')
        self.assertIsInstance(d['enabled_encoders'], list)


class TestVideoContainer(unittest.TestCase):
    """Test video container format."""

    def test_empty_container(self):
        """Empty container creation."""
        c = VideoContainer()
        self.assertEqual(len(c.segments), 0)

    def test_add_segment(self):
        """Add segment to container."""
        c = VideoContainer()
        record = SegmentRecord(
            segment_id=0,
            start_time=0.0,
            end_time=4.0,
            chosen_encoder_id="x265",
            encoder_parameters={"crf": 20},
            perceptual_metrics={"vmaf": 96.0},
            payload_offset=0,
            payload_size=0,
        )
        c.add_segment(record, b"test payload")
        self.assertEqual(len(c.segments), 1)
        self.assertEqual(c.segments[0].payload_size, 12)

    def test_write_read_roundtrip(self):
        """Container write/read roundtrip."""
        c1 = VideoContainer()
        record = SegmentRecord(
            segment_id=0,
            start_time=0.0,
            end_time=4.0,
            chosen_encoder_id="x265",
            encoder_parameters={"crf": 20},
            perceptual_metrics={"vmaf": 96.0},
            payload_offset=0,
            payload_size=0,
        )
        c1.add_segment(record, b"test payload data")

        with tempfile.NamedTemporaryFile(suffix='.rwvv', delete=False) as f:
            path = f.name

        try:
            c1.write(path, source_info={"test": "value"})
            c2 = VideoContainer.read(path)

            self.assertEqual(len(c2.segments), 1)
            self.assertEqual(c2.segments[0].segment_id, 0)
            self.assertEqual(c2.segments[0].chosen_encoder_id, "x265")

            payload = c2.get_segment_payload(0)
            self.assertEqual(payload, b"test payload data")
        finally:
            os.unlink(path)

    def test_manifest(self):
        """Get container manifest."""
        c = VideoContainer()
        record = SegmentRecord(
            segment_id=0,
            start_time=0.0,
            end_time=4.0,
            chosen_encoder_id="x264",
            encoder_parameters={},
            perceptual_metrics={},
            payload_offset=0,
            payload_size=0,
        )
        c.add_segment(record, b"data")

        m = c.get_manifest()
        self.assertEqual(m['magic'], 'RWVV')
        self.assertEqual(m['version'], 1)
        self.assertEqual(m['segment_count'], 1)


class TestPipeline(unittest.TestCase):
    """Test video pipeline."""

    def test_pipeline_init(self):
        """Pipeline initialization."""
        p = VideoPipeline()
        self.assertIsNotNone(p.config)

    def test_pipeline_with_config(self):
        """Pipeline with custom config."""
        config = PipelineConfig(segment_duration=2.0)
        p = VideoPipeline(config)
        self.assertEqual(p.config.segment_duration, 2.0)

    def test_pipeline_nonexistent_input(self):
        """Pipeline with nonexistent input."""
        p = VideoPipeline()
        result = p.run("/nonexistent/file.mp4", "/tmp/out.mp4")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error.lower())


class TestPipelineResult(unittest.TestCase):
    """Test pipeline result."""

    def test_compression_ratio(self):
        """Compression ratio calculation."""
        r = PipelineResult(
            input_path="in.mp4",
            output_path="out.mp4",
            segments=[],
            total_input_size=1000000,
            total_output_size=500000,
            total_time=1.0,
            config=PipelineConfig(),
            success=True,
        )
        self.assertEqual(r.compression_ratio, 0.5)

    def test_passed_all_gates(self):
        """Gate pass checking."""
        segment = SegmentResult(
            segment=Segment(0, 0, 4),
            chosen_encoder=EncoderConfig(EncoderID.X264),
            metrics=PerceptualMetrics(vmaf=96),
            input_size=1000,
            output_size=500,
            encode_time=1.0,
            passed_gate=True,
        )
        r = PipelineResult(
            input_path="in.mp4",
            output_path="out.mp4",
            segments=[segment],
            total_input_size=1000,
            total_output_size=500,
            total_time=1.0,
            config=PipelineConfig(),
            success=True,
        )
        self.assertTrue(r.passed_all_gates)

    def test_save_manifest(self):
        """Manifest saving."""
        r = PipelineResult(
            input_path="in.mp4",
            output_path="out.mp4",
            segments=[],
            total_input_size=1000,
            total_output_size=500,
            total_time=1.0,
            config=PipelineConfig(),
            success=True,
        )

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            path = f.name

        try:
            r.save_manifest(path)
            with open(path) as f:
                m = json.load(f)
            self.assertEqual(m['input_path'], 'in.mp4')
            self.assertTrue(m['success'])
        finally:
            os.unlink(path)


class TestScenarios(unittest.TestCase):
    """Test predefined scenarios."""

    def test_scenarios_defined(self):
        """Scenarios are defined."""
        self.assertIn('sd_to_4k_archival', SCENARIOS)
        self.assertIn('hd_to_8k_premium', SCENARIOS)
        self.assertIn('realtime_broadcast', SCENARIOS)

    def test_scenario_structure(self):
        """Scenario structure is correct."""
        for name, scenario in SCENARIOS.items():
            self.assertIn('description', scenario)
            self.assertIn('input_resolution', scenario)
            self.assertIn('output_resolution', scenario)


if __name__ == '__main__':
    unittest.main()
