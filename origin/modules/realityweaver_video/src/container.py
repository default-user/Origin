# RealityWeaverVideo Container Format (RWV-VIDEO-V1)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RWV-VIDEO-V1 Container Format.

Purpose: Store encoded video segments with decision provenance for audit,
re-weaving, and decoupling encoding logic from codecs.

Binary Format Specification (Version 1):
=========================================

Header (fixed 64 bytes):
  Offset  Size  Field
  ------  ----  -----
  0       4     Magic: "RWVV" (0x52 0x57 0x56 0x56)
  4       1     Version: 1
  5       1     Flags: bit 0 = has_checksum, bit 1 = compressed_index
  6       2     Reserved (zero)
  8       4     Segment count (big-endian u32)
  12      8     Total duration (big-endian f64, seconds)
  20      8     Index offset (big-endian u64, from start of file)
  28      8     Index size (big-endian u64)
  36      8     Payload offset (big-endian u64, from start of file)
  40      8     Payload size (big-endian u64)
  48      4     Source info size (big-endian u32)
  52      4     Checksum type: 0=none, 1=CRC32, 2=SHA256
  56      8     Header checksum (CRC32 of bytes 0-55, zero-padded)

Source Info (variable length, JSON):
  Length-prefixed JSON blob containing source metadata

Segment Index (variable length):
  For each segment (fixed 80 bytes per entry):
    Offset  Size  Field
    ------  ----  -----
    0       4     Segment ID (big-endian u32)
    4       8     Start time (big-endian f64, seconds)
    12      8     End time (big-endian f64, seconds)
    20      16    Encoder ID (UTF-8, null-padded)
    36      4     CRF value (big-endian u32)
    40      8     VMAF score (big-endian f64, -1 if unavailable)
    48      8     PSNR score (big-endian f64, -1 if unavailable)
    56      8     SSIM score (big-endian f64, -1 if unavailable)
    64      8     Payload offset (big-endian u64, relative to payload section)
    72      8     Payload size (big-endian u64)

Payload Section:
  Concatenated segment video data
