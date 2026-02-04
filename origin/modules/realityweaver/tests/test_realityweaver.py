#!/usr/bin/env python3
# RealityWeaver Test Suite
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Test suite for RealityWeaver compression.
"""

import hashlib
import struct
import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from container import (
    compress_bytes,
    decompress_bytes,
    get_container_info,
    RWV1Error,
)
from types import RWV1Config, BranchID, RWV1_MAGIC
from mo_zlib import mo_zlib_encode, mo_zlib_decode, MOZlibError


class TestMOZlib(unittest.TestCase):
    """Test MO+zlib branch encoder."""

    def test_empty_data(self):
        """Empty data should roundtrip."""
        data = b''
        encoded = mo_zlib_encode(data)
        decoded = mo_zlib_decode(encoded)
        self.assertEqual(decoded, data)

    def test_simple_text(self):
        """Simple text should roundtrip."""
        data = b'hello world hello world'
        encoded = mo_zlib_encode(data)
        decoded = mo_zlib_decode(encoded)
        self.assertEqual(decoded, data)

    def test_repetitive_text(self):
        """Repetitive text should compress well."""
        data = b'function test() { return true; } ' * 20
        encoded = mo_zlib_encode(data)
        decoded = mo_zlib_decode(encoded)
        self.assertEqual(decoded, data)
        # Should achieve some compression
        self.assertLess(len(encoded), len(data))

    def test_binary_data(self):
        """Binary data should roundtrip."""
        data = bytes(range(256)) * 10
        encoded = mo_zlib_encode(data)
        decoded = mo_zlib_decode(encoded)
        self.assertEqual(decoded, data)

    def test_contains_zero_bytes(self):
        """Data with zero bytes should roundtrip."""
        data = b'\x00\x01\x02\x00\x00\x03\x04\x00'
        encoded = mo_zlib_encode(data)
        decoded = mo_zlib_decode(encoded)
        self.assertEqual(decoded, data)


class TestRWV1Container(unittest.TestCase):
    """Test RWV1 container format."""

    def test_empty_input(self):
        """Empty input should roundtrip."""
        data = b''
        compressed = compress_bytes(data)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)

    def test_header_magic(self):
        """Container should have correct magic."""
        data = b'test'
        compressed = compress_bytes(data)
        self.assertEqual(compressed[:4], RWV1_MAGIC)

    def test_header_version(self):
        """Container should have version 1."""
        data = b'test'
        compressed = compress_bytes(data)
        self.assertEqual(compressed[4], 1)

    def test_small_data(self):
        """Small data should roundtrip."""
        data = b'Hello, World!'
        compressed = compress_bytes(data)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)

    def test_large_data(self):
        """Data larger than one block should roundtrip."""
        data = b'x' * 100000
        config = RWV1Config(block_size=10000)
        compressed = compress_bytes(data, config)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)

    def test_sha256_verification(self):
        """SHA-256 verification should work."""
        data = b'Test data for integrity checking'
        config = RWV1Config(include_sha256=True)
        compressed = compress_bytes(data, config)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)

    def test_sha256_flag_set(self):
        """SHA-256 flag should be set in header."""
        data = b'test'
        config = RWV1Config(include_sha256=True)
        compressed = compress_bytes(data, config)
        flags = compressed[5]
        self.assertTrue(flags & 0x01)

    def test_container_info(self):
        """Container info should parse correctly."""
        data = b'x' * 5000
        config = RWV1Config(block_size=1000)
        compressed = compress_bytes(data, config)
        info = get_container_info(compressed)

        self.assertEqual(info.version, 1)
        self.assertEqual(info.block_size, 1000)
        self.assertEqual(info.block_count, 5)
        self.assertEqual(info.total_raw_size, 5000)

    def test_branch_selection(self):
        """Race should pick smallest result."""
        # Repetitive text favors MO+zlib
        data = (b'function test() { return "hello"; } ' * 50)
        compressed = compress_bytes(data)
        info = get_container_info(compressed)

        # Should have selected some branch
        self.assertGreater(info.block_count, 0)

    def test_zlib_only(self):
        """Should work with only zlib enabled."""
        data = b'test data' * 100
        config = RWV1Config(allow_zlib=True, allow_mo_zlib=False)
        compressed = compress_bytes(data, config)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)

        info = get_container_info(compressed)
        usage = info.branch_usage()
        self.assertEqual(usage.get('ZLIB', 0), info.block_count)

    def test_mo_zlib_only(self):
        """Should work with only MO+zlib enabled."""
        data = b'test data' * 100
        config = RWV1Config(allow_zlib=False, allow_mo_zlib=True)
        compressed = compress_bytes(data, config)
        decompressed = decompress_bytes(compressed)
        self.assertEqual(decompressed, data)


class TestRWV1Errors(unittest.TestCase):
    """Test error handling."""

    def test_invalid_magic(self):
        """Invalid magic should fail."""
        data = b'XXXX' + bytes(10)
        with self.assertRaises(RWV1Error):
            decompress_bytes(data)

    def test_truncated_header(self):
        """Truncated header should fail."""
        data = RWV1_MAGIC + bytes(5)
        with self.assertRaises(RWV1Error):
            decompress_bytes(data)

    def test_sha256_mismatch(self):
        """SHA-256 mismatch should fail."""
        data = b'test'
        config = RWV1Config(include_sha256=True)
        compressed = bytearray(compress_bytes(data, config))

        # Corrupt the data
        compressed[-1] ^= 0xFF

        with self.assertRaises(RWV1Error) as ctx:
            decompress_bytes(bytes(compressed))
        self.assertIn('mismatch', str(ctx.exception).lower())


class TestDeterminism(unittest.TestCase):
    """Test deterministic behavior."""

    def test_same_output(self):
        """Same input should always produce same output."""
        data = b'Deterministic test data' * 100
        results = [compress_bytes(data) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))

    def test_config_determinism(self):
        """Same config should produce same output."""
        data = b'Config test' * 100
        config = RWV1Config(block_size=500, zlib_level=6)
        results = [compress_bytes(data, config) for _ in range(5)]
        self.assertTrue(all(r == results[0] for r in results))


class TestConfig(unittest.TestCase):
    """Test configuration validation."""

    def test_block_size_validation(self):
        """Block size should be validated."""
        with self.assertRaises(ValueError):
            config = RWV1Config(block_size=100)  # Too small
            config.validate()

    def test_no_branches_enabled(self):
        """At least one branch must be enabled."""
        with self.assertRaises(ValueError):
            config = RWV1Config(
                allow_zlib=False,
                allow_mo_zlib=False,
                allow_bz2=False,
                allow_lzma=False,
            )
            config.validate()

    def test_enabled_branches(self):
        """Enabled branches list should be correct."""
        config = RWV1Config(
            allow_zlib=True,
            allow_mo_zlib=True,
            allow_bz2=False,
            allow_lzma=False,
        )
        branches = config.enabled_branches()
        self.assertEqual(len(branches), 2)
        self.assertIn(BranchID.ZLIB, branches)
        self.assertIn(BranchID.MO_ZLIB, branches)


if __name__ == '__main__':
    unittest.main()
