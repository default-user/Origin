# ProofWeave Types
# Attribution: Ande → Kai
# License: WCL-1.0

"""
Core types for PWOF v1 proof objects.

Formula encoding:
  Atoms:      {"atom":{"pred":"P","args":[<term>, ...]}}
  Equality:   {"eq":{"left":<term>,"right":<term>}}
  Connectives:
    {"and":[f1,f2]}
    {"or":[f1,f2]}
    {"imp":[f1,f2]}
    {"not":f}

Terms:
  {"var":"x"}
  {"fun":{"name":"f","args":[t1,...]}}

Quantifiers (reserved for v1.1+):
  {"all":{"var":"x","body":f}}
  {"ex":{"var":"x","body":f}}
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Any, Optional, Union


# PWOF Constants
PWOF_VERSION = "1"
SUPPORTED_RULESETS = ["PWK_ND_PROP_EQ_v1"]


class RuleID(str, Enum):
    """
    PWK_ND_PROP_EQ_v1 Ruleset.

    Structural:
    - ASSUME: Must match a context assumption
    - REITERATE: Repeat a previously derived formula

    Propositional ND:
    - IMP_ELIM: Modus Ponens (A, A→B ⊢ B)
    - AND_INTRO: Conjunction intro (A, B ⊢ A∧B)
    - AND_ELIM_L: Left conjunction elim (A∧B ⊢ A)
    - AND_ELIM_R: Right conjunction elim (A∧B ⊢ B)
    - OR_INTRO_L: Left disjunction intro (A ⊢ A∨B)
    - OR_INTRO_R: Right disjunction intro (B ⊢ A∨B)
    - NOT_ELIM: Negation elimination (A, ¬A ⊢ ⊥)

    Equality:
    - EQ_REFL: Reflexivity (⊢ t=t)
    - EQ_SYMM: Symmetry (t1=t2 ⊢ t2=t1)
    - EQ_TRANS: Transitivity (t1=t2, t2=t3 ⊢ t1=t3)
    - EQ_SUBST_PRED: Substitution in unary predicate (t1=t2, P(t1) ⊢ P(t2))
    """
    # Structural
    ASSUME = "ASSUME"
    REITERATE = "REITERATE"

    # Propositional
    IMP_ELIM = "IMP_ELIM"
    AND_INTRO = "AND_INTRO"
    AND_ELIM_L = "AND_ELIM_L"
    AND_ELIM_R = "AND_ELIM_R"
    OR_INTRO_L = "OR_INTRO_L"
    OR_INTRO_R = "OR_INTRO_R"
    NOT_ELIM = "NOT_ELIM"

    # Equality
    EQ_REFL = "EQ_REFL"
    EQ_SYMM = "EQ_SYMM"
    EQ_TRANS = "EQ_TRANS"
    EQ_SUBST_PRED = "EQ_SUBST_PRED"


@dataclass
class Term:
    """
    A term in the logic.

    Either a variable {"var": "x"} or a function {"fun": {"name": "f", "args": [...]}}
    """
    data: Dict[str, Any]

    @classmethod
    def var(cls, name: str) -> 'Term':
        return cls({"var": name})

    @classmethod
    def fun(cls, name: str, args: List['Term']) -> 'Term':
        return cls({"fun": {"name": name, "args": [t.data for t in args]}})

    @property
    def is_var(self) -> bool:
        return "var" in self.data

    @property
    def is_fun(self) -> bool:
        return "fun" in self.data

    def to_dict(self) -> Dict[str, Any]:
        return self.data

    def __eq__(self, other) -> bool:
        if not isinstance(other, Term):
            return False
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(str(self.data))


@dataclass
class Formula:
    """
    A formula in the logic.

    Types:
    - Atom: {"atom": {"pred": "P", "args": [...]}}
    - Equality: {"eq": {"left": term, "right": term}}
    - And: {"and": [f1, f2]}
    - Or: {"or": [f1, f2]}
    - Imp: {"imp": [f1, f2]}
    - Not: {"not": f}
    """
    data: Dict[str, Any]

    @classmethod
    def atom(cls, pred: str, args: List[Term]) -> 'Formula':
        return cls({"atom": {"pred": pred, "args": [t.data for t in args]}})

    @classmethod
    def eq(cls, left: Term, right: Term) -> 'Formula':
        return cls({"eq": {"left": left.data, "right": right.data}})

    @classmethod
    def and_(cls, f1: 'Formula', f2: 'Formula') -> 'Formula':
        return cls({"and": [f1.data, f2.data]})

    @classmethod
    def or_(cls, f1: 'Formula', f2: 'Formula') -> 'Formula':
        return cls({"or": [f1.data, f2.data]})

    @classmethod
    def imp(cls, f1: 'Formula', f2: 'Formula') -> 'Formula':
        return cls({"imp": [f1.data, f2.data]})

    @classmethod
    def not_(cls, f: 'Formula') -> 'Formula':
        return cls({"not": f.data})

    @classmethod
    def false(cls) -> 'Formula':
        """The False atom (⊥)."""
        return cls({"atom": {"pred": "False", "args": []}})

    @property
    def formula_type(self) -> str:
        """Return the type of this formula."""
        for key in ["atom", "eq", "and", "or", "imp", "not", "all", "ex"]:
            if key in self.data:
                return key
        return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        return self.data

    def __eq__(self, other) -> bool:
        if not isinstance(other, Formula):
            return False
        return self.data == other.data

    def __hash__(self) -> int:
        return hash(str(self.data))


@dataclass
class ProofNode:
    """
    A single step in a proof.

    Attributes:
        node_id: Unique identifier within the proof
        rule: The rule applied (from RuleID)
        premises: List of node_ids this step depends on
        formula: The formula derived by this step
        justification: Optional additional data for the rule
    """
    node_id: str
    rule: str
    premises: List[str]
    formula: Dict[str, Any]
    justification: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "id": self.node_id,
            "rule": self.rule,
            "premises": self.premises,
            "formula": self.formula,
        }
        if self.justification:
            d["justification"] = self.justification
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ProofNode':
        return cls(
            node_id=d["id"],
            rule=d["rule"],
            premises=d.get("premises", []),
            formula=d["formula"],
            justification=d.get("justification"),
        )


@dataclass
class ProofObject:
    """
    PWOF v1 Proof Object.

    Top-level schema:
    {
      "pwof_version": "1",
      "ruleset_id": "PWK_ND_PROP_EQ_v1",
      "context": { "assumptions": [...] },
      "goal": {"formula": ...},
      "proof": { "nodes": [...], "conclusion": "nLast" },
      "who": {...},  # optional
      "why": {...}   # optional
    }
    """
    pwof_version: str
    ruleset_id: str
    context: Dict[str, Any]
    goal: Dict[str, Any]
    proof: Dict[str, Any]
    who: Optional[Dict[str, Any]] = None
    why: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "pwof_version": self.pwof_version,
            "ruleset_id": self.ruleset_id,
            "context": self.context,
            "goal": self.goal,
            "proof": self.proof,
        }
        if self.who:
            d["who"] = self.who
        if self.why:
            d["why"] = self.why
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ProofObject':
        return cls(
            pwof_version=d["pwof_version"],
            ruleset_id=d["ruleset_id"],
            context=d["context"],
            goal=d["goal"],
            proof=d["proof"],
            who=d.get("who"),
            why=d.get("why"),
        )

    @property
    def nodes(self) -> List[ProofNode]:
        """Return proof nodes as ProofNode objects."""
        return [ProofNode.from_dict(n) for n in self.proof.get("nodes", [])]

    @property
    def conclusion_id(self) -> str:
        """Return the conclusion node ID."""
        return self.proof.get("conclusion", "")

    @property
    def assumptions(self) -> List[Dict[str, Any]]:
        """Return context assumptions."""
        return self.context.get("assumptions", [])

    @property
    def goal_formula(self) -> Dict[str, Any]:
        """Return the goal formula."""
        return self.goal.get("formula", {})
