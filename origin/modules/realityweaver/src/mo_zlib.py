# MO+zlib Branch Encoder
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Middle-Out Dictionary Rewrite + zlib compression.

This is RWV1's per-block phrase dictionary, NOT PhraseWeave.

Token stream rule:
- TOKEN_RAW marker = 0 (u8)
- Output stream bytes:
  - If byte == 0: next byte is literal raw byte
  - Else: byte is dictionary token referencing a phrase

MO+zlib PAYLOAD FORMAT:
  dict_count(u16 big-endian)
  repeated dict_count times:
    token(u8)
    phrase_len(u16 big-endian)
    phrase(bytes[phrase_len])
  comp_len(u32 big-endian)
  comp_bytes[comp_len]  # zlib.compress(token_stream)
"""

import struct
import zlib
from collections import Counter
from typing import Dict, List, Tuple, Optional


# Token constants
TOKEN_RAW = 0
TOKEN_BASE = 1
TOKEN_MAX = 255


class MOZlibError(Exception):
    """Error in MO+zlib encoding/decoding."""
    pass


def _find_phrases(data: bytes, min_len: int = 3, max_len: int = 64) -> List[Tuple[bytes, int]]:
    """
    Find candidate phrases in data.

    Returns list of (phrase, score) sorted by score descending.
    Score = frequency * (len - 1) to favor longer, frequent phrases.
    """
    # Count n-gram frequencies for various lengths
    phrase_counts: Counter = Counter()

    for length in range(min_len, min(max_len + 1, len(data) + 1)):
        for i in range(len(data) - length + 1):
            phrase = data[i:i + length]
            # Skip phrases containing TOKEN_RAW (0) to avoid ambiguity issues
            # Actually, we can include them, just escape properly
            phrase_counts[phrase] += 1

    # Score each phrase: frequency * (length - 1)
    # This favors longer phrases that appear multiple times
    scored = []
    for phrase, count in phrase_counts.items():
        if count >= 2:  # Must appear at least twice to be worth tokenizing
            # Score: bytes saved = count * len - (count + header_overhead)
            # Simplified: count * (len - 1) - header_overhead
            score = count * (len(phrase) - 1)
            scored.append((phrase, score))

    # Sort by score descending
    scored.sort(key=lambda x: -x[1])

    return scored


def _build_dictionary(data: bytes, max_entries: int) -> Dict[bytes, int]:
    """
    Build phrase dictionary from data.

    Returns mapping from phrase -> token (TOKEN_BASE to TOKEN_MAX).
    Entries are sorted longest-first for greedy replacement.
    """
    candidates = _find_phrases(data)

    # Take top candidates up to max_entries and available tokens
    max_tokens = TOKEN_MAX - TOKEN_BASE + 1
    limit = min(max_entries, max_tokens, len(candidates))

    dictionary = {}
    token = TOKEN_BASE

    for phrase, score in candidates[:limit]:
        if token > TOKEN_MAX:
            break
        dictionary[phrase] = token
        token += 1

    return dictionary


def _rewrite_to_tokens(data: bytes, dictionary: Dict[bytes, int]) -> bytes:
    """
    Rewrite data using dictionary tokens.

    Token stream rules:
    - 0 followed by byte = literal byte
    - non-zero = dictionary token
    """
    if not dictionary:
        # No dictionary: emit all as raw
        result = bytearray()
        for byte in data:
            result.append(TOKEN_RAW)
            result.append(byte)
        return bytes(result)

    # Sort patterns by length (longest first) for greedy matching
    patterns = sorted(dictionary.keys(), key=len, reverse=True)

    result = bytearray()
    pos = 0

    while pos < len(data):
        matched = False

        # Try to match longest pattern first
        for pattern in patterns:
            if data[pos:pos + len(pattern)] == pattern:
                result.append(dictionary[pattern])
                pos += len(pattern)
                matched = True
                break

        if not matched:
            # Emit raw byte
            result.append(TOKEN_RAW)
            result.append(data[pos])
            pos += 1

    return bytes(result)


def _rewrite_from_tokens(token_stream: bytes, reverse_dict: Dict[int, bytes]) -> bytes:
    """
    Convert token stream back to original data.
    """
    result = bytearray()
    pos = 0

    while pos < len(token_stream):
        token = token_stream[pos]
        pos += 1

        if token == TOKEN_RAW:
            if pos >= len(token_stream):
                raise MOZlibError("Truncated raw token")
            result.append(token_stream[pos])
            pos += 1
        else:
            if token not in reverse_dict:
                raise MOZlibError(f"Unknown token: {token}")
            result.extend(reverse_dict[token])

    return bytes(result)


def mo_zlib_encode(data: bytes, max_entries: int = 200,
                   zlib_level: int = 9) -> bytes:
    """
    Encode data using MO+zlib.

    Args:
        data: Raw data to encode
        max_entries: Maximum dictionary entries
        zlib_level: zlib compression level (1-9)

    Returns:
        MO+zlib payload bytes
    """
    # Build dictionary from data
    dictionary = _build_dictionary(data, max_entries)

    # Rewrite data to token stream
    token_stream = _rewrite_to_tokens(data, dictionary)

    # Compress token stream with zlib
    compressed = zlib.compress(token_stream, level=zlib_level)

    # Build payload
    result = bytearray()

    # Dictionary count (u16 big-endian)
    result.extend(struct.pack(">H", len(dictionary)))

    # Dictionary entries (sorted by token for determinism)
    for phrase, token in sorted(dictionary.items(), key=lambda x: x[1]):
        result.append(token)
        result.extend(struct.pack(">H", len(phrase)))
        result.extend(phrase)

    # Compressed data length and bytes
    result.extend(struct.pack(">I", len(compressed)))
    result.extend(compressed)

    return bytes(result)


def mo_zlib_decode(payload: bytes) -> bytes:
    """
    Decode MO+zlib payload to original data.

    Args:
        payload: MO+zlib payload bytes

    Returns:
        Original raw data

    Raises:
        MOZlibError: If decoding fails
    """
    if len(payload) < 2:
        raise MOZlibError("Payload too short")

    pos = 0

    # Read dictionary count
    dict_count = struct.unpack(">H", payload[pos:pos + 2])[0]
    pos += 2

    # Read dictionary entries
    reverse_dict: Dict[int, bytes] = {}
    for _ in range(dict_count):
        if pos >= len(payload):
            raise MOZlibError("Truncated dictionary")

        token = payload[pos]
        pos += 1

        if pos + 2 > len(payload):
            raise MOZlibError("Truncated phrase length")
        phrase_len = struct.unpack(">H", payload[pos:pos + 2])[0]
        pos += 2

        if pos + phrase_len > len(payload):
            raise MOZlibError("Truncated phrase data")
        phrase = payload[pos:pos + phrase_len]
        pos += phrase_len

        reverse_dict[token] = phrase

    # Read compressed length
    if pos + 4 > len(payload):
        raise MOZlibError("Truncated compressed length")
    comp_len = struct.unpack(">I", payload[pos:pos + 4])[0]
    pos += 4

    # Read and decompress
    if pos + comp_len > len(payload):
        raise MOZlibError("Truncated compressed data")
    comp_bytes = payload[pos:pos + comp_len]

    try:
        token_stream = zlib.decompress(comp_bytes)
    except zlib.error as e:
        raise MOZlibError(f"zlib decompression failed: {e}")

    # Convert tokens back to original data
    return _rewrite_from_tokens(token_stream, reverse_dict)
