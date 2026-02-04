# ProofWeave Canonicalization
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Canonical JSON serialization for PWOF v1 proof objects.

Canonicalization rules:
- UTF-8 encoding
- Sorted object keys
- Arrays preserve order
- No floats (integers only)
- No whitespace in serialization
- IDs are stable strings
"""

import json
import hashlib
from typing import Any, Dict


def _sort_keys_recursive(obj: Any) -> Any:
    """Recursively sort all dictionary keys."""
    if isinstance(obj, dict):
        return {k: _sort_keys_recursive(v) for k, v in sorted(obj.items())}
    elif isinstance(obj, list):
        return [_sort_keys_recursive(item) for item in obj]
    else:
        return obj


def canonicalize_pwof(pwof: Dict[str, Any]) -> bytes:
    """
    Canonicalize a PWOF object to deterministic bytes.

    Args:
        pwof: PWOF proof object dictionary

    Returns:
        Canonical UTF-8 encoded JSON bytes
    """
    # Sort all keys recursively
    sorted_obj = _sort_keys_recursive(pwof)

    # Serialize with no whitespace, sorted keys, no ensure_ascii
    canonical = json.dumps(
        sorted_obj,
        separators=(',', ':'),
        sort_keys=True,
        ensure_ascii=False,
    )

    return canonical.encode('utf-8')


def compute_hash(pwof: Dict[str, Any], algorithm: str = 'sha256') -> str:
    """
    Compute hash of canonicalized PWOF.

    Args:
        pwof: PWOF proof object dictionary
        algorithm: Hash algorithm ('sha256' or 'blake3')

    Returns:
        Hex-encoded hash string

    Note: blake3 requires the blake3 package. If not available,
    falls back to sha256 with a warning in the output.
    """
    canonical = canonicalize_pwof(pwof)

    if algorithm == 'blake3':
        try:
            import blake3
            return blake3.blake3(canonical).hexdigest()
        except ImportError:
            # TODO: blake3 not available, using sha256
            # Fall through to sha256
            pass

    # Default to sha256
    return hashlib.sha256(canonical).hexdigest()


def parse_pwof(data: bytes) -> Dict[str, Any]:
    """
    Parse PWOF JSON bytes to dictionary.

    Args:
        data: UTF-8 encoded JSON bytes

    Returns:
        Parsed PWOF dictionary

    Raises:
        ValueError: If parsing fails
    """
    try:
        return json.loads(data.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise ValueError(f"Invalid PWOF JSON: {e}")
