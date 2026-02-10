"""Tests for RW-3: Index (non-semantic)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import sha256_bytes
from origin.utilities.realityweaver.index import (
    IndexEntry,
    WeaverIndex,
    build_index,
    index_to_json,
)


def _make_manifests():
    return [
        {
            "manifest_id": "RWMF-000000000000000a",
            "files": {
                "audio.rwv1": {"sha256": sha256_bytes(b"audio"), "size": 5, "content_type": "audio/rwv1"},
                "shared.txt": {"sha256": sha256_bytes(b"shared"), "size": 6},
            },
        },
        {
            "manifest_id": "RWMF-000000000000000b",
            "files": {
                "video.rwv1": {"sha256": sha256_bytes(b"video"), "size": 5},
                "shared.txt": {"sha256": sha256_bytes(b"shared"), "size": 6},
            },
        },
    ]


class TestIndex:
    def test_build_index(self):
        manifests = _make_manifests()
        index = build_index(manifests)
        assert index.file_count() == 4  # 2 + 2

    def test_lookup_by_path(self):
        manifests = _make_manifests()
        index = build_index(manifests)
        results = index.lookup_path("shared.txt")
        assert len(results) == 2

    def test_lookup_by_hash(self):
        manifests = _make_manifests()
        index = build_index(manifests)
        h = sha256_bytes(b"shared")
        results = index.lookup_hash(h)
        assert len(results) == 2

    def test_unique_hashes(self):
        manifests = _make_manifests()
        index = build_index(manifests)
        # audio, video, shared = 3 unique
        assert index.unique_hashes() == 3

    def test_index_to_json(self):
        manifests = _make_manifests()
        index = build_index(manifests)
        data = index_to_json(index)
        assert data["file_count"] == 4
        assert len(data["entries"]) == 4

    def test_empty_index(self):
        index = build_index([])
        assert index.file_count() == 0
        assert index.unique_hashes() == 0
