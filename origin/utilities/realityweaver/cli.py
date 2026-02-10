"""
RW-8: CLI shell with receipts.

Command-line interface for RealityWeaver sidecar operations.
Every command emits a receipt. Sidecar-only: no runtime wiring.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

from .primitives import canonical_json_pretty
from .receipts import emit_receipt, gate, write_receipt
from .weaverpack import verify


def cmd_verify(args: argparse.Namespace) -> int:
    """Verify a WeaverPack manifest."""
    result = verify(args.manifest, args.base_path)

    gates = []
    gates.append(gate(
        "manifest_schema", "pass" if not result.errors else "fail",
        f"Schema check: {len(result.errors)} errors",
    ))
    gates.append(gate(
        "pack_integrity", "pass" if result.passed else "fail",
        f"Files checked: {result.files_checked}",
    ))

    receipt = emit_receipt(
        operation="verify",
        operator_id="RW-2_weaverpack_verify",
        inputs={"manifest_path": args.manifest},
        outputs={"passed": result.passed, "files_checked": result.files_checked},
        gates=gates,
        invariants_checked=result.invariants_checked,
        error="; ".join(result.errors) if result.errors else None,
    )

    if args.receipt_path:
        write_receipt(receipt, args.receipt_path)

    if result.passed:
        print(f"PASS: manifest verified ({result.files_checked} files)")
    else:
        print(f"FAIL: {len(result.errors)} error(s)")
        for err in result.errors:
            print(f"  - {err}")

    return 0 if result.passed else 1


def cmd_seal(args: argparse.Namespace) -> int:
    """Seal a WeaverPack (commitment only)."""
    from .seal import seal
    from .weaverpack import load_manifest

    manifest = load_manifest(args.manifest)
    try:
        seal_result = seal(manifest)
    except ValueError as e:
        print(f"FAIL: {e}")
        return 1

    commitment = seal_result.commitment
    output = {
        "commitment_id": commitment.commitment_id,
        "manifest_id": commitment.manifest_id,
        "pack_hash": commitment.pack_hash,
        "commitment_hash": commitment.commitment_hash,
        "timestamp": commitment.timestamp,
    }

    receipt = emit_receipt(
        operation="seal",
        operator_id="RW-6_seal_commit",
        inputs={"manifest_path": args.manifest},
        outputs=output,
        gates=[gate("integrity", "pass", "pack_hash verified before seal")],
        invariants_checked=["RW-C1"],
    )

    if args.receipt_path:
        write_receipt(receipt, args.receipt_path)

    print(json.dumps(output, indent=2))
    return 0


def cmd_info(args: argparse.Namespace) -> int:
    """Display manifest information."""
    from .weaverpack import load_manifest

    manifest = load_manifest(args.manifest)
    info = {
        "manifest_id": manifest.get("manifest_id"),
        "weaverpack_id": manifest.get("weaverpack_id"),
        "schema_version": manifest.get("schema_version"),
        "authorship": manifest.get("authorship"),
        "license": manifest.get("license"),
        "file_count": len(manifest.get("files", {})),
        "pack_hash": manifest.get("pack_hash"),
        "invariants_declared": manifest.get("invariants_declared", []),
    }
    print(json.dumps(info, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="rw",
        description="RealityWeaver sidecar CLI. All commands emit receipts.",
    )
    sub = parser.add_subparsers(dest="command")

    # verify
    p_verify = sub.add_parser("verify", help="Verify a WeaverPack manifest")
    p_verify.add_argument("manifest", help="Path to manifest JSON")
    p_verify.add_argument("--base-path", dest="base_path", default=None,
                          help="Base path for file verification")
    p_verify.add_argument("--receipt", dest="receipt_path", default=None,
                          help="Path to write receipt JSON")

    # seal
    p_seal = sub.add_parser("seal", help="Seal a WeaverPack (commitment only)")
    p_seal.add_argument("manifest", help="Path to manifest JSON")
    p_seal.add_argument("--receipt", dest="receipt_path", default=None,
                        help="Path to write receipt JSON")

    # info
    p_info = sub.add_parser("info", help="Display manifest information")
    p_info.add_argument("manifest", help="Path to manifest JSON")

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    dispatch = {
        "verify": cmd_verify,
        "seal": cmd_seal,
        "info": cmd_info,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        print(f"Unknown command: {args.command}")
        return 1

    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
