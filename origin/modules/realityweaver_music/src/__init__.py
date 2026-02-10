# RealityWeaverMusic (RXM1) - Reality Weaver Music Container
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RealityWeaverMusic: Chunk-based music container with score and synced audio.

Features:
- RXM1 container format with META, SCOR, SYNC, and AUDI chunks
- Score-only mode (MIDI data compressed with RWV1)
- Score+audio mode with monotonic sync map
- RWV1 codec racing for compression (zlib, MO+zlib, bz2, lzma)
- SHA-256 verification for integrity
- Forward compatibility: unknown chunks preserved

Core invariant: unpack(pack(score, audio, sync, meta)) reproduces all inputs.
"""

from .container import (
    pack,
    unpack,
    pack_bytes,
    unpack_bytes,
    validate_container,
    get_container_info,
    validate_sync,
    tick_to_frame,
    frame_to_tick,
    RXMError,
)
from .rxm_types import (
    RXMConfig,
    RXMContainerInfo,
    RXMMetadata,
    ChunkInfo,
    SyncEntry,
    RXMMode,
)

__all__ = [
    'pack',
    'unpack',
    'pack_bytes',
    'unpack_bytes',
    'validate_container',
    'get_container_info',
    'validate_sync',
    'tick_to_frame',
    'frame_to_tick',
    'RXMError',
    'RXMConfig',
    'RXMContainerInfo',
    'RXMMetadata',
    'ChunkInfo',
    'SyncEntry',
    'RXMMode',
]

__version__ = '1.0.0'
