# ProofWeave (PWOF v1 + PWK Kernel)
# Attribution: Ande → Kai
# License: WCL-1.0

"""
ProofWeave: Deterministic proof object format with trusted kernel checker.

TRUST BOUNDARY:
- PWK Kernel is TRUSTED (the only thing that validates proofs)
- Everything else is UNTRUSTED (engines, tactics, LLM suggestions, renderers)

This module implements:
- PWOF v1 canonical JSON proof format
- PWK_ND_PROP_EQ_v1 ruleset (Natural Deduction + Propositional + Equality)
- Proof verification and canonicalization
"""

from .kernel import pwk_check, PWKResult, PWKError
from .canonicalize import canonicalize_pwof, compute_hash
from .types import (
    Formula,
    Term,
    ProofNode,
    ProofObject,
    RuleID,
)

__all__ = [
    'pwk_check',
    'PWKResult',
    'PWKError',
    'canonicalize_pwof',
    'compute_hash',
    'Formula',
    'Term',
    'ProofNode',
    'ProofObject',
    'RuleID',
]

__version__ = '1.0.0'
