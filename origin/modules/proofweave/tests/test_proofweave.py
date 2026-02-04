#!/usr/bin/env python3
# ProofWeave Test Suite
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Test suite for ProofWeave kernel.
"""

import unittest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from kernel import pwk_check, PWKResult
from canonicalize import canonicalize_pwof, compute_hash
from types import Formula, Term, ProofNode, ProofObject, RuleID


class TestFormulas(unittest.TestCase):
    """Test formula construction."""

    def test_atom(self):
        """Atom formula construction."""
        f = Formula.atom("P", [Term.var("x")])
        self.assertEqual(f.formula_type, "atom")
        self.assertEqual(f.data["atom"]["pred"], "P")

    def test_equality(self):
        """Equality formula construction."""
        t1 = Term.var("x")
        t2 = Term.var("y")
        f = Formula.eq(t1, t2)
        self.assertEqual(f.formula_type, "eq")

    def test_connectives(self):
        """Logical connective construction."""
        a = Formula.atom("A", [])
        b = Formula.atom("B", [])

        and_f = Formula.and_(a, b)
        self.assertEqual(and_f.formula_type, "and")

        or_f = Formula.or_(a, b)
        self.assertEqual(or_f.formula_type, "or")

        imp_f = Formula.imp(a, b)
        self.assertEqual(imp_f.formula_type, "imp")

        not_f = Formula.not_(a)
        self.assertEqual(not_f.formula_type, "not")

    def test_false_atom(self):
        """False atom (bottom) construction."""
        f = Formula.false()
        self.assertEqual(f.data["atom"]["pred"], "False")
        self.assertEqual(f.data["atom"]["args"], [])


class TestCanonicalization(unittest.TestCase):
    """Test canonicalization."""

    def test_sorted_keys(self):
        """Object keys should be sorted."""
        obj = {"z": 1, "a": 2, "m": 3}
        canonical = canonicalize_pwof(obj)
        self.assertEqual(canonical, b'{"a":2,"m":3,"z":1}')

    def test_nested_sorted(self):
        """Nested object keys should be sorted."""
        obj = {"b": {"z": 1, "a": 2}, "a": 1}
        canonical = canonicalize_pwof(obj)
        self.assertEqual(canonical, b'{"a":1,"b":{"a":2,"z":1}}')

    def test_deterministic(self):
        """Same input should produce same output."""
        obj1 = {"b": 1, "a": 2}
        obj2 = {"a": 2, "b": 1}
        self.assertEqual(canonicalize_pwof(obj1), canonicalize_pwof(obj2))

    def test_hash_deterministic(self):
        """Hash should be deterministic."""
        obj = {"test": "data", "nested": {"a": 1, "b": 2}}
        h1 = compute_hash(obj)
        h2 = compute_hash(obj)
        self.assertEqual(h1, h2)


class TestKernelBasic(unittest.TestCase):
    """Test basic kernel operations."""

    def test_unsupported_version(self):
        """Unsupported version should fail."""
        pwof = {
            "pwof_version": "99",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {}},
            "proof": {"nodes": [], "conclusion": ""}
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)
        self.assertIn("version", result.message.lower())

    def test_unsupported_ruleset(self):
        """Unsupported ruleset should fail."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "UNKNOWN_RULESET",
            "context": {"assumptions": []},
            "goal": {"formula": {}},
            "proof": {"nodes": [], "conclusion": ""}
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)
        self.assertIn("ruleset", result.message.lower())

    def test_empty_proof(self):
        """Empty proof should fail."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
            "proof": {"nodes": [], "conclusion": ""}
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)


class TestAssumeRule(unittest.TestCase):
    """Test ASSUME rule."""

    def test_valid_assume(self):
        """Valid assumption should pass."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"atom": {"pred": "P", "args": []}}
                ]
            },
            "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"atom": {"pred": "P", "args": []}}
                    }
                ],
                "conclusion": "n1"
            }
        }
        result = pwk_check(pwof)
        self.assertTrue(result.passed)

    def test_invalid_assume(self):
        """Assumption not in context should fail."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
            "proof": {
                "nodes": [
                    {
                        "id": "n1",
                        "rule": "ASSUME",
                        "premises": [],
                        "formula": {"atom": {"pred": "P", "args": []}}
                    }
                ],
                "conclusion": "n1"
            }
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)


class TestImpElim(unittest.TestCase):
    """Test IMP_ELIM (modus ponens) rule."""

    def test_valid_imp_elim(self):
        """Valid modus ponens should pass."""
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
        self.assertTrue(result.passed)


class TestAndRules(unittest.TestCase):
    """Test conjunction rules."""

    def test_and_intro(self):
        """AND_INTRO should work."""
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
                    {"id": "n1", "rule": "ASSUME", "premises": [],
                     "formula": {"atom": {"pred": "P", "args": []}}},
                    {"id": "n2", "rule": "ASSUME", "premises": [],
                     "formula": {"atom": {"pred": "Q", "args": []}}},
                    {"id": "n3", "rule": "AND_INTRO", "premises": ["n1", "n2"],
                     "formula": {"and": [
                         {"atom": {"pred": "P", "args": []}},
                         {"atom": {"pred": "Q", "args": []}}
                     ]}}
                ],
                "conclusion": "n3"
            }
        }
        result = pwk_check(pwof)
        self.assertTrue(result.passed)

    def test_and_elim_l(self):
        """AND_ELIM_L should work."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"and": [
                        {"atom": {"pred": "P", "args": []}},
                        {"atom": {"pred": "Q", "args": []}}
                    ]}
                ]
            },
            "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
            "proof": {
                "nodes": [
                    {"id": "n1", "rule": "ASSUME", "premises": [],
                     "formula": {"and": [
                         {"atom": {"pred": "P", "args": []}},
                         {"atom": {"pred": "Q", "args": []}}
                     ]}},
                    {"id": "n2", "rule": "AND_ELIM_L", "premises": ["n1"],
                     "formula": {"atom": {"pred": "P", "args": []}}}
                ],
                "conclusion": "n2"
            }
        }
        result = pwk_check(pwof)
        self.assertTrue(result.passed)


