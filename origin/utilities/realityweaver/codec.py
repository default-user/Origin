"""
RW-1: Codec core stubs and determinism scaffold.

Stub implementations for codec operations. These provide the interface
contract and determinism guarantees. Full codec racing is in the existing
realityweaver module; these stubs provide the WeaverPack-level abstraction.
"""

from __future__ import annotations

import hashlib
import zlib
from dataclasses import dataclass

from .primitives import sha256_bytes


@dataclass
class CodecResult:
    """Result of a codec operation."""

    data: bytes
    codec_id: str
    original_size: int
    compressed_size: int
    sha256_original: str
    deterministic: bool = True


def compress_zlib(data: bytes, level: int = 9) -> CodecResult:
    """Deterministic zlib compression."""
    compressed = zlib.compress(data, level)
    return CodecResult(
        data=compressed,
        codec_id="zlib",
        original_size=len(data),
        compressed_size=len(compressed),
        sha256_original=sha256_bytes(data),
    )


def decompress_zlib(data: bytes, expected_size: int | None = None) -> bytes:
    """Deterministic zlib decompression. Fail-closed on error."""
    result = zlib.decompress(data)
    if expected_size is not None and len(result) != expected_size:
        raise ValueError(
            f"Decompressed size mismatch: expected {expected_size}, got {len(result)}"
        )
    return result


def verify_roundtrip(data: bytes, level: int = 9) -> bool:
    """Verify compress(decompress(x)) == x for given data."""
    compressed = compress_zlib(data, level)
    decompressed = decompress_zlib(compressed.data, compressed.original_size)
    return decompressed == data


def identity_codec(data: bytes) -> CodecResult:
    """Identity codec (no compression). Used as baseline."""
    return CodecResult(
        data=data,
        codec_id="identity",
        original_size=len(data),
        compressed_size=len(data),
        sha256_original=sha256_bytes(data),
    )


def select_best_codec(data: bytes) -> CodecResult:
    """
    Race codecs and select the smallest output.

    Stub: only races zlib vs identity. Full racing with MO+zlib, bz2,
    lzma is in the existing realityweaver module.
    """
    candidates = [
        compress_zlib(data),
        identity_codec(data),
    ]
    return min(candidates, key=lambda c: c.compressed_size)
