# RWV1 Container Format
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RWV1 Container encoder/decoder with race compressor.

BINARY FORMAT:
  MAGIC: "RWV1" (4 bytes)
  VERSION: 1 (u8)
  FLAGS: u8
    bit0 = raw_sha256_present
  BLOCK_SIZE: u32 big-endian
  BLOCK_COUNT: u32 big-endian
  [RAW_SHA256: 32 bytes if flags&1]

  BLOCK RECORDS (repeated block_count times):
    branch_id: u8
    raw_len: u32 big-endian
    payload_len: u32 big-endian
    payload: bytes[payload_len]

Core invariant: decompress(compress(x)) == x
"""

import hashlib
import struct
import zlib
from typing import Optional, Tuple, List, BinaryIO

from .types import (
    RWV1_MAGIC,
    RWV1_VERSION,
    RWV1_FLAG_RAW_SHA256_PRESENT,
    RWV1Config,
    ContainerInfo,
    BlockInfo,
    BranchID,
)
from .mo_zlib import mo_zlib_encode, mo_zlib_decode, MOZlibError


class RWV1Error(Exception):
    """Error in RWV1 container operations."""
    pass


# Optional imports for additional branches
try:
    import bz2
    HAS_BZ2 = True
except ImportError:
    HAS_BZ2 = False

try:
    import lzma
    HAS_LZMA = True
except ImportError:
    HAS_LZMA = False


def _encode_block(data: bytes, branch_id: BranchID,
                  config: RWV1Config) -> bytes:
    """Encode a single block with the specified branch."""
    if branch_id == BranchID.ZLIB:
        return zlib.compress(data, level=config.zlib_level)

    elif branch_id == BranchID.MO_ZLIB:
        return mo_zlib_encode(data,
                              max_entries=config.mo_max_entries,
                              zlib_level=config.zlib_level)

    elif branch_id == BranchID.BZ2:
        if not HAS_BZ2:
            raise RWV1Error("bz2 not available")
        return bz2.compress(data, compresslevel=config.bz2_level)

    elif branch_id == BranchID.LZMA:
        if not HAS_LZMA:
            raise RWV1Error("lzma not available")
        return lzma.compress(data, preset=config.lzma_preset)

    else:
        raise RWV1Error(f"Unknown branch ID: {branch_id}")


def _decode_block(payload: bytes, branch_id: BranchID,
                  expected_len: int) -> bytes:
    """Decode a single block payload."""
    if branch_id == BranchID.ZLIB:
        data = zlib.decompress(payload)

    elif branch_id == BranchID.MO_ZLIB:
        data = mo_zlib_decode(payload)

    elif branch_id == BranchID.BZ2:
        if not HAS_BZ2:
            raise RWV1Error("bz2 not available")
        data = bz2.decompress(payload)

    elif branch_id == BranchID.LZMA:
        if not HAS_LZMA:
            raise RWV1Error("lzma not available")
        data = lzma.decompress(payload)

    else:
        raise RWV1Error(f"Unknown branch ID: {branch_id}")

    if len(data) != expected_len:
        raise RWV1Error(
            f"Block size mismatch: expected {expected_len}, got {len(data)}")

    return data


def _race_encode_block(data: bytes, branches: List[BranchID],
                       config: RWV1Config) -> Tuple[BranchID, bytes]:
    """
    Race encode a block with all enabled branches, return smallest result.

    Returns (winning_branch_id, payload).
    """
    best_branch = None
    best_payload = None
    best_size = float('inf')

    for branch_id in branches:
        try:
            payload = _encode_block(data, branch_id, config)
            if len(payload) < best_size:
                best_size = len(payload)
                best_branch = branch_id
                best_payload = payload
        except Exception:
            # Skip failed encoders
            continue

    if best_branch is None or best_payload is None:
        raise RWV1Error("All branch encoders failed")

    return best_branch, best_payload


def _probe_gate(data: bytes) -> List[BranchID]:
    """
    Heuristic probe to filter out obviously bad codecs.

    Returns list of branches that should be tried.
    """
    # Simple heuristic: check if data looks like text
    # Text tends to have many values in printable ASCII range

    if len(data) == 0:
        return [BranchID.ZLIB]

    printable_count = sum(1 for b in data if 32 <= b <= 126)
    text_ratio = printable_count / len(data)

    # If mostly text, MO+zlib is likely to help
    if text_ratio > 0.7:
        return [BranchID.MO_ZLIB, BranchID.ZLIB]

    # For binary data, plain zlib often wins
    return [BranchID.ZLIB, BranchID.MO_ZLIB]


def compress_bytes(data: bytes, config: Optional[RWV1Config] = None) -> bytes:
    """
    Compress data to RWV1 container format.

    Args:
        data: Raw data to compress
        config: Compression configuration (uses defaults if None)

    Returns:
        RWV1 container bytes
    """
    if config is None:
        config = RWV1Config()
    config.validate()

    # Compute optional SHA-256
    raw_sha256 = hashlib.sha256(data).digest() if config.include_sha256 else None

    # Split into blocks
    blocks_data = []
    for i in range(0, len(data), config.block_size):
        block = data[i:i + config.block_size]
        blocks_data.append(block)

    if not blocks_data:
        blocks_data = [b'']  # Handle empty input

    # Get enabled branches
    enabled_branches = config.enabled_branches()

    # Encode each block
    encoded_blocks: List[Tuple[BranchID, int, bytes]] = []

    for block_data in blocks_data:
        if config.probe and len(enabled_branches) > 1:
            # Use probe gating to filter branches
            probe_branches = _probe_gate(block_data)
            branches = [b for b in probe_branches if b in enabled_branches]
            if not branches:
                branches = enabled_branches
        else:
            branches = enabled_branches

        branch_id, payload = _race_encode_block(block_data, branches, config)
        encoded_blocks.append((branch_id, len(block_data), payload))

    # Build container
    result = bytearray()

    # Header
    result.extend(RWV1_MAGIC)
    result.append(RWV1_VERSION)

    flags = 0
    if config.include_sha256:
        flags |= RWV1_FLAG_RAW_SHA256_PRESENT
    result.append(flags)

    result.extend(struct.pack(">I", config.block_size))
    result.extend(struct.pack(">I", len(encoded_blocks)))

    # Optional SHA-256
    if raw_sha256:
        result.extend(raw_sha256)

    # Block records
    for branch_id, raw_len, payload in encoded_blocks:
        result.append(branch_id)
        result.extend(struct.pack(">I", raw_len))
        result.extend(struct.pack(">I", len(payload)))
        result.extend(payload)

    return bytes(result)


def decompress_bytes(container: bytes) -> bytes:
    """
    Decompress RWV1 container to original data.

    Args:
        container: RWV1 container bytes

    Returns:
        Original raw data

    Raises:
        RWV1Error: If decompression fails or integrity check fails
    """
    if len(container) < 14:  # Minimum header size
        raise RWV1Error("Container too short")

    # Parse header
    if container[:4] != RWV1_MAGIC:
        raise RWV1Error(f"Invalid magic: {container[:4]!r}")

    version = container[4]
    if version != RWV1_VERSION:
        raise RWV1Error(f"Unsupported version: {version}")

    flags = container[5]
    has_sha256 = bool(flags & RWV1_FLAG_RAW_SHA256_PRESENT)

    block_size = struct.unpack(">I", container[6:10])[0]
    block_count = struct.unpack(">I", container[10:14])[0]

    pos = 14

    # Read optional SHA-256
    expected_sha256 = None
    if has_sha256:
        if pos + 32 > len(container):
            raise RWV1Error("Truncated SHA-256")
        expected_sha256 = container[pos:pos + 32]
        pos += 32

    # Read and decode blocks
    result = bytearray()

    for i in range(block_count):
        if pos + 9 > len(container):
            raise RWV1Error(f"Truncated block {i} header")

        branch_id = BranchID(container[pos])
        pos += 1

        raw_len = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        payload_len = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        if pos + payload_len > len(container):
            raise RWV1Error(f"Truncated block {i} payload")

        payload = container[pos:pos + payload_len]
        pos += payload_len

        # Decode block
        try:
            block_data = _decode_block(payload, branch_id, raw_len)
        except (MOZlibError, zlib.error) as e:
            raise RWV1Error(f"Block {i} decode failed: {e}")

        result.extend(block_data)

    # Verify SHA-256 if present
    if expected_sha256:
        actual_sha256 = hashlib.sha256(result).digest()
        if actual_sha256 != expected_sha256:
            raise RWV1Error("SHA-256 mismatch (data corruption)")

    return bytes(result)


def compress(input_path: str, output_path: str,
             config: Optional[RWV1Config] = None) -> ContainerInfo:
    """
    Compress a file to RWV1 container format.

    Args:
        input_path: Path to input file
        output_path: Path to output .rwv file
        config: Compression configuration

    Returns:
        ContainerInfo with compression statistics
    """
    with open(input_path, 'rb') as f:
        data = f.read()

    container = compress_bytes(data, config)

    with open(output_path, 'wb') as f:
        f.write(container)

    return get_container_info(container)


def decompress(input_path: str, output_path: str) -> int:
    """
    Decompress RWV1 container to original file.

    Args:
        input_path: Path to .rwv file
        output_path: Path to output file

    Returns:
        Size of decompressed data
    """
    with open(input_path, 'rb') as f:
        container = f.read()

    data = decompress_bytes(container)

    with open(output_path, 'wb') as f:
        f.write(data)

    return len(data)


def get_container_info(container: bytes) -> ContainerInfo:
    """
    Parse container and return information without full decompression.
    """
    if len(container) < 14:
        raise RWV1Error("Container too short")

    if container[:4] != RWV1_MAGIC:
        raise RWV1Error(f"Invalid magic: {container[:4]!r}")

    version = container[4]
    flags = container[5]
    has_sha256 = bool(flags & RWV1_FLAG_RAW_SHA256_PRESENT)

    block_size = struct.unpack(">I", container[6:10])[0]
    block_count = struct.unpack(">I", container[10:14])[0]

    pos = 14

    raw_sha256 = None
    if has_sha256:
        raw_sha256 = container[pos:pos + 32]
        pos += 32

    info = ContainerInfo(
        version=version,
        flags=flags,
        block_size=block_size,
        block_count=block_count,
        raw_sha256=raw_sha256,
    )

    # Read block headers (skip payloads)
    for i in range(block_count):
        if pos + 9 > len(container):
            break

        branch_id = BranchID(container[pos])
        pos += 1

        raw_len = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        payload_len = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        info.blocks.append(BlockInfo(
            index=i,
            branch_id=branch_id,
            raw_len=raw_len,
            payload_len=payload_len,
        ))

        info.total_raw_size += raw_len
        info.total_payload_size += payload_len

        pos += payload_len  # Skip payload

    return info
