# RealityWeaverMusic Types
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Core types for RealityWeaverMusic (RXM1) container format.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Any


# RXM1 Container Constants
RXM1_MAGIC = b'RXM1'
RXM1_VERSION = 1

# Header flags
RXM1_FLAG_HAS_SHA256 = 0x01
RXM1_FLAG_HAS_AUDIO = 0x02
RXM1_FLAG_HAS_SYNC = 0x04

# Chunk type FourCC identifiers
CHUNK_META = b'META'
CHUNK_SCOR = b'SCOR'
CHUNK_SYNC = b'SYNC'
CHUNK_AUDI = b'AUDI'

# Required chunks for each mode
REQUIRED_CHUNKS_SCORE_ONLY = {CHUNK_META, CHUNK_SCOR}
REQUIRED_CHUNKS_SCORE_PLUS_AUDIO = {CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI}

# Known chunk types (for forward-compatibility: unknown chunks are preserved)
KNOWN_CHUNK_TYPES = {CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI}


class RXMMode(str, Enum):
    """Operating modes for RXM container."""
    SCORE_ONLY = "score_only"
    SCORE_PLUS_AUDIO = "score_plus_audio"


@dataclass
class SyncEntry:
    """A single synchronization anchor point."""
    score_tick: int
    audio_frame: int


@dataclass
class RXMConfig:
    """Configuration for RXM container packing."""

    # Include SHA-256 of all chunk data for integrity
    include_sha256: bool = False

    # RWV1 compression settings for SCOR and AUDI chunks
    rwv1_block_size: int = 1 << 20
    rwv1_allow_bz2: bool = False
    rwv1_allow_lzma: bool = False

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.rwv1_block_size < 1024:
            raise ValueError("rwv1_block_size must be >= 1024")
        if self.rwv1_block_size > 64 * 1024 * 1024:
            raise ValueError("rwv1_block_size must be <= 64 MiB")


@dataclass
class ChunkInfo:
    """Information about a single chunk in the container."""
    chunk_type: bytes
    data_size: int

    @property
    def type_str(self) -> str:
        return self.chunk_type.decode('ascii', errors='replace')


@dataclass
class RXMContainerInfo:
    """Information about an RXM1 container."""
    version: int
    flags: int
    chunk_count: int
    chunks: List[ChunkInfo] = field(default_factory=list)
    has_sha256: bool = False
    has_audio: bool = False
    has_sync: bool = False
    sha256_hex: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    sync_entry_count: int = 0
    mode: str = "score_only"
    total_size: int = 0


@dataclass
class RXMMetadata:
    """Metadata for an RXM container."""
    title: str = ""
    composer: str = ""
    tempo_bpm: float = 120.0
    time_signature: str = "4/4"
    key_signature: str = "C"
    description: str = ""
    score_format: str = "midi"
    audio_format: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "title": self.title,
            "composer": self.composer,
            "tempo_bpm": self.tempo_bpm,
            "time_signature": self.time_signature,
            "key_signature": self.key_signature,
            "description": self.description,
            "score_format": self.score_format,
        }
        if self.audio_format:
            d["audio_format"] = self.audio_format
        if self.extra:
            d["extra"] = self.extra
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'RXMMetadata':
        return cls(
            title=d.get("title", ""),
            composer=d.get("composer", ""),
            tempo_bpm=d.get("tempo_bpm", 120.0),
            time_signature=d.get("time_signature", "4/4"),
            key_signature=d.get("key_signature", "C"),
            description=d.get("description", ""),
            score_format=d.get("score_format", "midi"),
            audio_format=d.get("audio_format", ""),
            extra=d.get("extra", {}),
        )
