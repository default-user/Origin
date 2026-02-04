# RealityWeaver Types
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Core types for RealityWeaver container format.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import List, Optional


# RWV1 Container Constants
RWV1_MAGIC = b'RWV1'
RWV1_VERSION = 1

# Header flags
RWV1_FLAG_RAW_SHA256_PRESENT = 0x01


class BranchID(IntEnum):
    """
    Codec branch identifiers.

    Each block stores one of these IDs to indicate
    which codec was used for compression.
    """
    ZLIB = 0        # zlib (deflate)
    MO_ZLIB = 1     # Middle-out dictionary rewrite + zlib
    BZ2 = 2         # bzip2
    LZMA = 3        # lzma/xz


@dataclass
class RWV1Config:
    """Configuration for RealityWeaver compression."""

    # Block size (default 1 MiB)
    block_size: int = 1 << 20

    # Branch enablement
    allow_zlib: bool = True
    allow_mo_zlib: bool = True
    allow_bz2: bool = False
    allow_lzma: bool = False

    # Compression levels
    zlib_level: int = 9
    bz2_level: int = 9
    lzma_preset: int = 6

    # MO+zlib config
    mo_max_entries: int = 200

    # Enable probe gating (heuristic pre-filter)
    probe: bool = False

    # Include SHA-256 of original data
    include_sha256: bool = False

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.block_size < 1024:
            raise ValueError("block_size must be >= 1024")
        if self.block_size > 64 * 1024 * 1024:
            raise ValueError("block_size must be <= 64 MiB")
        if not (1 <= self.zlib_level <= 9):
            raise ValueError("zlib_level must be 1-9")
        if not (1 <= self.bz2_level <= 9):
            raise ValueError("bz2_level must be 1-9")
        if not (0 <= self.lzma_preset <= 9):
            raise ValueError("lzma_preset must be 0-9")
        if self.mo_max_entries < 1:
            raise ValueError("mo_max_entries must be >= 1")
        if not any([self.allow_zlib, self.allow_mo_zlib,
                    self.allow_bz2, self.allow_lzma]):
            raise ValueError("At least one branch must be enabled")

    def enabled_branches(self) -> List[BranchID]:
        """Return list of enabled branch IDs."""
        branches = []
        if self.allow_zlib:
            branches.append(BranchID.ZLIB)
        if self.allow_mo_zlib:
            branches.append(BranchID.MO_ZLIB)
        if self.allow_bz2:
            branches.append(BranchID.BZ2)
        if self.allow_lzma:
            branches.append(BranchID.LZMA)
        return branches


@dataclass
class BlockInfo:
    """Information about a single compressed block."""
    index: int
    branch_id: BranchID
    raw_len: int
    payload_len: int
    ratio: float = 0.0

    def __post_init__(self):
        if self.raw_len > 0:
            self.ratio = self.payload_len / self.raw_len


@dataclass
class ContainerInfo:
    """Information about an RWV1 container."""
    version: int
    flags: int
    block_size: int
    block_count: int
    raw_sha256: Optional[bytes]
    blocks: List[BlockInfo] = field(default_factory=list)
    total_raw_size: int = 0
    total_payload_size: int = 0

    @property
    def has_sha256(self) -> bool:
        return bool(self.flags & RWV1_FLAG_RAW_SHA256_PRESENT)

    @property
    def overall_ratio(self) -> float:
        if self.total_raw_size == 0:
            return 0.0
        return self.total_payload_size / self.total_raw_size

    def branch_usage(self) -> dict:
        """Return count of blocks per branch."""
        usage = {}
        for block in self.blocks:
            name = BranchID(block.branch_id).name
            usage[name] = usage.get(name, 0) + 1
        return usage
