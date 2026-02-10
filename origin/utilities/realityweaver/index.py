"""
RW-3: Index (non-semantic first).

Content-addressable index for WeaverPack files.
Non-semantic: indexes by path, hash, and size only.
Semantic indexing requires governance permit (not enabled here).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from .primitives import sha256_bytes


@dataclass
class IndexEntry:
    """A single entry in the WeaverPack index."""

    path: str
    sha256: str
    size: int
    manifest_id: str
    content_type: str | None = None


@dataclass
class WeaverIndex:
    """Non-semantic index for WeaverPack contents."""

    entries: list[IndexEntry] = field(default_factory=list)
    by_path: dict[str, list[IndexEntry]] = field(default_factory=dict)
    by_hash: dict[str, list[IndexEntry]] = field(default_factory=dict)

    def add(self, entry: IndexEntry) -> None:
        """Add an entry to the index."""
        self.entries.append(entry)
        self.by_path.setdefault(entry.path, []).append(entry)
        self.by_hash.setdefault(entry.sha256, []).append(entry)

    def lookup_path(self, path: str) -> list[IndexEntry]:
        """Look up entries by path."""
        return self.by_path.get(path, [])

    def lookup_hash(self, sha256: str) -> list[IndexEntry]:
        """Look up entries by SHA-256 hash."""
        return self.by_hash.get(sha256, [])

    def file_count(self) -> int:
        """Total number of indexed files."""
        return len(self.entries)

    def unique_hashes(self) -> int:
        """Number of unique content hashes."""
        return len(self.by_hash)


def build_index(manifests: list[dict]) -> WeaverIndex:
    """
    Build a non-semantic index from a list of manifests.

    Indexes by path, hash, and size. No semantic analysis.
    """
    index = WeaverIndex()
    for mf in manifests:
        mf_id = mf.get("manifest_id", "unknown")
        for path, entry in mf.get("files", {}).items():
            index.add(IndexEntry(
                path=path,
                sha256=entry["sha256"],
                size=entry.get("size", 0),
                manifest_id=mf_id,
                content_type=entry.get("content_type"),
            ))
    return index


def index_to_json(index: WeaverIndex) -> dict:
    """Serialize index to JSON-compatible dict."""
    return {
        "file_count": index.file_count(),
        "unique_hashes": index.unique_hashes(),
        "entries": [
            {
                "path": e.path,
                "sha256": e.sha256,
                "size": e.size,
                "manifest_id": e.manifest_id,
                "content_type": e.content_type,
            }
            for e in index.entries
        ],
    }
