#!/usr/bin/env python3
# PhraseWeave Test Suite
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Test suite for PhraseWeave encoding/decoding.

Tests cover:
- PWV1 format compliance
- PWDC dictionary format
- Roundtrip invariants
- Edge cases and error handling
- Test vectors for cross-implementation verification
"""

import hashlib
import unittest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from codec import phraseweave_encode, phraseweave_decode, DecodingError
from dictionary import Dictionary, encode_varint, decode_varint
from types import Config, Metadata, PWV1_MAGIC, PWV1_HEADER_SIZE, DomainType


class TestVarint(unittest.TestCase):
    """Test varint encoding/decoding."""

    def test_single_byte(self):
        """Values 0-127 should encode to single byte."""
        for i in range(128):
            encoded = encode_varint(i)
            self.assertEqual(len(encoded), 1)
            decoded, consumed = decode_varint(encoded)
            self.assertEqual(decoded, i)
            self.assertEqual(consumed, 1)

    def test_two_bytes(self):
        """Values 128-16383 should encode to two bytes."""
        test_values = [128, 255, 256, 1000, 16383]
        for val in test_values:
            encoded = encode_varint(val)
            self.assertEqual(len(encoded), 2)
            decoded, consumed = decode_varint(encoded)
            self.assertEqual(decoded, val)
            self.assertEqual(consumed, 2)

    def test_large_values(self):
        """Test larger varint values."""
        test_values = [16384, 65535, 100000, 2**20, 2**28]
        for val in test_values:
            encoded = encode_varint(val)
            decoded, consumed = decode_varint(encoded)
            self.assertEqual(decoded, val)
            self.assertEqual(consumed, len(encoded))

    def test_negative_raises(self):
        """Negative values should raise."""
        with self.assertRaises(ValueError):
            encode_varint(-1)


class TestDictionary(unittest.TestCase):
    """Test PWDC dictionary format."""

    def test_empty_dictionary(self):
        """Empty dictionary should have deterministic ID."""
        d = Dictionary()
        # sha256 of empty string
        expected_id = hashlib.sha256(b'').digest()
        self.assertEqual(d.compute_canonical_id(), expected_id)

    def test_canonical_id_determinism(self):
        """Same entries should produce same ID regardless of insertion order."""
        d1 = Dictionary()
        d1.add_entry(1, b'hello')
        d1.add_entry(2, b'world')

        d2 = Dictionary()
        d2.add_entry(2, b'world')
        d2.add_entry(1, b'hello')

        self.assertEqual(d1.compute_canonical_id(), d2.compute_canonical_id())

    def test_serialization_roundtrip(self):
        """Dictionary should survive serialization."""
        d = Dictionary(domain=DomainType.TEXT)
        d.add_entry(1, b'hello')
        d.add_entry(2, b'world')
        d.add_entry(100, b'longer phrase here')

        data = d.to_bytes()
        d2 = Dictionary.from_bytes(data)

        self.assertEqual(d.domain, d2.domain)
        self.assertEqual(set(d.entries.keys()), set(d2.entries.keys()))
        for key in d.entries:
            self.assertEqual(d.entries[key].raw_form, d2.entries[key].raw_form)

    def test_serialization_with_phrases(self):
        """Dictionary with phrases should serialize correctly."""
        d = Dictionary()
        d.add_entry(1, b'hello')
        d.add_entry(2, b' ')
        d.add_entry(3, b'world')
        d.add_phrase(100, [1, 2, 3])

        data = d.to_bytes()
        d2 = Dictionary.from_bytes(data)

        self.assertEqual(len(d.phrases), len(d2.phrases))
        self.assertEqual(d.phrases[100].stan_ids, d2.phrases[100].stan_ids)

    def test_serialization_with_weights(self):
        """Dictionary with weights should serialize correctly."""
        d = Dictionary()
        d.add_entry(1, b'hello', weight=0.5)
        d.add_entry(2, b'world', weight=0.3)

        data = d.to_bytes()
        d2 = Dictionary.from_bytes(data)

        self.assertAlmostEqual(d2.entries[1].weight, 0.5, places=5)
        self.assertAlmostEqual(d2.entries[2].weight, 0.3, places=5)


class TestPWV1Encoding(unittest.TestCase):
    """Test PWV1 woven format encoding."""

    def test_empty_input_empty_dict(self):
        """Vector 1: Empty input with empty dictionary."""
        dictionary = Dictionary()
        raw = b''
        woven, metadata = phraseweave_encode(raw, dictionary)

        # Expected header (38 bytes)
        expected_dict_id = hashlib.sha256(b'').digest()
        expected = PWV1_MAGIC + bytes([1, 0]) + expected_dict_id

        self.assertEqual(woven, expected)
        self.assertEqual(len(woven), 38)
        self.assertEqual(metadata.original_len, 0)
        self.assertEqual(metadata.woven_len, 38)

    def test_header_structure(self):
        """Verify PWV1 header structure."""
        dictionary = Dictionary()
        dictionary.add_entry(1, b'test')
        woven, _ = phraseweave_encode(b'test', dictionary)

        # Check magic
        self.assertEqual(woven[:4], PWV1_MAGIC)
        # Check version
        self.assertEqual(woven[4], 1)
        # Check flags
        self.assertEqual(woven[5], 0)
        # Check dict_id (32 bytes)
        self.assertEqual(len(woven[6:38]), 32)
        self.assertEqual(woven[6:38], dictionary.compute_canonical_id())

    def test_roundtrip_empty(self):
        """Empty input roundtrip."""
        dictionary = Dictionary()
        raw = b''
        woven, _ = phraseweave_encode(raw, dictionary)
        decoded = phraseweave_decode(woven, dictionary)
        self.assertEqual(decoded, raw)

    def test_roundtrip_literals_only(self):
        """All-literal roundtrip."""
        dictionary = Dictionary()
        raw = b'hello world'
        woven, metadata = phraseweave_encode(raw, dictionary)
        decoded = phraseweave_decode(woven, dictionary)

        self.assertEqual(decoded, raw)
        self.assertEqual(metadata.literal_count, len(raw))
        self.assertEqual(metadata.stan_count, 0)

    def test_roundtrip_with_stans(self):
        """Roundtrip with dictionary entries."""
        dictionary = Dictionary()
        dictionary.add_entry(1, b'hello')
        dictionary.add_entry(2, b'world')

        raw = b'hello world hello'
        woven, metadata = phraseweave_encode(raw, dictionary)
        decoded = phraseweave_decode(woven, dictionary)

        self.assertEqual(decoded, raw)
        self.assertEqual(metadata.stan_count, 2)  # 'hello' twice
        # Space is literal (not in dictionary)

    def test_roundtrip_binary_data(self):
        """Binary data with all byte values."""
        dictionary = Dictionary()
        raw = bytes(range(256))
        woven, _ = phraseweave_encode(raw, dictionary)
        decoded = phraseweave_decode(woven, dictionary)
        self.assertEqual(decoded, raw)

    def test_greedy_matching(self):
        """Greedy should prefer longer matches."""
        dictionary = Dictionary()
        dictionary.add_entry(1, b'he')
        dictionary.add_entry(2, b'hello')

        raw = b'hello'
        woven, metadata = phraseweave_encode(raw, dictionary)
        decoded = phraseweave_decode(woven, dictionary)

        self.assertEqual(decoded, raw)
        # Should use 'hello' (stan 2), not 'he' + literals
        self.assertEqual(metadata.stan_count, 1)

    def test_config_min_phrase_len(self):
        """Respect min_phrase_len config."""
        dictionary = Dictionary()
        dictionary.add_entry(1, b'a')  # Too short with min=2

        config = Config(min_phrase_len=2)
        raw = b'aaa'
        woven, metadata = phraseweave_encode(raw, dictionary, config)

        # Should use all literals since 'a' is too short
        self.assertEqual(metadata.literal_count, 3)
        self.assertEqual(metadata.stan_count, 0)


class TestPWV1Decoding(unittest.TestCase):
    """Test PWV1 decoding error handling."""

    def test_invalid_magic(self):
        """Invalid magic should fail."""
        data = b'XXXX' + bytes(34)
        dictionary = Dictionary()
        with self.assertRaises(DecodingError) as ctx:
            phraseweave_decode(data, dictionary)
        self.assertIn('magic', str(ctx.exception).lower())

    def test_truncated_header(self):
        """Truncated header should fail."""
        data = PWV1_MAGIC + bytes(10)  # Too short
        dictionary = Dictionary()
        with self.assertRaises(DecodingError):
            phraseweave_decode(data, dictionary)

    def test_dict_id_mismatch(self):
        """Mismatched dictionary ID should fail."""
        dictionary = Dictionary()
        woven, _ = phraseweave_encode(b'test', dictionary)

        # Use different dictionary for decode
        dictionary2 = Dictionary()
        dictionary2.add_entry(1, b'different')

        with self.assertRaises(DecodingError) as ctx:
            phraseweave_decode(woven, dictionary2)
        self.assertIn('mismatch', str(ctx.exception).lower())

    def test_max_output_size(self):
        """Respect max_output_size limit."""
        dictionary = Dictionary()
        raw = b'x' * 1000
        woven, _ = phraseweave_encode(raw, dictionary)

        config = Config(max_output_size=100)
        with self.assertRaises(DecodingError) as ctx:
            phraseweave_decode(woven, dictionary, config)
        self.assertIn('max_output_size', str(ctx.exception).lower())


class TestVectors(unittest.TestCase):
    """Cross-implementation test vectors."""

    def test_vector_1_empty_input_empty_dict(self):
        """
        Vector 1: Empty input, empty dictionary, default config.
        Expected woven bytes (hex):
            50 57 56 31  # "PWV1"
            01           # version
            00           # flags
            e3 b0 c4 42 98 fc 1c 14 9a fb f4 c8 99 6f b9 24
            27 ae 41 e4 64 9b 93 4c a4 95 99 1b 78 52 b8 55  # sha256(empty)
        Total: 38 bytes
        """
        expected_hex = (
            "50575631"  # PWV1
            "01"        # version
            "00"        # flags
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # sha256(empty)
        )
        expected = bytes.fromhex(expected_hex)

        dictionary = Dictionary()
        raw = b''
        woven, _ = phraseweave_encode(raw, dictionary)

        self.assertEqual(woven, expected)
        self.assertEqual(len(woven), 38)


class TestDeterminism(unittest.TestCase):
    """Verify deterministic behavior."""

    def test_same_input_same_output(self):
        """Same input should always produce same output."""
        dictionary = Dictionary()
        dictionary.add_entry(1, b'hello')
        dictionary.add_entry(2, b'world')

        raw = b'hello world test data hello'
        results = [phraseweave_encode(raw, dictionary)[0] for _ in range(10)]

        # All results should be identical
        self.assertTrue(all(r == results[0] for r in results))

    def test_dictionary_order_independence(self):
        """Dictionary entry order shouldn't affect output."""
        d1 = Dictionary()
        d1.add_entry(1, b'hello')
        d1.add_entry(2, b'world')

        d2 = Dictionary()
        d2.add_entry(2, b'world')
        d2.add_entry(1, b'hello')

        raw = b'hello world'
        woven1, _ = phraseweave_encode(raw, d1)
        woven2, _ = phraseweave_encode(raw, d2)

        self.assertEqual(woven1, woven2)


if __name__ == '__main__':
    unittest.main()
