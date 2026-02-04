#!/usr/bin/env python3
# PhraseWeave CLI
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Command-line interface for PhraseWeave encoding/decoding.

Usage:
    phraseweave encode <input> <output> [--dict <dict_file>]
    phraseweave decode <input> <output> [--dict <dict_file>]
    phraseweave info <input>
    phraseweave dict-info <dict_file>
    phraseweave selftest
"""

import argparse
import sys
from pathlib import Path

from .codec import phraseweave_encode, phraseweave_decode, PhraseWeaveError
from .dictionary import Dictionary, load_dictionary, save_dictionary
from .types import Config, PWV1_MAGIC, PWV1_HEADER_SIZE


def cmd_encode(args: argparse.Namespace) -> int:
    """Encode a file using PhraseWeave."""
    try:
        with open(args.input, 'rb') as f:
            raw = f.read()

        if args.dict:
            dictionary = load_dictionary(args.dict)
        else:
            dictionary = Dictionary()

        config = Config(
            min_phrase_len=args.min_phrase_len,
            max_phrase_len=args.max_phrase_len,
            greedy=not args.no_greedy,
        )

        woven, metadata = phraseweave_encode(raw, dictionary, config)

        with open(args.output, 'wb') as f:
            f.write(woven)

        print(f"Encoded {metadata.original_len} bytes -> {metadata.woven_len} bytes")
        print(f"  Stan tokens: {metadata.stan_count}")
        print(f"  Literal bytes: {metadata.literal_count}")
        print(f"  Phrase tokens: {metadata.phrase_count}")

        return 0

    except PhraseWeaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_decode(args: argparse.Namespace) -> int:
    """Decode a PhraseWeave file."""
    try:
        with open(args.input, 'rb') as f:
            woven = f.read()

        if args.dict:
            dictionary = load_dictionary(args.dict)
        else:
            dictionary = Dictionary()

        config = Config(
            max_output_size=args.max_output_size,
        )

        raw = phraseweave_decode(woven, dictionary, config)

        with open(args.output, 'wb') as f:
            f.write(raw)

        print(f"Decoded {len(woven)} bytes -> {len(raw)} bytes")

        return 0

    except PhraseWeaveError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display information about a PWV1 file."""
    try:
        with open(args.input, 'rb') as f:
            data = f.read()

        if len(data) < PWV1_HEADER_SIZE:
            print(f"Error: File too small ({len(data)} bytes)")
            return 1

        if data[:4] != PWV1_MAGIC:
            print(f"Error: Not a PWV1 file (magic: {data[:4]!r})")
            return 1

        version = data[4]
        flags = data[5]
        dict_id = data[6:38].hex()

        print(f"PWV1 File: {args.input}")
        print(f"  Total size: {len(data)} bytes")
        print(f"  Version: {version}")
        print(f"  Flags: {flags:#04x}")
        print(f"  Dictionary ID: {dict_id}")
        print(f"  Token stream size: {len(data) - PWV1_HEADER_SIZE} bytes")

        return 0

    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_dict_info(args: argparse.Namespace) -> int:
    """Display information about a PWDC dictionary file."""
    try:
        dictionary = load_dictionary(args.dict_file)

        print(f"PWDC Dictionary: {args.dict_file}")
        print(f"  Version: {dictionary.version}")
        print(f"  Domain: {dictionary.domain.name}")
        print(f"  Entry count: {len(dictionary.entries)}")
        print(f"  Phrase count: {len(dictionary.phrases)}")
        print(f"  Dictionary ID: {dictionary.compute_canonical_id().hex()}")

        if dictionary.entries:
            total_raw_size = sum(len(e.raw_form) for e in dictionary.entries.values())
            print(f"  Total raw form size: {total_raw_size} bytes")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run self-tests to verify PhraseWeave implementation."""
    import hashlib

    print("Running PhraseWeave self-tests...")
    failures = 0

    # Test 1: Empty input, empty dictionary
    print("\n[Test 1] Empty input with empty dictionary")
    try:
        dictionary = Dictionary()
        raw = b''
        woven, metadata = phraseweave_encode(raw, dictionary)

        # Expected: 38 bytes header (PWV1 + version + flags + sha256(empty))
        expected_dict_id = hashlib.sha256(b'').digest()
        expected = PWV1_MAGIC + bytes([1, 0]) + expected_dict_id

        if woven == expected:
            print("  PASS: Output matches expected 38 bytes")
        else:
            print(f"  FAIL: Expected {expected.hex()}")
            print(f"        Got      {woven.hex()}")
            failures += 1

        # Verify roundtrip
        decoded = phraseweave_decode(woven, dictionary)
        if decoded == raw:
            print("  PASS: Roundtrip successful")
        else:
            print("  FAIL: Roundtrip failed")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 2: Simple text with dictionary
    print("\n[Test 2] Simple text with dictionary entries")
    try:
        dictionary = Dictionary()
        dictionary.add_entry(1, b'hello')
        dictionary.add_entry(2, b'world')

        raw = b'hello world hello'
        woven, metadata = phraseweave_encode(raw, dictionary)

        # Verify roundtrip
        decoded = phraseweave_decode(woven, dictionary)
        if decoded == raw:
            print("  PASS: Roundtrip successful")
            print(f"  Compression: {len(raw)} -> {len(woven)} bytes")
            print(f"  Stan tokens: {metadata.stan_count}, Literals: {metadata.literal_count}")
        else:
            print(f"  FAIL: Decoded '{decoded}' != original '{raw}'")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 3: Binary data with literals only
    print("\n[Test 3] Binary data (literals only)")
    try:
        dictionary = Dictionary()
        raw = bytes(range(256))
        woven, metadata = phraseweave_encode(raw, dictionary)

        decoded = phraseweave_decode(woven, dictionary)
        if decoded == raw:
            print("  PASS: Roundtrip successful")
            print(f"  Size: {len(raw)} -> {len(woven)} bytes")
        else:
            print("  FAIL: Roundtrip failed")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 4: Dictionary serialization roundtrip
    print("\n[Test 4] Dictionary PWDC serialization")
    try:
        dictionary = Dictionary()
        dictionary.add_entry(1, b'test')
        dictionary.add_entry(2, b'data')
        dictionary.add_entry(10, b'phrase')

        data = dictionary.to_bytes()
        loaded = Dictionary.from_bytes(data)

        if (loaded.entries.keys() == dictionary.entries.keys() and
            all(loaded.entries[k].raw_form == dictionary.entries[k].raw_form
                for k in dictionary.entries)):
            print("  PASS: Dictionary roundtrip successful")
        else:
            print("  FAIL: Dictionary roundtrip failed")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Summary
    print(f"\n{'=' * 40}")
    if failures == 0:
        print("All tests PASSED")
        return 0
    else:
        print(f"{failures} test(s) FAILED")
        return 1


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog='phraseweave',
        description='PhraseWeave (PWV1) encoding/decoding tool',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # encode command
    encode_parser = subparsers.add_parser('encode', help='Encode a file')
    encode_parser.add_argument('input', help='Input file')
    encode_parser.add_argument('output', help='Output file')
    encode_parser.add_argument('--dict', help='Dictionary file (PWDC format)')
    encode_parser.add_argument('--min-phrase-len', type=int, default=2)
    encode_parser.add_argument('--max-phrase-len', type=int, default=64)
    encode_parser.add_argument('--no-greedy', action='store_true')

    # decode command
    decode_parser = subparsers.add_parser('decode', help='Decode a file')
    decode_parser.add_argument('input', help='Input file (PWV1)')
    decode_parser.add_argument('output', help='Output file')
    decode_parser.add_argument('--dict', help='Dictionary file (PWDC format)')
    decode_parser.add_argument('--max-output-size', type=int, default=None)

    # info command
    info_parser = subparsers.add_parser('info', help='Show PWV1 file info')
    info_parser.add_argument('input', help='Input file (PWV1)')

    # dict-info command
    dict_info_parser = subparsers.add_parser('dict-info', help='Show dictionary info')
    dict_info_parser.add_argument('dict_file', help='Dictionary file (PWDC)')

    # selftest command
    selftest_parser = subparsers.add_parser('selftest', help='Run self-tests')

    args = parser.parse_args()

    if args.command == 'encode':
        return cmd_encode(args)
    elif args.command == 'decode':
        return cmd_decode(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'dict-info':
        return cmd_dict_info(args)
    elif args.command == 'selftest':
        return cmd_selftest(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