"""

import hashlib
import json
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO, Tuple


# Container magic and version
RWV_VIDEO_MAGIC = b'RWVV'
RWV_VIDEO_VERSION = 1

# Header constants
HEADER_SIZE = 64
SEGMENT_INDEX_ENTRY_SIZE = 80
ENCODER_ID_SIZE = 16

# Flags
FLAG_HAS_CHECKSUM = 0x01
FLAG_COMPRESSED_INDEX = 0x02

# Checksum types
CHECKSUM_NONE = 0
CHECKSUM_CRC32 = 1
CHECKSUM_SHA256 = 2


@dataclass
class SegmentRecord:
    """
    Record for a single video segment in the container.

    Stores:
    - segment_id: Unique identifier
    - time_range: (start, end) in seconds
    - chosen_encoder_id: Which encoder produced this segment
    - encoder_parameters: Configuration used
    - perceptual_metrics: Quality metrics (VMAF, PSNR, SSIM)
    - payload_offset: Offset into payload blob
    - payload_size: Size of segment data
    """
    segment_id: int
    start_time: float
    end_time: float
    chosen_encoder_id: str
    encoder_parameters: Dict[str, Any]
    perceptual_metrics: Dict[str, float]
    payload_offset: int
    payload_size: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "time_range": [self.start_time, self.end_time],
            "encoder_id": self.chosen_encoder_id,
            "encoder_params": self.encoder_parameters,
            "metrics": self.perceptual_metrics,
            "payload_offset": self.payload_offset,
            "payload_size": self.payload_size,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'SegmentRecord':
        time_range = d.get("time_range", [0, 0])
        return cls(
            segment_id=d["segment_id"],
            start_time=time_range[0],
            end_time=time_range[1],
            chosen_encoder_id=d["encoder_id"],
            encoder_parameters=d.get("encoder_params", {}),
            perceptual_metrics=d.get("metrics", {}),
            payload_offset=d["payload_offset"],
            payload_size=d["payload_size"],
        )


@dataclass
class ContainerHeader:
    """Header for RWV-VIDEO-V1 container."""
    version: int
    segment_count: int
    total_duration: float
    source_info: Dict[str, Any]
    index_offset: int  # Offset to JSONL index
    payload_offset: int  # Offset to payload blob

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "segment_count": self.segment_count,
            "total_duration": self.total_duration,
            "source_info": self.source_info,
            "index_offset": self.index_offset,
            "payload_offset": self.payload_offset,
        }


class VideoContainer:
    """
    RWV-VIDEO-V1 container reader/writer.

    Implements the stable binary format for production use:
    - Fixed 64-byte header with checksums
    - Fixed-size segment index entries (80 bytes each)
    - Concatenated payload blob

    Supports:
    - CRC32 checksums for integrity verification
    - Efficient random access to segments
    - Backward-compatible version handling
    """

    def __init__(self):
        self.header: Optional[ContainerHeader] = None
        self.segments: List[SegmentRecord] = []
        self._payload_data: bytes = b''
        self._source_info: Dict[str, Any] = {}
        self._use_checksum: bool = True
        self._checksum_type: int = CHECKSUM_CRC32

    def add_segment(self, record: SegmentRecord, payload: bytes) -> None:
        """Add a segment to the container."""
        # Update offset to current position in payload
        record.payload_offset = len(self._payload_data)
        record.payload_size = len(payload)
        self.segments.append(record)
        self._payload_data += payload

    def _encode_segment_index_entry(self, segment: SegmentRecord) -> bytes:
        """Encode a segment record to fixed-size binary format (80 bytes)."""
        # Encode encoder ID as fixed 16-byte string
        encoder_id_bytes = segment.chosen_encoder_id.encode('utf-8')[:ENCODER_ID_SIZE]
        encoder_id_bytes = encoder_id_bytes.ljust(ENCODER_ID_SIZE, b'\x00')

        # Extract CRF from encoder parameters (default 23)
        crf = segment.encoder_parameters.get('crf', 23)

        # Get metrics, use -1 for unavailable
        vmaf = segment.perceptual_metrics.get('vmaf', -1.0)
        psnr = segment.perceptual_metrics.get('psnr', -1.0)
        ssim = segment.perceptual_metrics.get('ssim', -1.0)

        if vmaf is None:
            vmaf = -1.0
        if psnr is None:
            psnr = -1.0
        if ssim is None:
            ssim = -1.0

        return struct.pack(
            ">I d d 16s I d d d Q Q",
            segment.segment_id,          # 4 bytes
            segment.start_time,          # 8 bytes
            segment.end_time,            # 8 bytes
            encoder_id_bytes,            # 16 bytes
            crf,                         # 4 bytes
            vmaf,                        # 8 bytes
            psnr,                        # 8 bytes
            ssim,                        # 8 bytes
            segment.payload_offset,      # 8 bytes
            segment.payload_size,        # 8 bytes
        )

    def _decode_segment_index_entry(self, data: bytes) -> SegmentRecord:
        """Decode a segment record from fixed-size binary format."""
        (
            segment_id, start_time, end_time, encoder_id_bytes,
            crf, vmaf, psnr, ssim, payload_offset, payload_size
        ) = struct.unpack(">I d d 16s I d d d Q Q", data)

        encoder_id = encoder_id_bytes.rstrip(b'\x00').decode('utf-8')

        # Convert -1 back to None for unavailable metrics
        metrics = {}
        if vmaf >= 0:
            metrics['vmaf'] = vmaf
        if psnr >= 0:
            metrics['psnr'] = psnr
        if ssim >= 0:
            metrics['ssim'] = ssim

        return SegmentRecord(
            segment_id=segment_id,
            start_time=start_time,
            end_time=end_time,
            chosen_encoder_id=encoder_id,
            encoder_parameters={'crf': crf},
            perceptual_metrics=metrics,
            payload_offset=payload_offset,
            payload_size=payload_size,
        )

    def _compute_checksum(self, data: bytes, checksum_type: int) -> bytes:
        """Compute checksum for data."""
        if checksum_type == CHECKSUM_CRC32:
            crc = zlib.crc32(data) & 0xFFFFFFFF
            return struct.pack(">Q", crc)
        elif checksum_type == CHECKSUM_SHA256:
            return hashlib.sha256(data).digest()[:8]
        return b'\x00' * 8

    def write(self, path: str, source_info: Optional[Dict[str, Any]] = None,
              use_checksum: bool = True) -> None:
        """
        Write container to file using stable binary format.

        Args:
            path: Output file path
            source_info: Optional metadata dictionary
            use_checksum: Whether to include CRC32 checksums
        """
        source_info = source_info or {}
        source_json = json.dumps(source_info, separators=(',', ':')).encode('utf-8')

        total_duration = 0.0
        if self.segments:
            total_duration = max(s.end_time for s in self.segments)

        # Calculate offsets
        # Header: 64 bytes
        # Source info: 4 bytes length + data
        # Index: segment_count * 80 bytes
        # Payload: variable

        source_info_start = HEADER_SIZE
        source_info_size = len(source_json)
        index_offset = source_info_start + 4 + source_info_size
        index_size = len(self.segments) * SEGMENT_INDEX_ENTRY_SIZE
        payload_offset = index_offset + index_size
        payload_size = len(self._payload_data)

        flags = 0
        checksum_type = CHECKSUM_NONE
        if use_checksum:
            flags |= FLAG_HAS_CHECKSUM
            checksum_type = CHECKSUM_CRC32

        with open(path, 'wb') as f:
            # Build header (without checksum field first)
            header_data = struct.pack(
                ">4s B B 2s I d Q Q Q Q I I",
                RWV_VIDEO_MAGIC,           # 4 bytes: Magic
                RWV_VIDEO_VERSION,         # 1 byte: Version
                flags,                     # 1 byte: Flags
                b'\x00\x00',               # 2 bytes: Reserved
                len(self.segments),        # 4 bytes: Segment count
                total_duration,            # 8 bytes: Total duration
                index_offset,              # 8 bytes: Index offset
                index_size,                # 8 bytes: Index size
                payload_offset,            # 8 bytes: Payload offset
                payload_size,              # 8 bytes: Payload size
                source_info_size,          # 4 bytes: Source info size
                checksum_type,             # 4 bytes: Checksum type
            )

            # Compute header checksum
            header_checksum = self._compute_checksum(header_data, checksum_type)

            # Write header + checksum
            f.write(header_data)
            f.write(header_checksum)

            # Write source info (length-prefixed)
            f.write(struct.pack(">I", source_info_size))
            f.write(source_json)

            # Write segment index
            for segment in self.segments:
                f.write(self._encode_segment_index_entry(segment))

            # Write payload
            f.write(self._payload_data)

    def write_legacy(self, path: str, source_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Write container using legacy JSONL format for backward compatibility.

        This method is provided for compatibility with older readers.
        """
        index_lines = [json.dumps(s.to_dict()) for s in self.segments]
        index_data = '\n'.join(index_lines).encode('utf-8')

        with open(path, 'wb') as f:
            f.write(RWV_VIDEO_MAGIC)
            f.write(bytes([RWV_VIDEO_VERSION]))
            f.write(bytes([0, 0, 0]))
            f.write(struct.pack(">I", len(self.segments)))
            f.write(struct.pack(">Q", len(index_data)))
            source_json = json.dumps(source_info or {}).encode('utf-8')
            f.write(struct.pack(">I", len(source_json)))
            f.write(source_json)
            f.write(index_data)
            f.write(self._payload_data)

    @classmethod
    def read(cls, path: str) -> 'VideoContainer':
        """
        Read container from file (auto-detects format version).
        """
        container = cls()

        with open(path, 'rb') as f:
            # Read magic
            magic = f.read(4)
            if magic != RWV_VIDEO_MAGIC:
                raise ValueError(f"Invalid magic: {magic!r}")

            # Read version and flags
            version = f.read(1)[0]
            if version != RWV_VIDEO_VERSION:
                raise ValueError(f"Unsupported version: {version}")

            flags = f.read(1)[0]

            # Check if this is the new binary format or legacy JSONL format
            # New format has specific flags, legacy format has flags = 0 followed by 0x00
            f.seek(0)  # Reset to start
            header_bytes = f.read(HEADER_SIZE)

            # Try to detect format by checking structure
            if len(header_bytes) >= HEADER_SIZE:
                try:
                    return cls._read_binary_format(path)
                except (struct.error, ValueError):
                    # Fall back to legacy format
                    pass

            # Try legacy format
            return cls._read_legacy_format(path)

    @classmethod
    def _read_binary_format(cls, path: str) -> 'VideoContainer':
        """Read container using stable binary format."""
        container = cls()

        with open(path, 'rb') as f:
            # Read and parse header
            header_bytes = f.read(HEADER_SIZE)
            if len(header_bytes) < HEADER_SIZE:
                raise ValueError("File too small for header")

            (
                magic, version, flags, reserved, segment_count,
                total_duration, index_offset, index_size,
                payload_offset, payload_size, source_info_size,
                checksum_type
            ) = struct.unpack(">4s B B 2s I d Q Q Q Q I I", header_bytes[:56])

            header_checksum = header_bytes[56:64]

            if magic != RWV_VIDEO_MAGIC:
                raise ValueError(f"Invalid magic: {magic!r}")

            if version != RWV_VIDEO_VERSION:
                raise ValueError(f"Unsupported version: {version}")

            # Verify checksum if present
            if flags & FLAG_HAS_CHECKSUM:
                expected_checksum = container._compute_checksum(header_bytes[:56], checksum_type)
                if header_checksum != expected_checksum:
                    raise ValueError("Header checksum mismatch")

            # Read source info
            f.seek(HEADER_SIZE)
            source_info_len = struct.unpack(">I", f.read(4))[0]
            source_json = f.read(source_info_len).decode('utf-8')
            source_info = json.loads(source_json) if source_json else {}
            container._source_info = source_info

            # Read segment index
            f.seek(index_offset)
            for _ in range(segment_count):
                entry_data = f.read(SEGMENT_INDEX_ENTRY_SIZE)
                if len(entry_data) < SEGMENT_INDEX_ENTRY_SIZE:
                    raise ValueError("Truncated segment index")
                record = container._decode_segment_index_entry(entry_data)
                container.segments.append(record)

            # Read payload
            f.seek(payload_offset)
            container._payload_data = f.read(payload_size)

            # Build header object
            container.header = ContainerHeader(
                version=version,
                segment_count=segment_count,
                total_duration=total_duration,
                source_info=source_info,
                index_offset=index_offset,
                payload_offset=payload_offset,
            )

        return container

    @classmethod
    def _read_legacy_format(cls, path: str) -> 'VideoContainer':
        """Read container using legacy JSONL format."""
        container = cls()

        with open(path, 'rb') as f:
            magic = f.read(4)
            if magic != RWV_VIDEO_MAGIC:
                raise ValueError(f"Invalid magic: {magic!r}")

            version = f.read(1)[0]
            if version != RWV_VIDEO_VERSION:
                raise ValueError(f"Unsupported version: {version}")

            f.read(3)  # Reserved

            segment_count = struct.unpack(">I", f.read(4))[0]
            index_length = struct.unpack(">Q", f.read(8))[0]

            source_json_len = struct.unpack(">I", f.read(4))[0]
            source_json = f.read(source_json_len).decode('utf-8')
            source_info = json.loads(source_json) if source_json else {}
            container._source_info = source_info

            index_data = f.read(index_length).decode('utf-8')
            for line in index_data.split('\n'):
                if line.strip():
                    record = SegmentRecord.from_dict(json.loads(line))
                    container.segments.append(record)

            container._payload_data = f.read()

            total_duration = 0.0
            if container.segments:
                total_duration = max(s.end_time for s in container.segments)

            container.header = ContainerHeader(
                version=version,
                segment_count=len(container.segments),
                total_duration=total_duration,
                source_info=source_info,
                index_offset=0,
                payload_offset=0,
            )

        return container

    def get_segment_payload(self, segment_id: int) -> Optional[bytes]:
        """Get payload data for a specific segment."""
        for segment in self.segments:
            if segment.segment_id == segment_id:
                start = segment.payload_offset
                end = start + segment.payload_size
                return self._payload_data[start:end]
        return None

    def get_segment_by_time(self, timestamp: float) -> Optional[SegmentRecord]:
        """Get segment containing the given timestamp."""
        for segment in self.segments:
            if segment.start_time <= timestamp < segment.end_time:
                return segment
        return None

    def extract_segment_to_file(self, segment_id: int, output_path: str) -> bool:
        """Extract a segment's payload to a file."""
        payload = self.get_segment_payload(segment_id)
        if payload is None:
            return False
        with open(output_path, 'wb') as f:
            f.write(payload)
        return True

    def verify_integrity(self) -> Tuple[bool, List[str]]:
        """Verify container integrity and return (success, error_messages)."""
        errors = []

        # Check segment count matches
        if self.header and self.header.segment_count != len(self.segments):
            errors.append(f"Segment count mismatch: header says {self.header.segment_count}, "
                         f"found {len(self.segments)}")

        # Verify all segment payloads are accessible
        total_payload_size = 0
        for segment in self.segments:
            if segment.payload_offset + segment.payload_size > len(self._payload_data):
                errors.append(f"Segment {segment.segment_id} payload extends beyond data")
            total_payload_size += segment.payload_size

        # Check for overlapping segments
        sorted_segments = sorted(self.segments, key=lambda s: s.payload_offset)
        for i in range(1, len(sorted_segments)):
            prev = sorted_segments[i - 1]
            curr = sorted_segments[i]
            if prev.payload_offset + prev.payload_size > curr.payload_offset:
                errors.append(f"Segments {prev.segment_id} and {curr.segment_id} "
                             f"have overlapping payloads")

        return len(errors) == 0, errors

    def get_manifest(self) -> Dict[str, Any]:
        """Get container manifest as dictionary."""
        return {
            "magic": RWV_VIDEO_MAGIC.decode('ascii'),
            "version": RWV_VIDEO_VERSION,
            "segment_count": len(self.segments),
            "total_payload_size": len(self._payload_data),
            "total_duration": self.header.total_duration if self.header else 0,
            "source_info": self._source_info,
            "segments": [s.to_dict() for s in self.segments],
        }
