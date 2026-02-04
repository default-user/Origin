# ProofWeave Kernel (PWK) - TRUSTED CHECKER
# Attribution: Ande → Kai
# License: WCL-1.0

"""
PWK Kernel: The TRUSTED proof checker for PWOF v1.

TRUST BOUNDARY:
  This kernel is the ONLY trusted component.
  Everything else (engines, tactics, LLM suggestions) is UNTRUSTED.

Behavior:
- Fail-closed on unsupported pwof_version
- Fail-closed on unsupported ruleset_id
- Proof passes ONLY if:
  1. Conclusion node exists
  2. All premises are resolvable
  3. Each rule application is valid
  4. Final formula equals goal.formula exactly

Supported ruleset: PWK_ND_PROP_EQ_v1
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .types import (
    ProofObject,
    ProofNode,
    RuleID,
    PWOF_VERSION,
    SUPPORTED_RULESETS,
)


class PWKError(Exception):
    """Error from the proof kernel."""
    pass


@dataclass
class PWKResult:
    """Result of proof checking."""
    passed: bool
    message: str
    node_count: int = 0
    rules_used: List[str] = None

    def __post_init__(self):
        if self.rules_used is None:
            self.rules_used = []


def _formulas_equal(f1: Dict[str, Any], f2: Dict[str, Any]) -> bool:
    """Deep equality check for formulas."""
    return f1 == f2


def _terms_equal(t1: Dict[str, Any], t2: Dict[str, Any]) -> bool:
    """Deep equality check for terms."""
    return t1 == t2


def _is_false_atom(f: Dict[str, Any]) -> bool:
    """Check if formula is the False atom (⊥)."""
    if "atom" in f:
        atom = f["atom"]
        return atom.get("pred") == "False" and atom.get("args", []) == []
    return False


def _check_assume(
    node: ProofNode,
    assumptions: List[Dict[str, Any]],
) -> bool:
    """
    ASSUME rule: formula must be in context assumptions.
    """
    for assumption in assumptions:
        if _formulas_equal(node.formula, assumption):
            return True
    return False


def _check_reiterate(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    REITERATE rule: repeat a previously derived formula.
    """
    if len(node.premises) != 1:
        return False
    premise_id = node.premises[0]
    if premise_id not in derived:
        return False
    return _formulas_equal(node.formula, derived[premise_id])


