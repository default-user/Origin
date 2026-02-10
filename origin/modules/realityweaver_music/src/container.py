# RXM1 Container Format
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RXM1 Container encoder/decoder for Reality Weaver Music.

BINARY FORMAT:
  MAGIC: "RXM1" (4 bytes)
  VERSION: 1 (u8)
  FLAGS: u8
    bit0 = has_sha256
    bit1 = has_audio
    bit2 = has_sync
  CHUNK_COUNT: u16 big-endian
  [SHA256: 32 bytes if flags & 0x01]

  CHUNK TABLE (repeated chunk_count times):
    CHUNK_TYPE: 4 bytes (FourCC)
    CHUNK_SIZE: u32 big-endian
    CHUNK_DATA: bytes[chunk_size]

Chunk types:
  META - JSON metadata (uncompressed)
  SCOR - Score data compressed with RWV1
  SYNC - Sync map: monotonic (score_tick, audio_frame) pairs
  AUDI - Audio data compressed with RWV1

Reuses RWV1 compression for SCOR and AUDI payloads.
Core invariant: unpack(pack(score, audio, sync, meta)) reproduces all inputs.
"""

import hashlib
import importlib.util
import json
import struct
import sys
import os
from typing import Optional, List, Tuple, Dict, Any

try:
    from .rxm_types import (
        RXM1_MAGIC, RXM1_VERSION,
        RXM1_FLAG_HAS_SHA256, RXM1_FLAG_HAS_AUDIO, RXM1_FLAG_HAS_SYNC,
        CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI, KNOWN_CHUNK_TYPES,
        RXMConfig, RXMContainerInfo, ChunkInfo, RXMMetadata, SyncEntry,
    )
except ImportError:
    from rxm_types import (
        RXM1_MAGIC, RXM1_VERSION,
        RXM1_FLAG_HAS_SHA256, RXM1_FLAG_HAS_AUDIO, RXM1_FLAG_HAS_SYNC,
        CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI, KNOWN_CHUNK_TYPES,
        RXMConfig, RXMContainerInfo, ChunkInfo, RXMMetadata, SyncEntry,
    )


def _load_rwv1():
    """
    Load RWV1 compression from the realityweaver sibling package.

    Creates a synthetic package so realityweaver's relative imports work.
    """
    import types as builtin_types

    rw_src = os.path.normpath(os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', '..', 'realityweaver', 'src'
    ))

    pkg_name = '_rwv1_pkg'

    # Only load once
    if pkg_name in sys.modules:
        rwv1_container = sys.modules[f'{pkg_name}.container']
        rwv1_types = sys.modules[f'{pkg_name}.types']
        return (rwv1_container.compress_bytes, rwv1_container.decompress_bytes,
                rwv1_types.RWV1Config)

    # Create a synthetic package so relative imports resolve
    pkg = builtin_types.ModuleType(pkg_name)
    pkg.__path__ = [rw_src]
    pkg.__package__ = pkg_name
    sys.modules[pkg_name] = pkg

    # Register submodule specs in the package
    for mod_name in ('types', 'mo_zlib', 'container'):
        fqn = f'{pkg_name}.{mod_name}'
        mod_path = os.path.join(rw_src, f'{mod_name}.py')
        spec = importlib.util.spec_from_file_location(fqn, mod_path)
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = pkg_name
        sys.modules[fqn] = mod
        setattr(pkg, mod_name, mod)

    # Execute in dependency order (types -> mo_zlib -> container)
    for mod_name in ('types', 'mo_zlib', 'container'):
        fqn = f'{pkg_name}.{mod_name}'
        sys.modules[fqn].__spec__.loader.exec_module(sys.modules[fqn])

    rwv1_container = sys.modules[f'{pkg_name}.container']
    rwv1_types = sys.modules[f'{pkg_name}.types']

    return (rwv1_container.compress_bytes, rwv1_container.decompress_bytes,
            rwv1_types.RWV1Config)


rwv1_compress, rwv1_decompress, RWV1Config = _load_rwv1()


class RXMError(Exception):
    """Error in RXM container operations."""
    pass


def _make_rwv1_config(config: RXMConfig) -> RWV1Config:
    """Create RWV1Config from RXM config."""
    return RWV1Config(
        block_size=config.rwv1_block_size,
        allow_bz2=config.rwv1_allow_bz2,
        allow_lzma=config.rwv1_allow_lzma,
        include_sha256=False,  # RXM handles its own integrity
    )


def _encode_sync(sync_entries: List[SyncEntry]) -> bytes:
    """Encode sync entries to binary format."""
    result = bytearray()
    result.extend(struct.pack(">I", len(sync_entries)))
    for entry in sync_entries:
        result.extend(struct.pack(">II", entry.score_tick, entry.audio_frame))
    return bytes(result)


def _decode_sync(data: bytes) -> List[SyncEntry]:
    """Decode sync entries from binary format."""
    if len(data) < 4:
        raise RXMError("SYNC chunk too short")

    count = struct.unpack(">I", data[:4])[0]
    expected_size = 4 + count * 8
    if len(data) < expected_size:
        raise RXMError(f"SYNC chunk truncated: expected {expected_size} bytes, got {len(data)}")

    entries = []
    pos = 4
    for _ in range(count):
        score_tick, audio_frame = struct.unpack(">II", data[pos:pos + 8])
        entries.append(SyncEntry(score_tick=score_tick, audio_frame=audio_frame))
        pos += 8

    return entries


def validate_sync(sync_entries: List[SyncEntry]) -> None:
    """
    Validate that sync entries are strictly monotonically increasing.

    Raises RXMError if validation fails.
    """
    if len(sync_entries) < 2:
        return

    for i in range(1, len(sync_entries)):
        prev = sync_entries[i - 1]
        curr = sync_entries[i]

        if curr.score_tick <= prev.score_tick:
            raise RXMError(
                f"SYNC validation failed: score_tick not monotonically increasing "
                f"at index {i}: {prev.score_tick} >= {curr.score_tick}"
            )
        if curr.audio_frame <= prev.audio_frame:
            raise RXMError(
                f"SYNC validation failed: audio_frame not monotonically increasing "
                f"at index {i}: {prev.audio_frame} >= {curr.audio_frame}"
            )


def tick_to_frame(sync_entries: List[SyncEntry], tick: int) -> int:
    """
    Convert a score tick to the nearest audio frame using linear interpolation.

    Args:
        sync_entries: List of sync anchor points (must be validated)
        tick: Score tick to convert

    Returns:
        Estimated audio frame
    """
    if not sync_entries:
        raise RXMError("No sync entries available")

    if tick <= sync_entries[0].score_tick:
        return sync_entries[0].audio_frame

    if tick >= sync_entries[-1].score_tick:
        return sync_entries[-1].audio_frame

    for i in range(1, len(sync_entries)):
        if sync_entries[i].score_tick >= tick:
            prev = sync_entries[i - 1]
            curr = sync_entries[i]
            tick_range = curr.score_tick - prev.score_tick
            frame_range = curr.audio_frame - prev.audio_frame
            tick_offset = tick - prev.score_tick
            return prev.audio_frame + int(frame_range * tick_offset / tick_range)

    return sync_entries[-1].audio_frame


def frame_to_tick(sync_entries: List[SyncEntry], frame: int) -> int:
    """
    Convert an audio frame to the nearest score tick using linear interpolation.

    Args:
        sync_entries: List of sync anchor points (must be validated)
        frame: Audio frame to convert

    Returns:
        Estimated score tick
    """
    if not sync_entries:
        raise RXMError("No sync entries available")

    if frame <= sync_entries[0].audio_frame:
        return sync_entries[0].score_tick

    if frame >= sync_entries[-1].audio_frame:
        return sync_entries[-1].score_tick

    for i in range(1, len(sync_entries)):
        if sync_entries[i].audio_frame >= frame:
            prev = sync_entries[i - 1]
            curr = sync_entries[i]
            frame_range = curr.audio_frame - prev.audio_frame
            tick_range = curr.score_tick - prev.score_tick
            frame_offset = frame - prev.audio_frame
            return prev.score_tick + int(tick_range * frame_offset / frame_range)

    return sync_entries[-1].score_tick


def pack_bytes(
    metadata: RXMMetadata,
    score_data: bytes,
    audio_data: Optional[bytes] = None,
    sync_entries: Optional[List[SyncEntry]] = None,
    config: Optional[RXMConfig] = None,
    extra_chunks: Optional[List[Tuple[bytes, bytes]]] = None,
) -> bytes:
    """
    Pack data into an RXM1 container.

    Args:
        metadata: Music metadata
        score_data: Raw score data (MIDI bytes)
        audio_data: Optional raw audio data
        sync_entries: Optional sync map (required if audio_data is provided)
        config: Packing configuration
        extra_chunks: Optional list of (fourcc, data) for unknown/extra chunks

    Returns:
        RXM1 container bytes

    Raises:
        RXMError: If packing fails or inputs are invalid
    """
    if config is None:
        config = RXMConfig()
    config.validate()

    if not score_data and not audio_data:
        raise RXMError("At least score_data must be provided")

    if audio_data is not None and sync_entries is None:
        raise RXMError("sync_entries required when audio_data is provided")

    if audio_data is not None and sync_entries is not None:
        validate_sync(sync_entries)

    # Determine flags
    has_audio = audio_data is not None
    has_sync = sync_entries is not None and len(sync_entries) > 0

    flags = 0
    if config.include_sha256:
        flags |= RXM1_FLAG_HAS_SHA256
    if has_audio:
        flags |= RXM1_FLAG_HAS_AUDIO
    if has_sync:
        flags |= RXM1_FLAG_HAS_SYNC

    # Build chunks
    chunks: List[Tuple[bytes, bytes]] = []

    # META chunk (uncompressed JSON)
    meta_json = json.dumps(metadata.to_dict(), separators=(',', ':')).encode('utf-8')
    chunks.append((CHUNK_META, meta_json))

    # SCOR chunk (RWV1 compressed)
    rwv1_config = _make_rwv1_config(config)
    compressed_score = rwv1_compress(score_data, rwv1_config)
    chunks.append((CHUNK_SCOR, compressed_score))

    # SYNC chunk (if present)
    if has_sync:
        sync_data = _encode_sync(sync_entries)
        chunks.append((CHUNK_SYNC, sync_data))

    # AUDI chunk (RWV1 compressed, if present)
    if has_audio:
        compressed_audio = rwv1_compress(audio_data, rwv1_config)
        chunks.append((CHUNK_AUDI, compressed_audio))

    # Extra/unknown chunks (for forward compatibility)
    if extra_chunks:
        for fourcc, data in extra_chunks:
            if len(fourcc) != 4:
                raise RXMError(f"Invalid chunk FourCC length: {len(fourcc)}")
            chunks.append((fourcc, data))

    # Build container
    result = bytearray()

    # Header
    result.extend(RXM1_MAGIC)
    result.append(RXM1_VERSION)
    result.append(flags)
    result.extend(struct.pack(">H", len(chunks)))

    # SHA-256 placeholder (filled after all chunks are written)
    sha256_offset = len(result) if config.include_sha256 else None
    if config.include_sha256:
        result.extend(b'\x00' * 32)

    # Chunk table
    chunk_data_for_hash = bytearray()
    for fourcc, data in chunks:
        result.extend(fourcc)
        result.extend(struct.pack(">I", len(data)))
        result.extend(data)
        chunk_data_for_hash.extend(data)

    # Fill in SHA-256 if requested
    if config.include_sha256 and sha256_offset is not None:
        sha256_digest = hashlib.sha256(chunk_data_for_hash).digest()
        result[sha256_offset:sha256_offset + 32] = sha256_digest

    return bytes(result)


def unpack_bytes(container: bytes) -> Dict[str, Any]:
    """
    Unpack an RXM1 container.

    Args:
        container: RXM1 container bytes

    Returns:
        Dict with keys:
            - metadata: RXMMetadata
            - score_data: bytes (decompressed)
            - audio_data: Optional[bytes] (decompressed, if present)
            - sync_entries: Optional[List[SyncEntry]] (if present)
            - extra_chunks: List[Tuple[bytes, bytes]] (unknown chunks preserved)

    Raises:
        RXMError: If unpacking fails
    """
    if len(container) < 8:
        raise RXMError("Container too short")

    # Parse header
    if container[:4] != RXM1_MAGIC:
        raise RXMError(f"Invalid magic: {container[:4]!r}")

    version = container[4]
    if version != RXM1_VERSION:
        raise RXMError(f"Unsupported version: {version}")

    flags = container[5]
    has_sha256 = bool(flags & RXM1_FLAG_HAS_SHA256)
    has_audio = bool(flags & RXM1_FLAG_HAS_AUDIO)
    has_sync = bool(flags & RXM1_FLAG_HAS_SYNC)

    chunk_count = struct.unpack(">H", container[6:8])[0]

    pos = 8

    # Read optional SHA-256
    expected_sha256 = None
    if has_sha256:
        if pos + 32 > len(container):
            raise RXMError("Truncated SHA-256")
        expected_sha256 = container[pos:pos + 32]
        pos += 32

    # Read chunks
    raw_chunks: List[Tuple[bytes, bytes]] = []
    chunk_data_for_hash = bytearray()

    for i in range(chunk_count):
        if pos + 8 > len(container):
            raise RXMError(f"Truncated chunk {i} header")

        fourcc = container[pos:pos + 4]
        pos += 4

        data_size = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        if pos + data_size > len(container):
            raise RXMError(f"Truncated chunk {i} data")

        data = container[pos:pos + data_size]
        pos += data_size

        raw_chunks.append((fourcc, data))
        chunk_data_for_hash.extend(data)

    # Verify SHA-256 if present
    if expected_sha256 is not None:
        actual_sha256 = hashlib.sha256(chunk_data_for_hash).digest()
        if actual_sha256 != expected_sha256:
            raise RXMError("SHA-256 mismatch (data corruption)")

    # Process chunks
    metadata = None
    score_data = None
    audio_data = None
    sync_entries = None
    extra_chunks = []

    for fourcc, data in raw_chunks:
        if fourcc == CHUNK_META:
            try:
                meta_dict = json.loads(data.decode('utf-8'))
                metadata = RXMMetadata.from_dict(meta_dict)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                raise RXMError(f"Invalid META chunk: {e}")

        elif fourcc == CHUNK_SCOR:
            try:
                score_data = rwv1_decompress(data)
            except Exception as e:
                raise RXMError(f"SCOR decompression failed: {e}")

        elif fourcc == CHUNK_SYNC:
            sync_entries = _decode_sync(data)
            validate_sync(sync_entries)

        elif fourcc == CHUNK_AUDI:
            try:
                audio_data = rwv1_decompress(data)
            except Exception as e:
                raise RXMError(f"AUDI decompression failed: {e}")

        else:
            # Unknown chunk: preserve for forward compatibility
            extra_chunks.append((fourcc, data))

    # Validate required chunks
    if metadata is None:
        raise RXMError("Missing required META chunk")
    if score_data is None:
        raise RXMError("Missing required SCOR chunk")
    if has_audio and audio_data is None:
        raise RXMError("Audio flag set but AUDI chunk missing")
    if has_sync and sync_entries is None:
        raise RXMError("Sync flag set but SYNC chunk missing")
    if audio_data is not None and sync_entries is None:
        raise RXMError("AUDI chunk present but SYNC chunk missing")

    return {
        'metadata': metadata,
        'score_data': score_data,
        'audio_data': audio_data,
        'sync_entries': sync_entries,
        'extra_chunks': extra_chunks,
    }


def pack(
    output_path: str,
    metadata: RXMMetadata,
    score_data: bytes,
    audio_data: Optional[bytes] = None,
    sync_entries: Optional[List[SyncEntry]] = None,
    config: Optional[RXMConfig] = None,
    extra_chunks: Optional[List[Tuple[bytes, bytes]]] = None,
) -> RXMContainerInfo:
    """
    Pack data into an RXM1 container file.

    Returns:
        RXMContainerInfo with container statistics
    """
    container = pack_bytes(metadata, score_data, audio_data,
                           sync_entries, config, extra_chunks)

    with open(output_path, 'wb') as f:
        f.write(container)

    return get_container_info(container)


def unpack(input_path: str) -> Dict[str, Any]:
    """
    Unpack an RXM1 container file.

    Returns:
        Dict with metadata, score_data, audio_data, sync_entries, extra_chunks
    """
    with open(input_path, 'rb') as f:
        container = f.read()

    return unpack_bytes(container)


def validate_container(container: bytes) -> Tuple[bool, List[str]]:
    """
    Validate an RXM1 container without fully unpacking.

    Returns:
        (is_valid, list_of_errors)
    """
    errors = []

    if len(container) < 8:
        return False, ["Container too short (< 8 bytes)"]

    # Check magic
    if container[:4] != RXM1_MAGIC:
        errors.append(f"Invalid magic: {container[:4]!r}")
        return False, errors

    version = container[4]
    if version != RXM1_VERSION:
        errors.append(f"Unsupported version: {version}")
        return False, errors

    flags = container[5]
    has_sha256 = bool(flags & RXM1_FLAG_HAS_SHA256)
    has_audio = bool(flags & RXM1_FLAG_HAS_AUDIO)
    has_sync = bool(flags & RXM1_FLAG_HAS_SYNC)

    chunk_count = struct.unpack(">H", container[6:8])[0]

    pos = 8

    if has_sha256:
        if pos + 32 > len(container):
            errors.append("Truncated SHA-256 field")
            return False, errors
        expected_sha256 = container[pos:pos + 32]
        pos += 32
    else:
        expected_sha256 = None

    # Parse chunks
    found_types = set()
    chunk_data_for_hash = bytearray()

    for i in range(chunk_count):
        if pos + 8 > len(container):
            errors.append(f"Truncated chunk {i} header")
            break

        fourcc = container[pos:pos + 4]
        pos += 4

        data_size = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        if pos + data_size > len(container):
            errors.append(f"Truncated chunk {i} data (type={fourcc!r})")
            break

        chunk_data = container[pos:pos + data_size]
        chunk_data_for_hash.extend(chunk_data)
        pos += data_size

        found_types.add(fourcc)

        # Validate SYNC monotonicity
        if fourcc == CHUNK_SYNC:
            try:
                entries = _decode_sync(chunk_data)
                validate_sync(entries)
            except RXMError as e:
                errors.append(str(e))

    # Check required chunks
    if CHUNK_META not in found_types:
        errors.append("Missing required META chunk")
    if CHUNK_SCOR not in found_types:
        errors.append("Missing required SCOR chunk")
    if has_audio and CHUNK_AUDI not in found_types:
        errors.append("Audio flag set but AUDI chunk missing")
    if has_sync and CHUNK_SYNC not in found_types:
        errors.append("Sync flag set but SYNC chunk missing")
    if CHUNK_AUDI in found_types and CHUNK_SYNC not in found_types:
        errors.append("AUDI chunk present but SYNC chunk missing")

    # Verify SHA-256
    if expected_sha256 is not None and not errors:
        actual_sha256 = hashlib.sha256(chunk_data_for_hash).digest()
        if actual_sha256 != expected_sha256:
            errors.append("SHA-256 mismatch (data corruption)")

    return len(errors) == 0, errors


def get_container_info(container: bytes) -> RXMContainerInfo:
    """
    Parse container and return information without full decompression.
    """
    if len(container) < 8:
        raise RXMError("Container too short")

    if container[:4] != RXM1_MAGIC:
        raise RXMError(f"Invalid magic: {container[:4]!r}")

    version = container[4]
    flags = container[5]
    has_sha256 = bool(flags & RXM1_FLAG_HAS_SHA256)
    has_audio = bool(flags & RXM1_FLAG_HAS_AUDIO)
    has_sync = bool(flags & RXM1_FLAG_HAS_SYNC)

    chunk_count = struct.unpack(">H", container[6:8])[0]

    pos = 8

    sha256_hex = None
    if has_sha256:
        if pos + 32 <= len(container):
            sha256_hex = container[pos:pos + 32].hex()
        pos += 32

    info = RXMContainerInfo(
        version=version,
        flags=flags,
        chunk_count=chunk_count,
        has_sha256=has_sha256,
        has_audio=has_audio,
        has_sync=has_sync,
        sha256_hex=sha256_hex,
        mode="score_plus_audio" if has_audio else "score_only",
        total_size=len(container),
    )

    for i in range(chunk_count):
        if pos + 8 > len(container):
            break

        fourcc = container[pos:pos + 4]
        pos += 4

        data_size = struct.unpack(">I", container[pos:pos + 4])[0]
        pos += 4

        info.chunks.append(ChunkInfo(chunk_type=fourcc, data_size=data_size))

        # Extract metadata if it's the META chunk
        if fourcc == CHUNK_META and pos + data_size <= len(container):
            try:
                meta_dict = json.loads(container[pos:pos + data_size].decode('utf-8'))
                info.metadata = meta_dict
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass

        # Count sync entries if it's the SYNC chunk
        if fourcc == CHUNK_SYNC and pos + 4 <= len(container):
            try:
                info.sync_entry_count = struct.unpack(">I", container[pos:pos + 4])[0]
            except struct.error:
                pass

        pos += data_size

    return info