class TestEqualityRules(unittest.TestCase):
    """Test equality rules."""

    def test_eq_refl(self):
        """EQ_REFL should work."""
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
                    {"id": "n1", "rule": "EQ_REFL", "premises": [],
                     "formula": {"eq": {
                         "left": {"var": "x"},
                         "right": {"var": "x"}
                     }}}
                ],
                "conclusion": "n1"
            }
        }
        result = pwk_check(pwof)
        self.assertTrue(result.passed)

    def test_eq_refl_invalid(self):
        """EQ_REFL with different terms should fail."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {"assumptions": []},
            "goal": {"formula": {"eq": {
                "left": {"var": "x"},
                "right": {"var": "y"}
            }}},
            "proof": {
                "nodes": [
                    {"id": "n1", "rule": "EQ_REFL", "premises": [],
                     "formula": {"eq": {
                         "left": {"var": "x"},
                         "right": {"var": "y"}
                     }}}
                ],
                "conclusion": "n1"
            }
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)

    def test_eq_symm(self):
        """EQ_SYMM should work."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"eq": {"left": {"var": "x"}, "right": {"var": "y"}}}
                ]
            },
            "goal": {"formula": {"eq": {
                "left": {"var": "y"},
                "right": {"var": "x"}
            }}},
            "proof": {
                "nodes": [
                    {"id": "n1", "rule": "ASSUME", "premises": [],
                     "formula": {"eq": {
                         "left": {"var": "x"},
                         "right": {"var": "y"}
                     }}},
                    {"id": "n2", "rule": "EQ_SYMM", "premises": ["n1"],
                     "formula": {"eq": {
                         "left": {"var": "y"},
                         "right": {"var": "x"}
                     }}}
                ],
                "conclusion": "n2"
            }
        }
        result = pwk_check(pwof)
        self.assertTrue(result.passed)


class TestGoalMismatch(unittest.TestCase):
    """Test goal matching."""

    def test_goal_mismatch(self):
        """Conclusion not matching goal should fail."""
        pwof = {
            "pwof_version": "1",
            "ruleset_id": "PWK_ND_PROP_EQ_v1",
            "context": {
                "assumptions": [
                    {"atom": {"pred": "A", "args": []}}
                ]
            },
            "goal": {"formula": {"atom": {"pred": "B", "args": []}}},  # Different!
            "proof": {
                "nodes": [
                    {"id": "n1", "rule": "ASSUME", "premises": [],
                     "formula": {"atom": {"pred": "A", "args": []}}}
                ],
                "conclusion": "n1"
            }
        }
        result = pwk_check(pwof)
        self.assertFalse(result.passed)
        self.assertIn("goal", result.message.lower())


if __name__ == '__main__':
    unittest.main()
