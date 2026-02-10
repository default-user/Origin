"""Tests for RW-0: Primitives and hashing (determinism_suite)."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from origin.utilities.realityweaver.primitives import (
    canonical_json,
    canonical_json_pretty,
    compute_pack_hash,
    generate_id,
    sha256_bytes,
    sha256_file,
    verify_pack_hash,
)


class TestSHA256:
    """DT-T3: Hash computation is deterministic."""

    def test_empty_bytes(self):
        h = sha256_bytes(b"")
        assert h == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    def test_known_value(self):
        h = sha256_bytes(b"hello")
        assert h == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    def test_deterministic(self):
        data = b"test data for determinism"
        assert sha256_bytes(data) == sha256_bytes(data)

    def test_file_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"file content")
            path = f.name
        try:
            h = sha256_file(path)
            assert h == sha256_bytes(b"file content")
        finally:
            os.unlink(path)


class TestCanonicalJSON:
    """Determinism for JSON serialisation."""

    def test_sorted_keys(self):
        obj = {"b": 1, "a": 2}
        result = canonical_json(obj)
        assert result == b'{"a":2,"b":1}\n'

    def test_deterministic(self):
        obj = {"x": [1, 2, 3], "a": {"nested": True}}
        assert canonical_json(obj) == canonical_json(obj)

    def test_pretty_sorted(self):
        obj = {"z": 1, "a": 2}
        result = canonical_json_pretty(obj)
        parsed = json.loads(result)
        assert parsed == obj


class TestPackHash:
    """DT-T3: Same file set produces same pack_hash."""

    def test_deterministic(self):
        files = {
            "a.txt": {"sha256": "aaa", "size": 3},
            "b.txt": {"sha256": "bbb", "size": 3},
        }
        h1 = compute_pack_hash(files)
        h2 = compute_pack_hash(files)
        assert h1 == h2

    def test_order_independent(self):
        """Sorted by path, so insertion order doesn't matter."""
        files1 = {"b.txt": {"sha256": "bbb"}, "a.txt": {"sha256": "aaa"}}
        files2 = {"a.txt": {"sha256": "aaa"}, "b.txt": {"sha256": "bbb"}}
        assert compute_pack_hash(files1) == compute_pack_hash(files2)

    def test_verify_pack_hash(self):
        files = {"x.rs": {"sha256": "abc123", "size": 10}}
        h = compute_pack_hash(files)
        assert verify_pack_hash(files, h)
        assert not verify_pack_hash(files, "wrong")


class TestGenerateId:
    def test_format(self):
        id_ = generate_id("RWMF")
        assert id_.startswith("RWMF-")
        assert len(id_) == 21  # "RWMF-" + 16 hex chars

    def test_unique(self):
        ids = {generate_id("RWMF") for _ in range(100)}
        assert len(ids) == 100
