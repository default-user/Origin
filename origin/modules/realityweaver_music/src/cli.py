#!/usr/bin/env python3
# RealityWeaverMusic CLI
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Command-line interface for RealityWeaverMusic.

Usage:
    rxm validate <input.rxm>
    rxm info <input.rxm>
    rxm pack --score <score_file> [--audio <audio_file>] [--sync <sync_file>] -o <output.rxm>
    rxm unpack <input.rxm> -o <output_dir>
    rxm selftest
"""

import argparse
import json
import os
import struct
import sys
from pathlib import Path

try:
    from .container import (
        pack, unpack, pack_bytes, unpack_bytes,
        validate_container, get_container_info, validate_sync, RXMError,
    )
    from .rxm_types import (
        RXMConfig, RXMMetadata, SyncEntry,
        CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI,
    )
except ImportError:
    from container import (
        pack, unpack, pack_bytes, unpack_bytes,
        validate_container, get_container_info, validate_sync, RXMError,
    )
    from rxm_types import (
        RXMConfig, RXMMetadata, SyncEntry,
        CHUNK_META, CHUNK_SCOR, CHUNK_SYNC, CHUNK_AUDI,
    )


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate an RXM container."""
    try:
        with open(args.input, 'rb') as f:
            container = f.read()

        is_valid, errors = validate_container(container)

        if is_valid:
            print(f"VALID: {args.input}")
            info = get_container_info(container)
            print(f"  Mode:   {info.mode}")
            print(f"  Chunks: {info.chunk_count}")
            return 0
        else:
            print(f"INVALID: {args.input}")
            for error in errors:
                print(f"  - {error}")
            return 1

    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Show container information."""
    try:
        with open(args.input, 'rb') as f:
            container = f.read()

        info = get_container_info(container)

        print(f"RXM1 Container: {args.input}")
        print(f"  File size:    {info.total_size:,} bytes")
        print(f"  Version:      {info.version}")
        print(f"  Flags:        {info.flags:#04x}")
        print(f"  Mode:         {info.mode}")
        print(f"  Chunk count:  {info.chunk_count}")
        print(f"  Has SHA-256:  {info.has_sha256}")
        print(f"  Has audio:    {info.has_audio}")
        print(f"  Has sync:     {info.has_sync}")

        if info.sha256_hex:
            print(f"  SHA-256:      {info.sha256_hex}")

        if info.chunks:
            print(f"  Chunks:")
            for chunk in info.chunks:
                print(f"    {chunk.type_str}: {chunk.data_size:,} bytes")

        if info.metadata:
            print(f"  Metadata:")
            for key, value in info.metadata.items():
                print(f"    {key}: {value}")

        if info.sync_entry_count > 0:
            print(f"  Sync entries: {info.sync_entry_count}")

        return 0

    except RXMError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def _parse_sync_file(path: str) -> list:
    """Parse a sync file (JSON array of [tick, frame] pairs)."""
    with open(path, 'r') as f:
        data = json.load(f)

    entries = []
    for pair in data:
        if len(pair) != 2:
            raise RXMError(f"Invalid sync entry: {pair}")
        entries.append(SyncEntry(score_tick=pair[0], audio_frame=pair[1]))

    return entries


def cmd_pack(args: argparse.Namespace) -> int:
    """Pack files into an RXM container."""
    try:
        # Read score data
        with open(args.score, 'rb') as f:
            score_data = f.read()

        # Read optional audio data
        audio_data = None
        if args.audio:
            with open(args.audio, 'rb') as f:
                audio_data = f.read()

        # Read optional sync map
        sync_entries = None
        if args.sync:
            sync_entries = _parse_sync_file(args.sync)

        # Build metadata
        metadata = RXMMetadata(
            title=args.title or Path(args.score).stem,
            composer=args.composer or "",
            tempo_bpm=args.tempo,
            time_signature=args.time_sig,
            score_format="midi",
            audio_format=Path(args.audio).suffix.lstrip('.') if args.audio else "",
        )

        # Build config
        config = RXMConfig(
            include_sha256=args.sha256,
            rwv1_block_size=args.block_size,
            rwv1_allow_bz2=args.allow_bz2,
            rwv1_allow_lzma=args.allow_lzma,
        )

        info = pack(args.output, metadata, score_data, audio_data,
                     sync_entries, config)

        input_size = len(score_data) + (len(audio_data) if audio_data else 0)
        output_size = Path(args.output).stat().st_size

        print(f"Packed: {args.output}")
        print(f"  Mode:        {info.mode}")
        print(f"  Input size:  {input_size:,} bytes")
        print(f"  Output size: {output_size:,} bytes")
        print(f"  Chunks:      {info.chunk_count}")

        if info.chunks:
            for chunk in info.chunks:
                print(f"    {chunk.type_str}: {chunk.data_size:,} bytes")

        return 0

    except RXMError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_unpack(args: argparse.Namespace) -> int:
    """Unpack an RXM container."""
    try:
        result = unpack(args.input)

        output_dir = args.output
        os.makedirs(output_dir, exist_ok=True)

        # Write metadata
        meta_path = os.path.join(output_dir, 'metadata.json')
        with open(meta_path, 'w') as f:
            json.dump(result['metadata'].to_dict(), f, indent=2)
        print(f"  Metadata:  {meta_path}")

        # Write score
        score_path = os.path.join(output_dir, 'score.mid')
        with open(score_path, 'wb') as f:
            f.write(result['score_data'])
        print(f"  Score:     {score_path} ({len(result['score_data']):,} bytes)")

        # Write audio if present
        if result['audio_data'] is not None:
            ext = result['metadata'].audio_format or 'raw'
            audio_path = os.path.join(output_dir, f'audio.{ext}')
            with open(audio_path, 'wb') as f:
                f.write(result['audio_data'])
            print(f"  Audio:     {audio_path} ({len(result['audio_data']):,} bytes)")

        # Write sync map if present
        if result['sync_entries'] is not None:
            sync_path = os.path.join(output_dir, 'sync.json')
            sync_data = [[e.score_tick, e.audio_frame] for e in result['sync_entries']]
            with open(sync_path, 'w') as f:
                json.dump(sync_data, f, indent=2)
            print(f"  Sync map:  {sync_path} ({len(result['sync_entries'])} entries)")

        # Write extra chunks if present
        for fourcc, data in result['extra_chunks']:
            chunk_name = fourcc.decode('ascii', errors='replace')
            chunk_path = os.path.join(output_dir, f'chunk_{chunk_name}.bin')
            with open(chunk_path, 'wb') as f:
                f.write(data)
            print(f"  Extra:     {chunk_path} ({len(data):,} bytes)")

        print(f"\nUnpacked to: {output_dir}")
        return 0

    except RXMError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run self-tests."""
    print("Running RealityWeaverMusic self-tests...")
    failures = 0

    # Test 1: Score-only roundtrip
    print("\n[Test 1] Score-only roundtrip")
    try:
        score = b'MThd' + b'\x00' * 100  # Minimal MIDI-like data
        metadata = RXMMetadata(title="Test", composer="Self-test")
        container = pack_bytes(metadata, score)
        result = unpack_bytes(container)
        if result['score_data'] == score and result['metadata'].title == "Test":
            print("  PASS: Score-only roundtrip")
        else:
            print("  FAIL: Data mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 2: Score+audio roundtrip
    print("\n[Test 2] Score+audio roundtrip")
    try:
        score = b'MThd' + bytes(range(256)) * 4
        audio = bytes(range(256)) * 40
        sync = [SyncEntry(i * 100, i * 4410) for i in range(10)]
        metadata = RXMMetadata(title="Audio Test", audio_format="raw")
        container = pack_bytes(metadata, score, audio, sync)
        result = unpack_bytes(container)
        if (result['score_data'] == score and
            result['audio_data'] == audio and
            len(result['sync_entries']) == 10):
            print("  PASS: Score+audio roundtrip")
        else:
            print("  FAIL: Data mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 3: SHA-256 verification
    print("\n[Test 3] SHA-256 verification")
    try:
        score = b'integrity test data'
        metadata = RXMMetadata(title="SHA256 Test")
        config = RXMConfig(include_sha256=True)
        container = pack_bytes(metadata, score, config=config)
        result = unpack_bytes(container)
        if result['score_data'] == score:
            print("  PASS: SHA-256 verified")
        else:
            print("  FAIL: Data mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 4: Non-monotonic sync rejection
    print("\n[Test 4] Non-monotonic sync rejection")
    try:
        score = b'test'
        audio = b'audio'
        bad_sync = [SyncEntry(100, 4410), SyncEntry(50, 8820)]  # Non-monotonic
        metadata = RXMMetadata(title="Bad Sync")
        try:
            pack_bytes(metadata, score, audio, bad_sync)
            print("  FAIL: Should have rejected non-monotonic sync")
            failures += 1
        except RXMError as e:
            if "monotonic" in str(e).lower():
                print("  PASS: Non-monotonic sync rejected")
            else:
                print(f"  FAIL: Wrong error: {e}")
                failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 5: Invalid magic rejection
    print("\n[Test 5] Invalid magic rejection")
    try:
        bad_container = b'XXXX' + b'\x00' * 20
        is_valid, errors = validate_container(bad_container)
        if not is_valid and any("magic" in e.lower() for e in errors):
            print("  PASS: Invalid magic rejected")
        else:
            print("  FAIL: Should have rejected invalid magic")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 6: Forward compatibility (unknown chunks preserved)
    print("\n[Test 6] Unknown chunk preservation")
    try:
        score = b'test score'
        metadata = RXMMetadata(title="Extra Chunks")
        extra = [(b'XTRA', b'extra data'), (b'TEST', b'test data')]
        container = pack_bytes(metadata, score, extra_chunks=extra)
        result = unpack_bytes(container)
        if (len(result['extra_chunks']) == 2 and
            result['extra_chunks'][0] == (b'XTRA', b'extra data') and
            result['extra_chunks'][1] == (b'TEST', b'test data')):
            print("  PASS: Unknown chunks preserved")
        else:
            print("  FAIL: Chunks not preserved correctly")
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
        prog='rxm',
        description='RealityWeaverMusic (RXM1) container tool',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # validate command
    validate_parser = subparsers.add_parser('validate',
                                             help='Validate an RXM container')
    validate_parser.add_argument('input', help='Input file (.rxm)')

    # info command
    info_parser = subparsers.add_parser('info', help='Show container info')
    info_parser.add_argument('input', help='Input file (.rxm)')

    # pack command
    pack_parser = subparsers.add_parser('pack',
                                         help='Pack files into RXM container')
    pack_parser.add_argument('--score', required=True,
                              help='Score file (MIDI)')
    pack_parser.add_argument('--audio',
                              help='Audio file (optional)')
    pack_parser.add_argument('--sync',
                              help='Sync map file (JSON, optional)')
    pack_parser.add_argument('-o', '--output', required=True,
                              help='Output file (.rxm)')
    pack_parser.add_argument('--title', help='Track title')
    pack_parser.add_argument('--composer', help='Composer name')
    pack_parser.add_argument('--tempo', type=float, default=120.0,
                              help='Tempo in BPM (default: 120)')
    pack_parser.add_argument('--time-sig', default='4/4',
                              help='Time signature (default: 4/4)')
    pack_parser.add_argument('--sha256', action='store_true',
                              help='Include SHA-256 checksum')
    pack_parser.add_argument('--block-size', type=int, default=1 << 20,
                              help='RWV1 block size (default: 1 MiB)')
    pack_parser.add_argument('--allow-bz2', action='store_true',
                              help='Enable bz2 compression branch')
    pack_parser.add_argument('--allow-lzma', action='store_true',
                              help='Enable lzma compression branch')

    # unpack command
    unpack_parser = subparsers.add_parser('unpack',
                                           help='Unpack RXM container')
    unpack_parser.add_argument('input', help='Input file (.rxm)')
    unpack_parser.add_argument('-o', '--output', required=True,
                                help='Output directory')

    # selftest command
    subparsers.add_parser('selftest', help='Run self-tests')

    args = parser.parse_args()

    if args.command == 'validate':
        return cmd_validate(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'pack':
        return cmd_pack(args)
    elif args.command == 'unpack':
        return cmd_unpack(args)
    elif args.command == 'selftest':
        return cmd_selftest(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
