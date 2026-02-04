# PhraseWeave Codec (PWV1 Format)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
PWV1 Woven Byte Stream Format encoder/decoder.

Header (fixed 38 bytes):
  MAGIC "PWV1" (4)
  VERSION 1 (u8)
  FLAGS (u8) = 0x00 for v1
  DICT_ID (32 bytes) = sha256 of dictionary canonical form

Token stream (until EOF):
  TokenType (1 byte):
    0x00 LITERAL  : [type][byte_value]
    0x01 STAN     : [type][stan_id varint]
    0x02 PHRASE   : [type][phrase_id varint][length varint]
    0x03 REPEAT   : [type][count varint]

Core invariant: phraseweave_decode(phraseweave_encode(x)) == x
"""

from typing import List, Tuple, Optional

from .types import (
    Config,
    Metadata,
    TokenType,
    PWV1_MAGIC,
    PWV1_VERSION,
    PWV1_FLAGS,
    PWV1_HEADER_SIZE,
)
from .dictionary import Dictionary, encode_varint, decode_varint


class PhraseWeaveError(Exception):
    """Base exception for PhraseWeave errors."""
    pass


class EncodingError(PhraseWeaveError):
    """Error during encoding."""
    pass


class DecodingError(PhraseWeaveError):
    """Error during decoding."""
    pass


def _build_reverse_index(dictionary: Dictionary, config: Config) -> dict:
    """
    Build reverse index from raw_form -> stan_id.
    Only includes entries within config length bounds.
    Returns dict sorted by key length (longest first) for greedy matching.
    """
    reverse = {}
    for stan_id, entry in dictionary.entries.items():
        raw_len = len(entry.raw_form)
        if config.min_phrase_len <= raw_len <= config.max_phrase_len:
            reverse[entry.raw_form] = stan_id
    return reverse


def phraseweave_encode(
    raw: bytes,
    dictionary: Dictionary,
    config: Optional[Config] = None
) -> Tuple[bytes, Metadata]:
    """
    Encode raw bytes into PWV1 woven format.

    Args:
        raw: Input bytes to encode
        dictionary: PhraseWeave dictionary
        config: Optional encoding configuration

    Returns:
        Tuple of (woven bytes, metadata)

    Raises:
        EncodingError: If encoding fails
    """
    if config is None:
        config = Config()
    config.validate()

    metadata = Metadata(original_len=len(raw))

    # Build header
    result = bytearray()
    result.extend(PWV1_MAGIC)
    result.append(PWV1_VERSION)
    result.append(PWV1_FLAGS)
    result.extend(dictionary.compute_canonical_id())

    # Build reverse index for matching
    reverse_index = _build_reverse_index(dictionary, config)

    # Sort by length descending for greedy matching
    sorted_patterns = sorted(
        reverse_index.keys(),
        key=lambda x: len(x),
        reverse=True
    )

    # Encode token stream
    pos = 0
    tokens: List[Tuple[TokenType, bytes]] = []
    last_expansion: Optional[bytes] = None

    while pos < len(raw):
        matched = False

        if config.greedy and sorted_patterns:
            # Try to match longest patterns first
            for pattern in sorted_patterns:
                if raw[pos:pos + len(pattern)] == pattern:
                    stan_id = reverse_index[pattern]
                    token_data = bytes([TokenType.STAN]) + encode_varint(stan_id)
                    tokens.append((TokenType.STAN, token_data))
                    metadata.stan_count += 1
                    last_expansion = pattern
                    pos += len(pattern)
                    matched = True
                    break

        if not matched:
            # Emit literal byte
            token_data = bytes([TokenType.LITERAL, raw[pos]])
            tokens.append((TokenType.LITERAL, token_data))
            metadata.literal_count += 1
            last_expansion = bytes([raw[pos]])
            pos += 1

    # Flatten tokens to bytes
    for _, token_data in tokens:
        result.extend(token_data)

    woven = bytes(result)
    metadata.woven_len = len(woven)

    return woven, metadata


def phraseweave_decode(
    woven: bytes,
    dictionary: Dictionary,
    config: Optional[Config] = None
) -> bytes:
    """
    Decode PWV1 woven format back to raw bytes.

    Args:
        woven: PWV1 woven bytes
        dictionary: PhraseWeave dictionary (must match encoded DICT_ID)
        config: Optional decoding configuration

    Returns:
        Original raw bytes

    Raises:
        DecodingError: If decoding fails
    """
    if config is None:
        config = Config()
    config.validate()

    if len(woven) < PWV1_HEADER_SIZE:
        raise DecodingError(f"Data too short: {len(woven)} < {PWV1_HEADER_SIZE}")

    # Verify header
    if woven[:4] != PWV1_MAGIC:
        raise DecodingError(f"Invalid magic: {woven[:4]!r}")

    version = woven[4]
    if version != PWV1_VERSION:
        raise DecodingError(f"Unsupported version: {version}")

    flags = woven[5]
    if flags != PWV1_FLAGS:
        raise DecodingError(f"Unsupported flags: {flags:#x}")

    # Verify dictionary ID
    stored_dict_id = woven[6:38]
    computed_dict_id = dictionary.compute_canonical_id()
    if stored_dict_id != computed_dict_id:
        raise DecodingError("Dictionary ID mismatch")

    # Decode token stream
    result = bytearray()
    pos = PWV1_HEADER_SIZE
    last_expansion: Optional[bytes] = None

    while pos < len(woven):
        token_type = woven[pos]
        pos += 1

        if token_type == TokenType.LITERAL:
            if pos >= len(woven):
                raise DecodingError("Truncated LITERAL token")
            byte_value = woven[pos]
            pos += 1
            result.append(byte_value)
            last_expansion = bytes([byte_value])

        elif token_type == TokenType.STAN:
            stan_id, consumed = decode_varint(woven, pos)
            pos += consumed
            try:
                raw_form = dictionary.get_raw_form(stan_id)
            except KeyError:
                raise DecodingError(f"Unknown Stan ID: {stan_id}")
            result.extend(raw_form)
            last_expansion = raw_form

        elif token_type == TokenType.PHRASE:
            phrase_id, consumed = decode_varint(woven, pos)
            pos += consumed
            length, consumed = decode_varint(woven, pos)
            pos += consumed

            if phrase_id not in dictionary.phrases:
                raise DecodingError(f"Unknown phrase ID: {phrase_id}")

            phrase = dictionary.phrases[phrase_id]
            expansion = bytearray()
            for stan_id in phrase.stan_ids[:length]:
                try:
                    raw_form = dictionary.get_raw_form(stan_id)
                except KeyError:
                    raise DecodingError(f"Unknown Stan ID in phrase: {stan_id}")
                expansion.extend(raw_form)

            result.extend(expansion)
            last_expansion = bytes(expansion)

        elif token_type == TokenType.REPEAT:
            count, consumed = decode_varint(woven, pos)
            pos += consumed

            if last_expansion is None:
                raise DecodingError("REPEAT with no previous expansion")

            for _ in range(count):
                result.extend(last_expansion)

        else:
            raise DecodingError(f"Unknown token type: {token_type:#x}")

        # Check max output size
        if config.max_output_size is not None and len(result) > config.max_output_size:
            raise DecodingError(f"Output exceeds max_output_size: {len(result)}")

    return bytes(result)
