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

Hash algorithms:
- blake3: Preferred for performance (requires blake3 package)
- sha256: Default fallback, always available
"""

import json
import hashlib
import logging
import warnings
from typing import Any, Dict, Optional, Tuple

# Module-level logger
logger = logging.getLogger(__name__)

# Blake3 availability flag (checked once at import)
_blake3_available: Optional[bool] = None
_blake3_module = None


def _check_blake3() -> bool:
    """Check if blake3 is available and cache the result."""
    global _blake3_available, _blake3_module
    if _blake3_available is None:
        try:
            import blake3 as b3
            _blake3_module = b3
            _blake3_available = True
            logger.debug("blake3 hash algorithm available")
        except ImportError:
            _blake3_available = False
            logger.debug("blake3 not available, will use sha256 as fallback")
    return _blake3_available


def is_blake3_available() -> bool:
    """
    Check if blake3 hashing is available.

    Returns:
        True if blake3 package is installed, False otherwise
    """
    return _check_blake3()


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


def compute_hash(pwof: Dict[str, Any], algorithm: str = 'sha256',
                 warn_on_fallback: bool = True) -> str:
    """
    Compute hash of canonicalized PWOF.

    Args:
        pwof: PWOF proof object dictionary
        algorithm: Hash algorithm ('sha256', 'blake3', or 'auto')
                   - 'sha256': Use SHA-256 (always available)
                   - 'blake3': Use BLAKE3 (requires blake3 package)
                   - 'auto': Use blake3 if available, otherwise sha256
        warn_on_fallback: If True, emit warning when falling back to sha256

    Returns:
        Hex-encoded hash string

    Raises:
        ValueError: If algorithm is 'blake3' but blake3 is not available
                   and warn_on_fallback is False
    """
    canonical = canonicalize_pwof(pwof)

    if algorithm == 'auto':
        # Use blake3 if available, otherwise sha256
        if _check_blake3():
            return _blake3_module.blake3(canonical).hexdigest()
        return hashlib.sha256(canonical).hexdigest()

    elif algorithm == 'blake3':
        if _check_blake3():
            return _blake3_module.blake3(canonical).hexdigest()
        else:
            if warn_on_fallback:
                warnings.warn(
                    "blake3 not available, falling back to sha256. "
                    "Install blake3 package for better performance: pip install blake3",
                    RuntimeWarning,
                    stacklevel=2
                )
                return hashlib.sha256(canonical).hexdigest()
            else:
                raise ValueError(
                    "blake3 algorithm requested but blake3 package is not installed. "
                    "Install with: pip install blake3"
                )

    elif algorithm == 'sha256':
        return hashlib.sha256(canonical).hexdigest()

    else:
        raise ValueError(f"Unknown hash algorithm: {algorithm}. "
                        f"Supported: 'sha256', 'blake3', 'auto'")


def compute_hash_with_algorithm(pwof: Dict[str, Any],
                                 preferred: str = 'blake3') -> Tuple[str, str]:
    """
    Compute hash and return both the hash and the algorithm actually used.

    This is useful for recording which algorithm was used in proof metadata.

    Args:
        pwof: PWOF proof object dictionary
        preferred: Preferred algorithm ('blake3' or 'sha256')

    Returns:
        Tuple of (hex_hash, algorithm_used)

    Example:
        >>> hash_val, algo = compute_hash_with_algorithm(proof)
        >>> print(f"Hash ({algo}): {hash_val}")
    """
    canonical = canonicalize_pwof(pwof)

    if preferred == 'blake3' and _check_blake3():
        return _blake3_module.blake3(canonical).hexdigest(), 'blake3'

    # Fall back to sha256
    return hashlib.sha256(canonical).hexdigest(), 'sha256'


def verify_hash(pwof: Dict[str, Any], expected_hash: str,
                algorithm: Optional[str] = None) -> bool:
    """
    Verify that a PWOF object matches an expected hash.

    Args:
        pwof: PWOF proof object dictionary
        expected_hash: Expected hex-encoded hash string
        algorithm: Hash algorithm to use, or None to try both

    Returns:
        True if hash matches, False otherwise
    """
    if algorithm:
        computed = compute_hash(pwof, algorithm, warn_on_fallback=False)
        return computed == expected_hash

    # Try both algorithms if not specified
    sha256_hash = compute_hash(pwof, 'sha256')
    if sha256_hash == expected_hash:
        return True

    if _check_blake3():
        blake3_hash = compute_hash(pwof, 'blake3', warn_on_fallback=False)
        if blake3_hash == expected_hash:
            return True

    return False


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


def create_proof_envelope(pwof: Dict[str, Any],
                          include_hash: bool = True) -> Dict[str, Any]:
    """
    Create a proof envelope with metadata including hash.

    Args:
        pwof: PWOF proof object dictionary
        include_hash: Whether to compute and include hash

    Returns:
        Envelope dictionary with 'proof', 'hash', and 'algorithm' fields
    """
    envelope = {
        'version': 'PWOF/1.0',
        'proof': pwof,
    }

    if include_hash:
        hash_val, algorithm = compute_hash_with_algorithm(pwof)
        envelope['hash'] = hash_val
        envelope['hash_algorithm'] = algorithm

    return envelope
