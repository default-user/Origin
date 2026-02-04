# RealityWeaverVideo Container Format (RWV-VIDEO-V1)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
RWV-VIDEO-V1 Container Format.

Purpose: Store encoded video segments with decision provenance for audit,
re-weaving, and decoupling encoding logic from codecs.

TODO: Exact binary layout not fully specified. Current implementation
uses JSONL index + binary payload blob as interim format.
"""

import json
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, BinaryIO


# Container magic and version
RWV_VIDEO_MAGIC = b'RWVV'
RWV_VIDEO_VERSION = 1


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

    Interim format (JSONL + blob):
    - Header (fixed size, binary)
    - Index (JSONL, one record per line)
    - Payload blob (concatenated segment data)

    TODO: Define stable binary format for production use.
    """

    def __init__(self):
        self.header: Optional[ContainerHeader] = None
        self.segments: List[SegmentRecord] = []
        self._payload_data: bytes = b''

    def add_segment(self, record: SegmentRecord, payload: bytes) -> None:
        """Add a segment to the container."""
        # Update offset to current position in payload
        record.payload_offset = len(self._payload_data)
        record.payload_size = len(payload)
        self.segments.append(record)
        self._payload_data += payload

    def write(self, path: str, source_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Write container to file.

        Format:
        - Magic (4 bytes): "RWVV"
        - Version (1 byte): 1
        - Reserved (3 bytes): 0
        - Index length (8 bytes): big-endian u64
        - Index data (JSONL)
        - Payload data
        """
        # Build index JSONL
        index_lines = [json.dumps(s.to_dict()) for s in self.segments]
        index_data = '\n'.join(index_lines).encode('utf-8')

        total_duration = 0.0
        if self.segments:
            total_duration = max(s.end_time for s in self.segments)

        with open(path, 'wb') as f:
            # Magic
            f.write(RWV_VIDEO_MAGIC)
            # Version
            f.write(bytes([RWV_VIDEO_VERSION]))
            # Reserved
            f.write(bytes([0, 0, 0]))
            # Segment count
            f.write(struct.pack(">I", len(self.segments)))
            # Index length
            f.write(struct.pack(">Q", len(index_data)))
            # Source info JSON (length-prefixed)
            source_json = json.dumps(source_info or {}).encode('utf-8')
            f.write(struct.pack(">I", len(source_json)))
            f.write(source_json)
            # Index data
            f.write(index_data)
            # Payload data
            f.write(self._payload_data)

    @classmethod
    def read(cls, path: str) -> 'VideoContainer':
        """
        Read container from file.
        """
        container = cls()

        with open(path, 'rb') as f:
            # Magic
            magic = f.read(4)
            if magic != RWV_VIDEO_MAGIC:
                raise ValueError(f"Invalid magic: {magic!r}")

            # Version
            version = f.read(1)[0]
            if version != RWV_VIDEO_VERSION:
                raise ValueError(f"Unsupported version: {version}")

            # Reserved
            f.read(3)

            # Segment count
            segment_count = struct.unpack(">I", f.read(4))[0]

            # Index length
            index_length = struct.unpack(">Q", f.read(8))[0]

            # Source info
            source_json_len = struct.unpack(">I", f.read(4))[0]
            source_json = f.read(source_json_len).decode('utf-8')
            source_info = json.loads(source_json) if source_json else {}

            # Index data
            index_data = f.read(index_length).decode('utf-8')
            for line in index_data.split('\n'):
                if line.strip():
                    record = SegmentRecord.from_dict(json.loads(line))
                    container.segments.append(record)

            # Payload data
            container._payload_data = f.read()

            # Build header
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

    def get_manifest(self) -> Dict[str, Any]:
        """Get container manifest as dictionary."""
        return {
            "magic": RWV_VIDEO_MAGIC.decode('ascii'),
            "version": RWV_VIDEO_VERSION,
            "segment_count": len(self.segments),
            "total_payload_size": len(self._payload_data),
            "segments": [s.to_dict() for s in self.segments],
        }
