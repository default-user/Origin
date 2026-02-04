# PWK_ND_PROP_EQ_v1 Ruleset Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## Overview

PWK_ND_PROP_EQ_v1 is the proof ruleset for ProofWeave v1, implementing Natural Deduction with Propositional Logic and Equality.

## Structural Rules

### ASSUME

Introduce an assumption from the context.

- **Premises**: none
- **Formula**: must be in `context.assumptions`

### REITERATE

Repeat a previously derived formula.

- **Premises**: 1 node
- **Formula**: must equal premise formula

## Propositional Rules

### IMP_ELIM (Modus Ponens)

From A and A→B, derive B.

- **Premises**: 2 nodes (A and A→B in either order)
- **Formula**: B

### AND_INTRO

From A and B, derive A∧B.

- **Premises**: 2 nodes
- **Formula**: `{"and": [premise1, premise2]}`

### AND_ELIM_L

From A∧B, derive A.

- **Premises**: 1 node with `{"and": [A, B]}`
- **Formula**: A

### AND_ELIM_R

From A∧B, derive B.

- **Premises**: 1 node with `{"and": [A, B]}`
- **Formula**: B

### OR_INTRO_L

From A, derive A∨B.

- **Premises**: 1 node with formula A
- **Formula**: `{"or": [A, B]}`

### OR_INTRO_R

From B, derive A∨B.

- **Premises**: 1 node with formula B
- **Formula**: `{"or": [A, B]}`

### NOT_ELIM

From A and ¬A, derive ⊥.

- **Premises**: 2 nodes (A and `{"not": A}`)
- **Formula**: `{"atom": {"pred": "False", "args": []}}`

## Equality Rules

### EQ_REFL

Derive t=t (reflexivity).

- **Premises**: none
- **Formula**: `{"eq": {"left": t, "right": t}}` where left == right

### EQ_SYMM

From t1=t2, derive t2=t1.

- **Premises**: 1 node with `{"eq": {"left": t1, "right": t2}}`
- **Formula**: `{"eq": {"left": t2, "right": t1}}`

### EQ_TRANS

From t1=t2 and t2=t3, derive t1=t3.

- **Premises**: 2 nodes with equalities sharing a middle term
- **Formula**: `{"eq": {"left": t1, "right": t3}}`

### EQ_SUBST_PRED

From t1=t2 and P(t1), derive P(t2).

- **Premises**: 2 nodes (equality and unary predicate)
- **Formula**: unary predicate with substituted term
- **Limitation**: Unary predicates only in v1

## Kernel Verification

```python
def pwk_check(pwof):
    # 1. Version check
    if pwof["pwof_version"] != "1":
        return FAIL("unsupported version")

    # 2. Ruleset check
    if pwof["ruleset_id"] != "PWK_ND_PROP_EQ_v1":
        return FAIL("unsupported ruleset")

    # 3. Process nodes in order
    derived = {}
    for node in pwof["proof"]["nodes"]:
        # Verify premises exist
        for p in node["premises"]:
            if p not in derived:
                return FAIL("unresolved premise")

        # Check rule application
        if not check_rule(node, assumptions, derived):
            return FAIL("invalid rule")

        derived[node["id"]] = node["formula"]

    # 4. Verify conclusion
    conclusion_id = pwof["proof"]["conclusion"]
    if derived[conclusion_id] != pwof["goal"]["formula"]:
        return FAIL("goal mismatch")

    return PASS
```

## Fail-Closed Behavior

The kernel MUST fail on:
- Unsupported version
- Unsupported ruleset
- Missing conclusion
- Unresolved premises
- Invalid rule applications
- Goal mismatch
- Any exception

## Reference

See `origin/modules/proofweave/` for implementation.