def _check_imp_elim(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    IMP_ELIM (Modus Ponens): A, A→B ⊢ B

    Premises: [p1, p2] where p2 has {"imp": [A, B]} and p1 has A
    Conclusion: B
    """
    if len(node.premises) != 2:
        return False

    p1_id, p2_id = node.premises
    if p1_id not in derived or p2_id not in derived:
        return False

    p1_formula = derived[p1_id]
    p2_formula = derived[p2_id]

    # p2 should be an implication
    if "imp" not in p2_formula:
        # Try swapping
        p1_formula, p2_formula = p2_formula, p1_formula
        if "imp" not in p2_formula:
            return False

    antecedent, consequent = p2_formula["imp"]

    # p1 should match the antecedent
    if not _formulas_equal(p1_formula, antecedent):
        return False

    # Conclusion should be the consequent
    return _formulas_equal(node.formula, consequent)


def _check_and_intro(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    AND_INTRO: A, B ⊢ A∧B
    """
    if len(node.premises) != 2:
        return False

    p1_id, p2_id = node.premises
    if p1_id not in derived or p2_id not in derived:
        return False

    if "and" not in node.formula:
        return False

    f1, f2 = node.formula["and"]
    return (
        _formulas_equal(derived[p1_id], f1) and
        _formulas_equal(derived[p2_id], f2)
    )


def _check_and_elim_l(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    AND_ELIM_L: A∧B ⊢ A
    """
    if len(node.premises) != 1:
        return False

    premise_id = node.premises[0]
    if premise_id not in derived:
        return False

    premise = derived[premise_id]
    if "and" not in premise:
        return False

    left, _ = premise["and"]
    return _formulas_equal(node.formula, left)


def _check_and_elim_r(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    AND_ELIM_R: A∧B ⊢ B
    """
    if len(node.premises) != 1:
        return False

    premise_id = node.premises[0]
    if premise_id not in derived:
        return False

    premise = derived[premise_id]
    if "and" not in premise:
        return False

    _, right = premise["and"]
    return _formulas_equal(node.formula, right)


def _check_or_intro_l(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    OR_INTRO_L: A ⊢ A∨B
    """
    if len(node.premises) != 1:
        return False

    premise_id = node.premises[0]
    if premise_id not in derived:
        return False

    if "or" not in node.formula:
        return False

    left, _ = node.formula["or"]
    return _formulas_equal(derived[premise_id], left)


def _check_or_intro_r(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    OR_INTRO_R: B ⊢ A∨B
    """
    if len(node.premises) != 1:
        return False

    premise_id = node.premises[0]
    if premise_id not in derived:
        return False

    if "or" not in node.formula:
        return False

    _, right = node.formula["or"]
    return _formulas_equal(derived[premise_id], right)


def _check_not_elim(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    NOT_ELIM: A, ¬A ⊢ ⊥

    Conclusion must be False atom.
    """
    if len(node.premises) != 2:
        return False

    if not _is_false_atom(node.formula):
        return False

    p1_id, p2_id = node.premises
    if p1_id not in derived or p2_id not in derived:
        return False

    f1 = derived[p1_id]
    f2 = derived[p2_id]

    # One should be negation of the other
    if "not" in f2:
        f1, f2 = f2, f1

    if "not" not in f1:
        return False

    return _formulas_equal(f1["not"], f2)


def _check_eq_refl(node: ProofNode) -> bool:
    """
    EQ_REFL: ⊢ t=t

    No premises needed, conclusion is t=t.
    """
    if len(node.premises) != 0:
        return False

    if "eq" not in node.formula:
        return False

    eq = node.formula["eq"]
    return _terms_equal(eq["left"], eq["right"])


def _check_eq_symm(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    EQ_SYMM: t1=t2 ⊢ t2=t1
    """
    if len(node.premises) != 1:
        return False

    premise_id = node.premises[0]
    if premise_id not in derived:
        return False

    premise = derived[premise_id]
    if "eq" not in premise or "eq" not in node.formula:
        return False

    p_eq = premise["eq"]
    c_eq = node.formula["eq"]

    return (
        _terms_equal(p_eq["left"], c_eq["right"]) and
        _terms_equal(p_eq["right"], c_eq["left"])
    )


def _check_eq_trans(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    EQ_TRANS: t1=t2, t2=t3 ⊢ t1=t3
    """
    if len(node.premises) != 2:
        return False

    p1_id, p2_id = node.premises
    if p1_id not in derived or p2_id not in derived:
        return False

    f1 = derived[p1_id]
    f2 = derived[p2_id]

    if "eq" not in f1 or "eq" not in f2 or "eq" not in node.formula:
        return False

    eq1 = f1["eq"]
    eq2 = f2["eq"]
    eq_c = node.formula["eq"]

    # t1=t2, t2=t3 -> t1=t3
    # Check if eq1.right == eq2.left (the middle term)
    if _terms_equal(eq1["right"], eq2["left"]):
        return (
            _terms_equal(eq1["left"], eq_c["left"]) and
            _terms_equal(eq2["right"], eq_c["right"])
        )

    # Try the other order
    if _terms_equal(eq2["right"], eq1["left"]):
        return (
            _terms_equal(eq2["left"], eq_c["left"]) and
            _terms_equal(eq1["right"], eq_c["right"])
        )

    return False


def _check_eq_subst_pred(
    node: ProofNode,
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    EQ_SUBST_PRED: t1=t2, P(t1) ⊢ P(t2)

    Limited to unary predicates only.
    """
    if len(node.premises) != 2:
        return False

    p1_id, p2_id = node.premises
    if p1_id not in derived or p2_id not in derived:
        return False

    f1 = derived[p1_id]
    f2 = derived[p2_id]

    # Find which is the equality
    eq_formula = None
    pred_formula = None

    if "eq" in f1:
        eq_formula = f1
        pred_formula = f2
    elif "eq" in f2:
        eq_formula = f2
        pred_formula = f1
    else:
        return False

    if "atom" not in pred_formula or "atom" not in node.formula:
        return False

    pred_in = pred_formula["atom"]
    pred_out = node.formula["atom"]

    # Must be same predicate
    if pred_in["pred"] != pred_out["pred"]:
        return False

    # Must be unary
    args_in = pred_in.get("args", [])
    args_out = pred_out.get("args", [])

    if len(args_in) != 1 or len(args_out) != 1:
        return False

    eq = eq_formula["eq"]
    t1 = eq["left"]
    t2 = eq["right"]

    # P(t1) -> P(t2) where t1=t2
    if _terms_equal(args_in[0], t1) and _terms_equal(args_out[0], t2):
        return True

    # Also allow P(t2) -> P(t1) where t1=t2 (by symmetry)
    if _terms_equal(args_in[0], t2) and _terms_equal(args_out[0], t1):
        return True

    return False


def _check_rule(
    node: ProofNode,
    assumptions: List[Dict[str, Any]],
    derived: Dict[str, Dict[str, Any]],
) -> bool:
    """
    Check if a rule application is valid.
    """
    rule = node.rule

    if rule == RuleID.ASSUME.value:
        return _check_assume(node, assumptions)
    elif rule == RuleID.REITERATE.value:
        return _check_reiterate(node, derived)
    elif rule == RuleID.IMP_ELIM.value:
        return _check_imp_elim(node, derived)
    elif rule == RuleID.AND_INTRO.value:
        return _check_and_intro(node, derived)
    elif rule == RuleID.AND_ELIM_L.value:
        return _check_and_elim_l(node, derived)
    elif rule == RuleID.AND_ELIM_R.value:
        return _check_and_elim_r(node, derived)
    elif rule == RuleID.OR_INTRO_L.value:
        return _check_or_intro_l(node, derived)
    elif rule == RuleID.OR_INTRO_R.value:
        return _check_or_intro_r(node, derived)
    elif rule == RuleID.NOT_ELIM.value:
        return _check_not_elim(node, derived)
    elif rule == RuleID.EQ_REFL.value:
        return _check_eq_refl(node)
    elif rule == RuleID.EQ_SYMM.value:
        return _check_eq_symm(node, derived)
    elif rule == RuleID.EQ_TRANS.value:
        return _check_eq_trans(node, derived)
    elif rule == RuleID.EQ_SUBST_PRED.value:
        return _check_eq_subst_pred(node, derived)
    else:
        # Unknown rule - fail closed
        return False


def pwk_check(pwof: Dict[str, Any]) -> PWKResult:
    """
    Check a PWOF proof object.

    This is the TRUSTED kernel checker. It validates:
    1. PWOF version is supported
    2. Ruleset is supported
    3. Each proof step is valid according to the rules
    4. Conclusion matches goal

    Args:
        pwof: PWOF proof object dictionary

    Returns:
        PWKResult with pass/fail and message

    The kernel NEVER raises exceptions - it returns fail results
    for any error condition (fail-closed).
    """
    try:
        # Check version
        version = pwof.get("pwof_version")
        if version != PWOF_VERSION:
            return PWKResult(
                passed=False,
                message=f"Unsupported pwof_version: {version}"
            )

        # Check ruleset
        ruleset = pwof.get("ruleset_id")
        if ruleset not in SUPPORTED_RULESETS:
            return PWKResult(
                passed=False,
                message=f"Unsupported ruleset_id: {ruleset}"
            )

        # Parse proof object
        pobj = ProofObject.from_dict(pwof)

        # Get assumptions and goal
        assumptions = pobj.assumptions
        goal_formula = pobj.goal_formula

        # Get proof nodes
        nodes = pobj.nodes
        conclusion_id = pobj.conclusion_id

        if not nodes:
            return PWKResult(
                passed=False,
                message="Proof has no nodes"
            )

        if not conclusion_id:
            return PWKResult(
                passed=False,
                message="No conclusion specified"
            )

        # Track derived formulas
        derived: Dict[str, Dict[str, Any]] = {}
        rules_used = []

        # Check each node in order
        for node in nodes:
            # Verify all premises exist
            for premise_id in node.premises:
                if premise_id not in derived:
                    return PWKResult(
                        passed=False,
                        message=f"Node {node.node_id}: unresolved premise {premise_id}"
                    )

            # Check rule application
            if not _check_rule(node, assumptions, derived):
                return PWKResult(
                    passed=False,
                    message=f"Node {node.node_id}: invalid {node.rule} application"
                )

            # Record derived formula
            derived[node.node_id] = node.formula
            rules_used.append(node.rule)

        # Check conclusion exists
        if conclusion_id not in derived:
            return PWKResult(
                passed=False,
                message=f"Conclusion node {conclusion_id} not found"
            )

        # Check conclusion matches goal
        conclusion_formula = derived[conclusion_id]
        if not _formulas_equal(conclusion_formula, goal_formula):
            return PWKResult(
                passed=False,
                message="Conclusion does not match goal formula"
            )

        # Success!
        return PWKResult(
            passed=True,
            message="Proof verified",
            node_count=len(nodes),
            rules_used=rules_used,
        )

    except Exception as e:
        # Fail-closed on any error
        return PWKResult(
            passed=False,
            message=f"Kernel error: {e}"
        )
