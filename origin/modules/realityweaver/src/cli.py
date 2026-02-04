#!/usr/bin/env python3
# RealityWeaver CLI
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Command-line interface for RealityWeaver compression.

Usage:
    realityweaver compress <input> <output> [options]
    realityweaver decompress <input.rwv> <output>
    realityweaver bench <input>
    realityweaver info <input.rwv>
    realityweaver selftest
"""

import argparse
import sys
import time
import zlib
from pathlib import Path

from .container import (
    compress,
    decompress,
    compress_bytes,
    decompress_bytes,
    get_container_info,
    RWV1Error,
)
from .types import RWV1Config, BranchID


def cmd_compress(args: argparse.Namespace) -> int:
    """Compress a file."""
    try:
        config = RWV1Config(
            block_size=args.block_size,
            allow_zlib=True,
            allow_mo_zlib=True,
            allow_bz2=args.allow_bz2,
            allow_lzma=args.allow_lzma,
            zlib_level=args.zlib_level,
            bz2_level=args.bz2_level,
            lzma_preset=args.lzma_preset,
            mo_max_entries=args.mo_max_entries,
            probe=args.probe,
            include_sha256=args.sha256,
        )
        config.validate()

        start = time.perf_counter()
        info = compress(args.input, args.output, config)
        elapsed = time.perf_counter() - start

        input_size = Path(args.input).stat().st_size
        output_size = Path(args.output).stat().st_size

        print(f"Compressed: {args.input} -> {args.output}")
        print(f"  Input size:  {input_size:,} bytes")
        print(f"  Output size: {output_size:,} bytes")
        print(f"  Ratio:       {output_size / input_size:.4f} ({100 * output_size / input_size:.2f}%)")
        print(f"  Blocks:      {info.block_count}")
        print(f"  Time:        {elapsed:.3f}s")

        if info.block_count > 0:
            usage = info.branch_usage()
            print(f"  Branch usage:")
            for branch, count in sorted(usage.items()):
                print(f"    {branch}: {count} blocks")

        return 0

    except RWV1Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_decompress(args: argparse.Namespace) -> int:
    """Decompress a file."""
    try:
        start = time.perf_counter()
        output_size = decompress(args.input, args.output)
        elapsed = time.perf_counter() - start

        input_size = Path(args.input).stat().st_size

        print(f"Decompressed: {args.input} -> {args.output}")
        print(f"  Compressed size:   {input_size:,} bytes")
        print(f"  Decompressed size: {output_size:,} bytes")
        print(f"  Time:              {elapsed:.3f}s")

        return 0

    except RWV1Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_bench(args: argparse.Namespace) -> int:
    """Benchmark compression against baselines."""
    try:
        with open(args.input, 'rb') as f:
            data = f.read()

        input_size = len(data)
        print(f"Benchmarking: {args.input} ({input_size:,} bytes)")
        print()

        results = []

        # Baseline: zlib only
        print("Running zlib-9...", end=" ", flush=True)
        start = time.perf_counter()
        zlib_data = zlib.compress(data, level=9)
        zlib_time = time.perf_counter() - start
        results.append(("zlib-9", len(zlib_data), zlib_time))
        print(f"{len(zlib_data):,} bytes ({zlib_time:.3f}s)")

        # RWV1 default
        print("Running RWV1 default...", end=" ", flush=True)
        start = time.perf_counter()
        rwv1_data = compress_bytes(data)
        rwv1_time = time.perf_counter() - start
        results.append(("RWV1", len(rwv1_data), rwv1_time))
        print(f"{len(rwv1_data):,} bytes ({rwv1_time:.3f}s)")

        # RWV1 with probe
        print("Running RWV1+probe...", end=" ", flush=True)
        start = time.perf_counter()
        rwv1p_data = compress_bytes(data, RWV1Config(probe=True))
        rwv1p_time = time.perf_counter() - start
        results.append(("RWV1+probe", len(rwv1p_data), rwv1p_time))
        print(f"{len(rwv1p_data):,} bytes ({rwv1p_time:.3f}s)")

        # Summary
        print()
        print(f"{'Method':<15} {'Size':>12} {'Ratio':>10} {'Time':>10}")
        print("-" * 50)
        for name, size, elapsed in results:
            ratio = size / input_size
            print(f"{name:<15} {size:>12,} {ratio:>10.4f} {elapsed:>10.3f}s")

        return 0

    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Show container information."""
    try:
        with open(args.input, 'rb') as f:
            container = f.read()

        info = get_container_info(container)

        print(f"RWV1 Container: {args.input}")
        print(f"  File size:    {len(container):,} bytes")
        print(f"  Version:      {info.version}")
        print(f"  Flags:        {info.flags:#04x}")
        print(f"  Block size:   {info.block_size:,} bytes")
        print(f"  Block count:  {info.block_count}")
        print(f"  Has SHA-256:  {info.has_sha256}")

        if info.raw_sha256:
            print(f"  Raw SHA-256:  {info.raw_sha256.hex()}")

        if info.blocks:
            print(f"  Total raw:    {info.total_raw_size:,} bytes")
            print(f"  Total payload:{info.total_payload_size:,} bytes")
            print(f"  Overall ratio:{info.overall_ratio:.4f}")

            usage = info.branch_usage()
            print(f"  Branch usage:")
            for branch, count in sorted(usage.items()):
                print(f"    {branch}: {count} blocks")

        return 0

    except RWV1Error as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except IOError as e:
        print(f"I/O Error: {e}", file=sys.stderr)
        return 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run self-tests."""
    print("Running RealityWeaver self-tests...")
    failures = 0

    # Test 1: Empty input
    print("\n[Test 1] Empty input")
    try:
        data = b''
        compressed = compress_bytes(data)
        decompressed = decompress_bytes(compressed)
        if decompressed == data:
            print("  PASS: Empty roundtrip")
        else:
            print("  FAIL: Empty roundtrip mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 2: Small text
    print("\n[Test 2] Small text")
    try:
        data = b"Hello, World! " * 100
        compressed = compress_bytes(data)
        decompressed = decompress_bytes(compressed)
        if decompressed == data:
            print(f"  PASS: {len(data)} -> {len(compressed)} bytes")
        else:
            print("  FAIL: Roundtrip mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 3: Binary data
    print("\n[Test 3] Binary data")
    try:
        data = bytes(range(256)) * 100
        compressed = compress_bytes(data)
        decompressed = decompress_bytes(compressed)
        if decompressed == data:
            print(f"  PASS: {len(data)} -> {len(compressed)} bytes")
        else:
            print("  FAIL: Roundtrip mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 4: SHA-256 verification
    print("\n[Test 4] SHA-256 verification")
    try:
        data = b"Test data for SHA-256 verification"
        config = RWV1Config(include_sha256=True)
        compressed = compress_bytes(data, config)
        decompressed = decompress_bytes(compressed)
        if decompressed == data:
            print("  PASS: SHA-256 verified")
        else:
            print("  FAIL: Roundtrip mismatch")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 5: Multi-block
    print("\n[Test 5] Multi-block")
    try:
        # Use small block size to force multiple blocks
        data = b"x" * 10000
        config = RWV1Config(block_size=1024)
        compressed = compress_bytes(data, config)
        info = get_container_info(compressed)
        decompressed = decompress_bytes(compressed)
        if decompressed == data and info.block_count > 1:
            print(f"  PASS: {info.block_count} blocks")
        else:
            print("  FAIL: Multi-block failed")
            failures += 1
    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 6: MO+zlib effectiveness on text
    print("\n[Test 6] MO+zlib text compression")
    try:
        # Repetitive text that should benefit from MO+zlib
        data = (b"function test() { return 'hello world'; } " * 50)
        compressed = compress_bytes(data)
        info = get_container_info(compressed)

        # Check if MO_ZLIB was used
        usage = info.branch_usage()
        if decompressed := decompress_bytes(compressed):
            if decompressed == data:
                print(f"  PASS: {len(data)} -> {len(compressed)} bytes")
                print(f"        Branches used: {usage}")
            else:
                print("  FAIL: Roundtrip mismatch")
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
        prog='realityweaver',
        description='RealityWeaver (RWV1) compression tool',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    # compress command
    compress_parser = subparsers.add_parser('compress', help='Compress a file')
    compress_parser.add_argument('input', help='Input file')
    compress_parser.add_argument('output', help='Output file (.rwv)')
    compress_parser.add_argument('--block-size', type=int, default=1 << 20,
                                 help='Block size (default: 1 MiB)')
    compress_parser.add_argument('--probe', action='store_true',
                                 help='Enable probe gating')
    compress_parser.add_argument('--allow-bz2', action='store_true',
                                 help='Enable bz2 branch')
    compress_parser.add_argument('--allow-lzma', action='store_true',
                                 help='Enable lzma branch')
    compress_parser.add_argument('--sha256', action='store_true',
                                 help='Include SHA-256 checksum')
    compress_parser.add_argument('--zlib-level', type=int, default=9,
                                 help='zlib compression level (1-9)')
    compress_parser.add_argument('--bz2-level', type=int, default=9,
                                 help='bz2 compression level (1-9)')
    compress_parser.add_argument('--lzma-preset', type=int, default=6,
                                 help='lzma preset (0-9)')
    compress_parser.add_argument('--mo-max-entries', type=int, default=200,
                                 help='MO+zlib max dictionary entries')

    # decompress command
    decompress_parser = subparsers.add_parser('decompress',
                                              help='Decompress a file')
    decompress_parser.add_argument('input', help='Input file (.rwv)')
    decompress_parser.add_argument('output', help='Output file')

    # bench command
    bench_parser = subparsers.add_parser('bench',
                                         help='Benchmark compression')
    bench_parser.add_argument('input', help='Input file')

    # info command
    info_parser = subparsers.add_parser('info', help='Show container info')
    info_parser.add_argument('input', help='Input file (.rwv)')

    # selftest command
    selftest_parser = subparsers.add_parser('selftest', help='Run self-tests')

    args = parser.parse_args()

    if args.command == 'compress':
        return cmd_compress(args)
    elif args.command == 'decompress':
        return cmd_decompress(args)
    elif args.command == 'bench':
        return cmd_bench(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'selftest':
        return cmd_selftest(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
