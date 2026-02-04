# PhraseWeave Types
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Core types for PhraseWeave encoding/decoding.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, List, Optional


class DomainType(IntEnum):
    """Domain type identifiers for dictionaries."""
    GENERAL = 0
    TEXT = 1
    CODE = 2
    BINARY = 3
    STRUCTURED = 4
    CUSTOM = 255


class TokenType(IntEnum):
    """Token types in PWV1 woven stream."""
    LITERAL = 0x00
    STAN = 0x01
    PHRASE = 0x02
    REPEAT = 0x03


@dataclass
class Config:
    """Configuration for PhraseWeave encoding/decoding."""
    min_phrase_len: int = 2
    max_phrase_len: int = 64
    greedy: bool = True
    max_output_size: Optional[int] = None  # None = unlimited

    def validate(self) -> None:
        """Validate configuration parameters."""
        if self.min_phrase_len < 1:
            raise ValueError("min_phrase_len must be >= 1")
        if self.max_phrase_len < self.min_phrase_len:
            raise ValueError("max_phrase_len must be >= min_phrase_len")
        if self.max_output_size is not None and self.max_output_size < 0:
            raise ValueError("max_output_size must be >= 0 or None")


@dataclass
class Metadata:
    """Metadata from PhraseWeave encoding."""
    original_len: int = 0
    stan_count: int = 0
    phrase_count: int = 0
    literal_count: int = 0
    woven_len: int = 0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'original_len': self.original_len,
            'stan_count': self.stan_count,
            'phrase_count': self.phrase_count,
            'literal_count': self.literal_count,
            'woven_len': self.woven_len,
        }


@dataclass
class DictionaryEntry:
    """Single entry in a PhraseWeave dictionary."""
    stan_id: int
    raw_form: bytes
    weight: Optional[float] = None
    frequency: Optional[float] = None


@dataclass
class PhraseEntry:
    """Multi-Stan phrase entry."""
    phrase_id: int
    stan_ids: List[int] = field(default_factory=list)


# PWV1 Constants
PWV1_MAGIC = b'PWV1'
PWV1_VERSION = 1
PWV1_FLAGS = 0x00
PWV1_HEADER_SIZE = 38  # 4 (magic) + 1 (version) + 1 (flags) + 32 (dict_id)

# PWDC Constants
PWDC_MAGIC = b'PWDC'
PWDC_VERSION = 1

# PWDC Flags
PWDC_FLAG_PHRASES_INCLUDED = 0x01
PWDC_FLAG_WEIGHTS_INCLUDED = 0x02
PWDC_FLAG_FREQUENCY_INCLUDED = 0x04
