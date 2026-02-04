# PhraseWeave Dictionary (PWDC) Format
# Attribution: Ande → Kai
# License: WCL-1.0

"""
PWDC (PhraseWeave Dictionary Container) binary format implementation.

Binary format:
  MAGIC: "PWDC" (4 bytes)
  VERSION: uint8
  FLAGS: uint8
    bit0: phrases_included
    bit1: weights_included
    bit2: frequency_included
  DOMAIN: uint16 (big-endian)
  ENTRY_COUNT: uint32 (big-endian)
  DICTIONARY_ID: bytes32

  ENTRIES (repeated ENTRY_COUNT times):
    STAN_ID: varint
    RAW_LEN: varint
    RAW_FORM: bytes[RAW_LEN]
    [WEIGHT: float32 if flags.weights_included]
    [FREQUENCY: float32 if flags.frequency_included]

  If flags.phrases_included:
    PHRASE_COUNT: uint32
    PHRASE_ENTRIES (repeated PHRASE_COUNT times):
      PHRASE_ID: varint
      STAN_COUNT: varint
      STANS: repeated STAN_COUNT of STAN_ID varint
"""

import hashlib
import struct
from dataclasses import dataclass, field
from typing import Dict, List, Optional, BinaryIO

from .types import (
    DictionaryEntry,
    PhraseEntry,
    DomainType,
    PWDC_MAGIC,
    PWDC_VERSION,
    PWDC_FLAG_PHRASES_INCLUDED,
    PWDC_FLAG_WEIGHTS_INCLUDED,
    PWDC_FLAG_FREQUENCY_INCLUDED,
)


def encode_varint(value: int) -> bytes:
    """Encode an unsigned integer as LEB128 varint."""
    if value < 0:
        raise ValueError("Varint must be non-negative")
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            result.append(byte | 0x80)
        else:
            result.append(byte)
            break
    return bytes(result)


def decode_varint(data: bytes, offset: int = 0) -> tuple[int, int]:
    """Decode a varint from bytes, returning (value, bytes_consumed)."""
    result = 0
    shift = 0
    consumed = 0
    while True:
        if offset + consumed >= len(data):
            raise ValueError("Truncated varint")
        byte = data[offset + consumed]
        consumed += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            break
        shift += 7
        if shift > 63:
            raise ValueError("Varint too large")
    return result, consumed


