"""
RW-0: Primitives and hashing.

Deterministic hashing, ID generation, and canonical JSON serialisation.
No RNG. No timestamps in hash computation. Same input -> same output.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from typing import Any


def sha256_bytes(data: bytes) -> str:
    """Compute SHA-256 hex digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str) -> str:
    """Compute SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def canonical_json(obj: Any) -> bytes:
    """Canonical JSON: sorted keys, no trailing whitespace, UTF-8, newline-terminated."""
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def canonical_json_pretty(obj: Any) -> bytes:
    """Pretty-printed canonical JSON for human-readable artefacts."""
    return (json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def compute_pack_hash(files: dict[str, dict]) -> str:
    """
    Compute pack_hash from file entries.

    Matches DpackManifest.compute_pack_hash: SHA-256 of sorted
    path:sha256 lines concatenated.
    """
    h = hashlib.sha256()
    for path in sorted(files.keys()):
        entry = files[path]
        h.update(path.encode())
        h.update(b":")
        h.update(entry["sha256"].encode())
        h.update(b"\n")
    return h.hexdigest()


def generate_id(prefix: str) -> str:
    """
    Generate a deterministic-style ID with the given prefix.

    Uses os.urandom for uniqueness. Format: PREFIX-<16 hex chars>.
    """
    return f"{prefix}-{os.urandom(8).hex()}"


def now_iso() -> str:
    """Current UTC time in ISO 8601 format."""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def verify_pack_hash(files: dict[str, dict], expected_hash: str) -> bool:
    """Verify that pack_hash matches the file entries."""
    return compute_pack_hash(files) == expected_hash
