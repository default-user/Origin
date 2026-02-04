# PhraseWeave (PWV1) - Reversible Transform + Dictionary Format
# Attribution: Ande → Kai
# License: WCL-1.0

"""
PhraseWeave: A reversible byte transformation system using dictionary-based encoding.

Core invariant: unweave(weave(x)) == x for all valid x

This module implements:
- PWV1 woven byte stream format
- PWDC dictionary format
- Reversible encode/decode operations
"""

from .codec import phraseweave_encode, phraseweave_decode
from .dictionary import Dictionary, DictionaryEntry, load_dictionary, save_dictionary
from .types import Config, Metadata, DomainType

__all__ = [
    'phraseweave_encode',
    'phraseweave_decode',
    'Dictionary',
    'DictionaryEntry',
    'load_dictionary',
    'save_dictionary',
    'Config',
    'Metadata',
    'DomainType',
]

__version__ = '1.0.0'
