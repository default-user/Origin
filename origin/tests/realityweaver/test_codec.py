"""Tests for RW-1: Codec core stubs and determinism."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.codec import (
    compress_zlib,
    decompress_zlib,
    identity_codec,
    select_best_codec,
    verify_roundtrip,
)


class TestCodecDeterminism:
    """DT-T1/DT-T2 partial: codec operations are deterministic."""

    def test_zlib_roundtrip(self):
        data = b"hello world" * 100
        assert verify_roundtrip(data)

    def test_zlib_deterministic(self):
        data = b"determinism test data"
        r1 = compress_zlib(data)
        r2 = compress_zlib(data)
        assert r1.data == r2.data
        assert r1.sha256_original == r2.sha256_original

    def test_identity_codec(self):
        data = b"raw bytes"
        result = identity_codec(data)
        assert result.data == data
        assert result.codec_id == "identity"
        assert result.original_size == result.compressed_size

    def test_select_best_codec(self):
        data = b"a" * 10000  # highly compressible
        result = select_best_codec(data)
        assert result.compressed_size <= len(data)

    def test_decompress_size_mismatch_fails(self):
        data = b"test"
        compressed = compress_zlib(data)
        try:
            decompress_zlib(compressed.data, expected_size=999)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "mismatch" in str(e)

    def test_empty_data(self):
        assert verify_roundtrip(b"")