@dataclass
class Dictionary:
    """
    PhraseWeave Dictionary.

    Stores mappings from Stan IDs to raw byte forms, with optional
    phrase entries for multi-Stan sequences.
    """
    entries: Dict[int, DictionaryEntry] = field(default_factory=dict)
    phrases: Dict[int, PhraseEntry] = field(default_factory=dict)
    domain: DomainType = DomainType.GENERAL
    version: int = 1

    def add_entry(self, stan_id: int, raw_form: bytes,
                  weight: Optional[float] = None,
                  frequency: Optional[float] = None) -> None:
        """Add a Stan entry to the dictionary."""
        self.entries[stan_id] = DictionaryEntry(
            stan_id=stan_id,
            raw_form=raw_form,
            weight=weight,
            frequency=frequency,
        )

    def add_phrase(self, phrase_id: int, stan_ids: List[int]) -> None:
        """Add a phrase entry (multi-Stan sequence)."""
        self.phrases[phrase_id] = PhraseEntry(
            phrase_id=phrase_id,
            stan_ids=stan_ids,
        )

    def get_raw_form(self, stan_id: int) -> bytes:
        """Get raw form for a Stan ID."""
        if stan_id not in self.entries:
            raise KeyError(f"Unknown Stan ID: {stan_id}")
        return self.entries[stan_id].raw_form

    def compute_canonical_id(self) -> bytes:
        """
        Compute the canonical dictionary ID (32-byte SHA-256 hash).

        Computed over concatenation for stan_id in sorted order:
          pack(">I", stan_id) + pack(">I", len(raw_form)) + raw_form
        """
        hasher = hashlib.sha256()
        for stan_id in sorted(self.entries.keys()):
            entry = self.entries[stan_id]
            hasher.update(struct.pack(">I", stan_id))
            hasher.update(struct.pack(">I", len(entry.raw_form)))
            hasher.update(entry.raw_form)
        return hasher.digest()

    def to_bytes(self) -> bytes:
        """Serialize dictionary to PWDC binary format."""
        result = bytearray()

        # Magic and version
        result.extend(PWDC_MAGIC)
        result.append(PWDC_VERSION)

        # Compute flags
        flags = 0
        has_phrases = len(self.phrases) > 0
        has_weights = any(e.weight is not None for e in self.entries.values())
        has_frequency = any(e.frequency is not None for e in self.entries.values())

        if has_phrases:
            flags |= PWDC_FLAG_PHRASES_INCLUDED
        if has_weights:
            flags |= PWDC_FLAG_WEIGHTS_INCLUDED
        if has_frequency:
            flags |= PWDC_FLAG_FREQUENCY_INCLUDED

        result.append(flags)

        # Domain and entry count
        result.extend(struct.pack(">H", self.domain))
        result.extend(struct.pack(">I", len(self.entries)))

        # Dictionary ID
        result.extend(self.compute_canonical_id())

        # Entries (sorted by stan_id for determinism)
        for stan_id in sorted(self.entries.keys()):
            entry = self.entries[stan_id]
            result.extend(encode_varint(entry.stan_id))
            result.extend(encode_varint(len(entry.raw_form)))
            result.extend(entry.raw_form)

            if has_weights:
                weight = entry.weight if entry.weight is not None else 0.0
                result.extend(struct.pack(">f", weight))
            if has_frequency:
                freq = entry.frequency if entry.frequency is not None else 0.0
                result.extend(struct.pack(">f", freq))

        # Phrase entries
        if has_phrases:
            result.extend(struct.pack(">I", len(self.phrases)))
            for phrase_id in sorted(self.phrases.keys()):
                phrase = self.phrases[phrase_id]
                result.extend(encode_varint(phrase.phrase_id))
                result.extend(encode_varint(len(phrase.stan_ids)))
                for sid in phrase.stan_ids:
                    result.extend(encode_varint(sid))

        return bytes(result)

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Dictionary':
        """Deserialize dictionary from PWDC binary format."""
        if len(data) < 12:
            raise ValueError("Data too short for PWDC header")

        # Verify magic
        if data[:4] != PWDC_MAGIC:
            raise ValueError(f"Invalid PWDC magic: {data[:4]!r}")

        version = data[4]
        if version != PWDC_VERSION:
            raise ValueError(f"Unsupported PWDC version: {version}")

        flags = data[5]
        has_phrases = bool(flags & PWDC_FLAG_PHRASES_INCLUDED)
        has_weights = bool(flags & PWDC_FLAG_WEIGHTS_INCLUDED)
        has_frequency = bool(flags & PWDC_FLAG_FREQUENCY_INCLUDED)

        domain = DomainType(struct.unpack(">H", data[6:8])[0])
        entry_count = struct.unpack(">I", data[8:12])[0]

        # Skip dictionary ID (32 bytes at offset 12)
        stored_dict_id = data[12:44]
        offset = 44

        # Read entries
        dictionary = cls(domain=domain, version=version)

        for _ in range(entry_count):
            stan_id, consumed = decode_varint(data, offset)
            offset += consumed

            raw_len, consumed = decode_varint(data, offset)
            offset += consumed

            raw_form = data[offset:offset + raw_len]
            offset += raw_len

            weight = None
            frequency = None

            if has_weights:
                weight = struct.unpack(">f", data[offset:offset + 4])[0]
                offset += 4
            if has_frequency:
                frequency = struct.unpack(">f", data[offset:offset + 4])[0]
                offset += 4

            dictionary.add_entry(stan_id, raw_form, weight, frequency)

        # Read phrases
        if has_phrases:
            phrase_count = struct.unpack(">I", data[offset:offset + 4])[0]
            offset += 4

            for _ in range(phrase_count):
                phrase_id, consumed = decode_varint(data, offset)
                offset += consumed

                stan_count, consumed = decode_varint(data, offset)
                offset += consumed

                stan_ids = []
                for _ in range(stan_count):
                    sid, consumed = decode_varint(data, offset)
                    offset += consumed
                    stan_ids.append(sid)

                dictionary.add_phrase(phrase_id, stan_ids)

        # Verify dictionary ID
        computed_id = dictionary.compute_canonical_id()
        if computed_id != stored_dict_id:
            raise ValueError("Dictionary ID mismatch (data corruption)")

        return dictionary


def load_dictionary(path: str) -> Dictionary:
    """Load dictionary from file."""
    with open(path, 'rb') as f:
        return Dictionary.from_bytes(f.read())


def save_dictionary(dictionary: Dictionary, path: str) -> None:
    """Save dictionary to file."""
    with open(path, 'wb') as f:
        f.write(dictionary.to_bytes())
