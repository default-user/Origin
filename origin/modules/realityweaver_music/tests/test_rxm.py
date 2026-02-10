#!/usr/bin/env python3
# RealityWeaverMusic Test Suite
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Test suite for RealityWeaverMusic (RXM1) container format.
"""

import hashlib
import json
import struct
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container import (
    pack_bytes,
    unpack_bytes,
    validate_container,
    get_container_info,
    validate_sync,
    tick_to_frame,
    frame_to_tick,
    RXMError,
)
from rxm_types import (
    RXMConfig,
    RXMMetadata,
    SyncEntry,
    RXM1_MAGIC,
    RXM1_VERSION,
    RXM1_FLAG_HAS_SHA256,
    RXM1_FLAG_HAS_AUDIO,
    RXM1_FLAG_HAS_SYNC,
    CHUNK_META,
    CHUNK_SCOR,
    CHUNK_SYNC,
    CHUNK_AUDI,
)


class TestScoreOnlyRoundtrip(unittest.TestCase):
    """Test score-only mode pack/unpack roundtrip."""

    def test_minimal_score(self):
        """Minimal score data should roundtrip."""
        score = b'MThd\x00\x00\x00\x06\x00\x01\x00\x01\x00\x60'
        metadata = RXMMetadata(title="Minimal", composer="Test")
        container = pack_bytes(metadata, score)
        result = unpack_bytes(container)

        self.assertEqual(result['score_data'], score)
        self.assertEqual(result['metadata'].title, "Minimal")
        self.assertEqual(result['metadata'].composer, "Test")
        self.assertIsNone(result['audio_data'])
        self.assertIsNone(result['sync_entries'])

    def test_large_score(self):
        """Large score data should roundtrip."""
        score = bytes(range(256)) * 100  # 25,600 bytes
        metadata = RXMMetadata(title="Large Score", tempo_bpm=140.0)
        container = pack_bytes(metadata, score)
        result = unpack_bytes(container)

        self.assertEqual(result['score_data'], score)
        self.assertEqual(result['metadata'].tempo_bpm, 140.0)

    def test_repetitive_score(self):
        """Repetitive score should compress well and roundtrip."""
        # Simulated MIDI-like repetitive data
        score = (b'MThd\x00\x00\x00\x06' + b'\x90\x3C\x40\x80\x3C\x00' * 500)
        metadata = RXMMetadata(title="Repetitive")
        container = pack_bytes(metadata, score)
        result = unpack_bytes(container)

        self.assertEqual(result['score_data'], score)
        # Container should be smaller than raw score due to compression
        self.assertLess(len(container), len(score) + 500)

    def test_empty_score(self):
        """Empty score should be rejected."""
        metadata = RXMMetadata(title="Empty")
        with self.assertRaises(RXMError):
            pack_bytes(metadata, b'', b'')


class TestScorePlusAudioRoundtrip(unittest.TestCase):
    """Test score+audio mode pack/unpack roundtrip."""

    def test_basic_audio(self):
        """Basic score+audio should roundtrip."""
        score = b'MThd' + b'\x00' * 50
        audio = bytes(range(256)) * 40  # 10,240 bytes
        sync = [SyncEntry(i * 480, i * 44100) for i in range(5)]
        metadata = RXMMetadata(title="Audio Test", audio_format="wav")

        container = pack_bytes(metadata, score, audio, sync)
        result = unpack_bytes(container)

        self.assertEqual(result['score_data'], score)
        self.assertEqual(result['audio_data'], audio)
        self.assertEqual(len(result['sync_entries']), 5)
        self.assertEqual(result['metadata'].audio_format, "wav")

    def test_sync_entries_preserved(self):
        """Sync entries should be exactly preserved."""
        score = b'score'
        audio = b'audio' * 100
        sync = [
            SyncEntry(0, 0),
            SyncEntry(480, 44100),
            SyncEntry(960, 88200),
            SyncEntry(1440, 132300),
        ]
        metadata = RXMMetadata(title="Sync Test")

        container = pack_bytes(metadata, score, audio, sync)
        result = unpack_bytes(container)

        for i, entry in enumerate(result['sync_entries']):
            self.assertEqual(entry.score_tick, sync[i].score_tick)
            self.assertEqual(entry.audio_frame, sync[i].audio_frame)

    def test_audio_without_sync_rejected(self):
        """Audio without sync should be rejected."""
        metadata = RXMMetadata(title="No Sync")
        with self.assertRaises(RXMError):
            pack_bytes(metadata, b'score', b'audio')


class TestSyncValidation(unittest.TestCase):
    """Test sync map validation."""

    def test_monotonic_valid(self):
        """Strictly monotonic sync should pass."""
        sync = [
            SyncEntry(0, 0),
            SyncEntry(100, 4410),
            SyncEntry(200, 8820),
            SyncEntry(300, 13230),
        ]
        validate_sync(sync)  # Should not raise

    def test_non_monotonic_tick_rejected(self):
        """Non-monotonic score_tick should fail."""
        sync = [
            SyncEntry(100, 4410),
            SyncEntry(50, 8820),  # Tick decreases
        ]
        with self.assertRaises(RXMError) as ctx:
            validate_sync(sync)
        self.assertIn("monotonic", str(ctx.exception).lower())

    def test_non_monotonic_frame_rejected(self):
        """Non-monotonic audio_frame should fail."""
        sync = [
            SyncEntry(100, 8820),
            SyncEntry(200, 4410),  # Frame decreases
        ]
        with self.assertRaises(RXMError) as ctx:
            validate_sync(sync)
        self.assertIn("monotonic", str(ctx.exception).lower())

    def test_duplicate_tick_rejected(self):
        """Duplicate score_tick should fail (not strictly increasing)."""
        sync = [
            SyncEntry(100, 4410),
            SyncEntry(100, 8820),  # Same tick
        ]
        with self.assertRaises(RXMError):
            validate_sync(sync)

    def test_duplicate_frame_rejected(self):
        """Duplicate audio_frame should fail (not strictly increasing)."""
        sync = [
            SyncEntry(100, 4410),
            SyncEntry(200, 4410),  # Same frame
        ]
        with self.assertRaises(RXMError):
            validate_sync(sync)

    def test_single_entry_valid(self):
        """Single entry sync should pass."""
        sync = [SyncEntry(0, 0)]
        validate_sync(sync)  # Should not raise

    def test_empty_sync_valid(self):
        """Empty sync should pass."""
        validate_sync([])  # Should not raise


class TestSyncConversion(unittest.TestCase):
    """Test tick<->frame conversion helpers."""

    def setUp(self):
        self.sync = [
            SyncEntry(0, 0),
            SyncEntry(480, 44100),
            SyncEntry(960, 88200),
        ]

    def test_tick_to_frame_exact(self):
        """Exact anchor points should map directly."""
        self.assertEqual(tick_to_frame(self.sync, 0), 0)
        self.assertEqual(tick_to_frame(self.sync, 480), 44100)
        self.assertEqual(tick_to_frame(self.sync, 960), 88200)

    def test_tick_to_frame_interpolated(self):
        """Mid-point should interpolate linearly."""
        frame = tick_to_frame(self.sync, 240)
        self.assertEqual(frame, 22050)

    def test_tick_to_frame_clamp_low(self):
        """Below first anchor should clamp."""
        frame = tick_to_frame(self.sync, -100)
        self.assertEqual(frame, 0)

    def test_tick_to_frame_clamp_high(self):
        """Above last anchor should clamp."""
        frame = tick_to_frame(self.sync, 2000)
        self.assertEqual(frame, 88200)

    def test_frame_to_tick_exact(self):
        """Exact anchor points should map directly."""
        self.assertEqual(frame_to_tick(self.sync, 0), 0)
        self.assertEqual(frame_to_tick(self.sync, 44100), 480)
        self.assertEqual(frame_to_tick(self.sync, 88200), 960)

    def test_frame_to_tick_interpolated(self):
        """Mid-point should interpolate linearly."""
        tick = frame_to_tick(self.sync, 22050)
        self.assertEqual(tick, 240)

    def test_empty_sync_raises(self):
        """Empty sync should raise error."""
        with self.assertRaises(RXMError):
            tick_to_frame([], 100)
        with self.assertRaises(RXMError):
            frame_to_tick([], 100)


class TestContainerValidation(unittest.TestCase):
    """Test container validation."""

    def test_valid_score_only(self):
        """Valid score-only container should validate."""
        metadata = RXMMetadata(title="Valid")
        container = pack_bytes(metadata, b'score data')
        is_valid, errors = validate_container(container)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_valid_score_plus_audio(self):
        """Valid score+audio container should validate."""
        sync = [SyncEntry(0, 0), SyncEntry(100, 4410)]
        metadata = RXMMetadata(title="Valid Audio")
        container = pack_bytes(metadata, b'score', b'audio' * 10, sync)
        is_valid, errors = validate_container(container)
        self.assertTrue(is_valid)

    def test_invalid_magic(self):
        """Invalid magic should fail."""
        is_valid, errors = validate_container(b'XXXX' + b'\x00' * 20)
        self.assertFalse(is_valid)
        self.assertTrue(any("magic" in e.lower() for e in errors))

    def test_truncated_container(self):
        """Truncated container should fail."""
        is_valid, errors = validate_container(b'RXM1\x01')
        self.assertFalse(is_valid)

    def test_invalid_version(self):
        """Invalid version should fail."""
        container = bytearray(b'RXM1\x02\x00\x00\x00')
        is_valid, errors = validate_container(bytes(container))
        self.assertFalse(is_valid)
        self.assertTrue(any("version" in e.lower() for e in errors))


class TestSHA256Integrity(unittest.TestCase):
    """Test SHA-256 integrity checking."""

    def test_sha256_roundtrip(self):
        """SHA-256 should verify on valid container."""
        metadata = RXMMetadata(title="Integrity Test")
        config = RXMConfig(include_sha256=True)
        container = pack_bytes(metadata, b'test data', config=config)
        result = unpack_bytes(container)
        self.assertEqual(result['score_data'], b'test data')

    def test_sha256_flag_set(self):
        """SHA-256 flag should be set in header."""
        config = RXMConfig(include_sha256=True)
        container = pack_bytes(RXMMetadata(), b'test', config=config)
        self.assertTrue(container[5] & RXM1_FLAG_HAS_SHA256)

    def test_sha256_corruption_detected(self):
        """Corrupted data should fail SHA-256 check."""
        config = RXMConfig(include_sha256=True)
        container = bytearray(pack_bytes(RXMMetadata(title="Corrupt"), b'test', config=config))

        # Corrupt a byte near the end
        container[-1] ^= 0xFF

        is_valid, errors = validate_container(bytes(container))
        # Should fail with either SHA-256 mismatch or decompression error
        self.assertFalse(is_valid)


class TestContainerInfo(unittest.TestCase):
    """Test container info extraction."""

    def test_score_only_info(self):
        """Score-only info should be correct."""
        metadata = RXMMetadata(title="Info Test", composer="Tester")
        container = pack_bytes(metadata, b'score data')
        info = get_container_info(container)

        self.assertEqual(info.version, 1)
        self.assertEqual(info.mode, "score_only")
        self.assertFalse(info.has_audio)
        self.assertFalse(info.has_sync)
        self.assertEqual(info.chunk_count, 2)  # META + SCOR

    def test_audio_info(self):
        """Score+audio info should be correct."""
        sync = [SyncEntry(0, 0), SyncEntry(100, 4410)]
        metadata = RXMMetadata(title="Audio Info")
        container = pack_bytes(metadata, b'score', b'audio' * 10, sync)
        info = get_container_info(container)

        self.assertEqual(info.mode, "score_plus_audio")
        self.assertTrue(info.has_audio)
        self.assertTrue(info.has_sync)
        self.assertEqual(info.chunk_count, 4)  # META + SCOR + SYNC + AUDI

    def test_metadata_extracted(self):
        """Metadata should be extractable from info."""
        metadata = RXMMetadata(title="Extract Me", tempo_bpm=90.0)
        container = pack_bytes(metadata, b'score')
        info = get_container_info(container)

        self.assertIsNotNone(info.metadata)
        self.assertEqual(info.metadata['title'], "Extract Me")
        self.assertEqual(info.metadata['tempo_bpm'], 90.0)


class TestHeaderFormat(unittest.TestCase):
    """Test binary header format correctness."""

    def test_magic(self):
        """Container should start with RXM1 magic."""
        container = pack_bytes(RXMMetadata(), b'test')
        self.assertEqual(container[:4], RXM1_MAGIC)

    def test_version(self):
        """Version should be 1."""
        container = pack_bytes(RXMMetadata(), b'test')
        self.assertEqual(container[4], RXM1_VERSION)

    def test_flags_score_only(self):
        """Score-only flags should not have audio or sync bits."""
        container = pack_bytes(RXMMetadata(), b'test')
        flags = container[5]
        self.assertFalse(flags & RXM1_FLAG_HAS_AUDIO)
        self.assertFalse(flags & RXM1_FLAG_HAS_SYNC)

    def test_flags_audio(self):
        """Audio mode flags should have audio and sync bits."""
        sync = [SyncEntry(0, 0), SyncEntry(100, 4410)]
        container = pack_bytes(RXMMetadata(), b'score', b'audio' * 10, sync)
        flags = container[5]
        self.assertTrue(flags & RXM1_FLAG_HAS_AUDIO)
        self.assertTrue(flags & RXM1_FLAG_HAS_SYNC)

    def test_chunk_count(self):
        """Chunk count should match number of chunks."""
        container = pack_bytes(RXMMetadata(), b'test')
        chunk_count = struct.unpack(">H", container[6:8])[0]
        self.assertEqual(chunk_count, 2)  # META + SCOR


class TestForwardCompatibility(unittest.TestCase):
    """Test that unknown chunks are preserved."""

    def test_extra_chunks_preserved(self):
        """Unknown chunks should survive roundtrip."""
        extras = [(b'XTRA', b'extra data'), (b'TEST', b'\x01\x02\x03')]
        metadata = RXMMetadata(title="Forward Compat")
        container = pack_bytes(metadata, b'score', extra_chunks=extras)
        result = unpack_bytes(container)

        self.assertEqual(len(result['extra_chunks']), 2)
        self.assertEqual(result['extra_chunks'][0], (b'XTRA', b'extra data'))
        self.assertEqual(result['extra_chunks'][1], (b'TEST', b'\x01\x02\x03'))

    def test_invalid_fourcc_length_rejected(self):
        """FourCC with wrong length should be rejected."""
        with self.assertRaises(RXMError):
            pack_bytes(RXMMetadata(), b'score', extra_chunks=[(b'XX', b'data')])


class TestDeterminism(unittest.TestCase):
    """Test deterministic behavior."""

    def test_same_output(self):
        """Same input should always produce same output."""
        metadata = RXMMetadata(title="Deterministic")
        score = b'deterministic test data' * 100
        results = [pack_bytes(metadata, score) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_config_determinism(self):
        """Same config should produce same output."""
        metadata = RXMMetadata(title="Config Test")
        score = b'config test' * 100
        config = RXMConfig(rwv1_block_size=2048, include_sha256=True)
        results = [pack_bytes(metadata, score, config=config) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))


class TestConfig(unittest.TestCase):
    """Test configuration validation."""

    def test_block_size_too_small(self):
        """Block size < 1024 should fail."""
        config = RXMConfig(rwv1_block_size=100)
        with self.assertRaises(ValueError):
            config.validate()

    def test_block_size_too_large(self):
        """Block size > 64 MiB should fail."""
        config = RXMConfig(rwv1_block_size=128 * 1024 * 1024)
        with self.assertRaises(ValueError):
            config.validate()

    def test_valid_config(self):
        """Default config should be valid."""
        config = RXMConfig()
        config.validate()  # Should not raise


if __name__ == '__main__':
    unittest.main()
