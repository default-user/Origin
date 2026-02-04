#!/usr/bin/env python3
# ProofWeave Kernel CLI (pwk)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
PWK - ProofWeave Kernel CLI

The TRUSTED proof checker for PWOF v1.

Usage:
    pwk check <path_to_pwof.json>  - Check proof, exit 0 PASS, exit 1 FAIL
    pwk hash <path_to_pwof.json>   - Output canonical hash
    pwk info <path_to_pwof.json>   - Display proof info
    pwk selftest                   - Run self-tests
"""

import argparse
import json
import sys

from .kernel import pwk_check, PWKResult
from .canonicalize import canonicalize_pwof, compute_hash, parse_pwof
from .types import ProofObject, PWOF_VERSION, SUPPORTED_RULESETS


def cmd_check(args: argparse.Namespace) -> int:
    """Check a proof file."""
    try:
        with open(args.path, 'rb') as f:
            data = f.read()

        pwof = parse_pwof(data)
        result = pwk_check(pwof)

        if result.passed:
            print(f"PASS: {result.message}")
            print(f"  Nodes: {result.node_count}")
            print(f"  Rules: {', '.join(set(result.rules_used))}")
            return 0
        else:
            print(f"FAIL: {result.message}")
            return 1

    except FileNotFoundError:
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_hash(args: argparse.Namespace) -> int:
    """Compute canonical hash of a proof file."""
    try:
        with open(args.path, 'rb') as f:
            data = f.read()

        pwof = parse_pwof(data)
        hash_value = compute_hash(pwof, algorithm=args.algorithm)

        print(hash_value)
        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_info(args: argparse.Namespace) -> int:
    """Display information about a proof file."""
    try:
        with open(args.path, 'rb') as f:
            data = f.read()

        pwof = parse_pwof(data)
        pobj = ProofObject.from_dict(pwof)

        print(f"PWOF File: {args.path}")
        print(f"  Version: {pobj.pwof_version}")
        print(f"  Ruleset: {pobj.ruleset_id}")
        print(f"  Assumptions: {len(pobj.assumptions)}")
        print(f"  Proof nodes: {len(pobj.nodes)}")
        print(f"  Conclusion: {pobj.conclusion_id}")

        if pobj.who:
            print(f"  Who: {pobj.who}")
        if pobj.why:
            print(f"  Why: {pobj.why}")

        # Compute hash
        hash_value = compute_hash(pwof)
        print(f"  SHA-256: {hash_value[:16]}...")

        return 0

    except FileNotFoundError:
        print(f"Error: File not found: {args.path}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_selftest(args: argparse.Namespace) -> int:
    """Run self-tests."""
    print("Running ProofWeave Kernel self-tests...")
    failures = 0

    # Test 1: Simple modus ponens proof
    print("\n[Test 1] Modus Ponens (IMP_ELIM)")
    try:
        # Prove B from assumptions A and A→B
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"atom": {"pred": "A", "args": []}},
                    {"imp": [
                        {"atom": {"pred": "A", "args": []}},
                        {"atom": {"pred": "B", "args": []}}
                    ]}
                ]
            },
            "goal": {"formula": {"atom": {"pred": "B", "args": []}}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"atom": {"pred": "A", "args": []}}
                    },
                    {
                        "id": "n2",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"imp": [
                            {"atom": {"pred": "A", "args": []}},
                            {"atom": {"pred": "B", "args": []}}
                        ]}
                    },
                    {
                        "id": "n3",
                        "rule": "IMP_ELIM",
                        "premises": ["n1", "n2"],
                        "formula": {"atom": {"pred": "B", "args": []}}
                    }
                ],
                "conclusion": "n3"
            }
        }

        result = pwk_check(pwof)
        if result.passed:
            print("  PASS: Modus ponens verified")
        else:
            print(f"  FAIL: {result.message}")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 2: Conjunction introduction
    print("\n[Test 2] Conjunction Introduction (AND_INTRO)")
    try:
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"atom": {"pred": "P", "args": []}},
                    {"atom": {"pred": "Q", "args": []}}
                ]
            },
            "goal": {"formula": {"and": [
                {"atom": {"pred": "P", "args": []}},
                {"atom": {"pred": "Q", "args": []}}
            ]}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"atom": {"pred": "P", "args": []}}
                    },
                    {
                        "id": "n2",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"atom": {"pred": "Q", "args": []}}
                    },
                    {
                        "id": "n3",
                        "rule": "AND_INTRO",
                        "premises": ["n1", "n2"],
                        "formula": {"and": [
                            {"atom": {"pred": "P", "args": []}},
                            {"atom": {"pred": "Q", "args": []}}
                        ]}
                    }
                ],
                "conclusion": "n3"
            }
        }

        result = pwk_check(pwof)
        if result.passed:
            print("  PASS: Conjunction intro verified")
        else:
            print(f"  FAIL: {result.message}")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 3: Equality reflexivity
    print("\n[Test 3] Equality Reflexivity (EQ_REFL)")
    try:
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {"eq": {
                "left": {"var": "x"},
                "right": {"var": "x"}
            }}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "EQ_REFL",
                        "premises": [],
                        "formula": {"eq": {
                            "left": {"var": "x"},
                            "right": {"var": "x"}
                        }}
                    }
                ],
                "conclusion": "n1"
            }
        }

        result = pwk_check(pwof)
        if result.passed:
            print("  PASS: Equality reflexivity verified")
        else:
            print(f"  FAIL: {result.message}")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 4: Invalid proof (should FAIL)
    print("\n[Test 4] Invalid proof detection")
    try:
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "ASSUME",  # No such assumption!
                        "premises": [],
                        "formula": {"atom": {"pred": "P", "args": []}}
                    }
                ],
                "conclusion": "n1"
            }
        }

        result = pwk_check(pwof)
        if not result.passed:
            print("  PASS: Invalid proof correctly rejected")
        else:
            print("  FAIL: Invalid proof incorrectly accepted")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 5: Unsupported version
    print("\n[Test 5] Unsupported version rejection")
    try:
        pwof = {
            "pwof_version": "99",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {}},
            "proof": {"nodes": [], "conclusion": ""}
        }

        result = pwk_check(pwof)
        if not result.passed and "version" in result.message.lower():
            print("  PASS: Unsupported version rejected")
        else:
            print("  FAIL: Should have rejected unsupported version")
            failures += 1

    except Exception as e:
        print(f"  FAIL: {e}")
        failures += 1

    # Test 6: Canonicalization
    print("\n[Test 6] Canonicalization determinism")
    try:
        pwof1 = {"b": 1, "a": 2, "c": {"z": 3, "y": 4}}
        pwof2 = {"a": 2, "c": {"y": 4, "z": 3}, "b": 1}

        c1 = canonicalize_pwof(pwof1)
        c2 = canonicalize_pwof(pwof2)

        if c1 == c2:
            print("  PASS: Canonicalization is deterministic")
        else:
            print("  FAIL: Canonicalization not deterministic")
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
        prog='pwk',
        description='ProofWeave Kernel (PWK) - TRUSTED proof checker',
    )
    parser.add_argument('--version', action='version',
                        version=f'PWK v1.0.0 (PWOF {PWOF_VERSION})')

    subparsers = parser.add_subparsers(dest='command', required=True)

    # check command
    check_parser = subparsers.add_parser('check',
                                         help='Check proof (exit 0=PASS, 1=FAIL)')
    check_parser.add_argument('path', help='Path to PWOF JSON file')

    # hash command
    hash_parser = subparsers.add_parser('hash',
                                        help='Compute canonical hash')
    hash_parser.add_argument('path', help='Path to PWOF JSON file')
    hash_parser.add_argument('--algorithm', choices=['sha256', 'blake3'],
                             default='sha256',
                             help='Hash algorithm (default: sha256)')

    # info command
    info_parser = subparsers.add_parser('info', help='Display proof info')
    info_parser.add_argument('path', help='Path to PWOF JSON file')

    # selftest command
    selftest_parser = subparsers.add_parser('selftest', help='Run self-tests')

    args = parser.parse_args()

    if args.command == 'check':
        return cmd_check(args)
    elif args.command == 'hash':
        return cmd_hash(args)
    elif args.command == 'info':
        return cmd_info(args)
    elif args.command == 'selftest':
        return cmd_selftest(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
