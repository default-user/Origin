# RealityWeaver (RWV1) - Container Format + Race Compressor
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RealityWeaver: Block-based compression container with adaptive codec racing.

Features:
- RWV1 container format with per-block codec selection
- Race compressor that picks the smallest result
- MO+zlib dictionary rewrite for text-heavy data
- Multiple branch encoders (zlib, bz2, lzma)
- SHA-256 verification for integrity

Core invariant: decompress(compress(x)) == x
"""

from .container import (
    compress,
    decompress,
    compress_bytes,
    decompress_bytes,
)
from .types import (
    RWV1Config,
    ContainerInfo,
    BlockInfo,
    BranchID,
)

__all__ = [
    'compress',
    'decompress',
    'compress_bytes',
    'decompress_bytes',
    'RWV1Config',
    'ContainerInfo',
    'BlockInfo',
    'BranchID',
]

__version__ = '1.0.0'
