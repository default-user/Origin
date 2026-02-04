# ProofWeave (PWOF v1 + PWK Kernel)

**Attribution: Ande → Kai**
**License: WCL-1.0**

ProofWeave is a deterministic proof object format with a trusted kernel checker.

## Trust Boundary

```
┌─────────────────────────────────────────────┐
│              TRUSTED ZONE                   │
│  ┌───────────────────────────────────────┐  │
│  │        PWK Kernel Checker            │  │
│  │   - Validates proof steps            │  │
│  │   - Checks rule applications         │  │
│  │   - Verifies goal match              │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
                    ▲
                    │ PWOF v1 JSON
                    │
┌─────────────────────────────────────────────┐
│            UNTRUSTED ZONE                   │
│  - Proof engines                            │
│  - Tactics                                  │
│  - LLM suggestions                          │
│  - Renderers                                │
│  - User input                               │
└─────────────────────────────────────────────┘
```

**The PWK Kernel is the ONLY trusted component.**

## Features

- **PWOF v1**: Canonical JSON proof format
- **PWK Kernel**: Trusted checker with fail-closed semantics
- **PWK_ND_PROP_EQ_v1**: Natural deduction + equality ruleset
- **Deterministic**: Canonicalization for hashing
- **Minimal**: Small trusted code base

## Installation

```bash
cd origin/modules/proofweave
pip install -e .
```

## Usage

### Python API

```python
from proofweave import pwk_check, PWKResult

# Construct or load a PWOF proof object
pwof = {
    "pwof_version": "1",
    "ruleset_id": "PWK_ND_PROP_EQ_v1",
    "context": {
        "assumptions": [
            {"atom": {"pred": "A", "args": []}}
        ]
    },
    "goal": {"formula": {"atom": {"pred": "A", "args": []}}},
    "proof": {
        "nodes": [
            {
                "id": "n1",
                "rule": "ASSUME",
                "premises": [],
                "formula": {"atom": {"pred": "A", "args": []}}
            }
        ],
        "conclusion": "n1"
    }
}

# Check the proof
result = pwk_check(pwof)

if result.passed:
    print(f"Proof verified! ({result.node_count} steps)")
else:
    print(f"Proof failed: {result.message}")
```

### CLI (pwk)

```bash
# Check a proof (exit 0 = PASS, exit 1 = FAIL)
pwk check proof.json

# Compute canonical hash
pwk hash proof.json

# Display proof info
pwk info proof.json

# Run self-tests
pwk selftest
```

## PWOF v1 Schema

```json
{
  "pwof_version": "1",
  "ruleset_id": "PWK_ND_PROP_EQ_v1",
  "context": {
    "assumptions": [<formula>, ...]
  },
  "goal": {
    "formula": <formula>
  },
  "proof": {
    "nodes": [
      {
        "id": "n1",
        "rule": "RULE_NAME",
        "premises": ["node_id", ...],
        "formula": <formula>
      },
      ...
    ],
    "conclusion": "last_node_id"
  },
  "who": { ... },  // optional
  "why": { ... }   // optional
}
```

## Formula Encoding

| Type | Format |
|------|--------|
| Atom | `{"atom": {"pred": "P", "args": [terms...]}}` |
| Equality | `{"eq": {"left": term, "right": term}}` |
| And | `{"and": [f1, f2]}` |
| Or | `{"or": [f1, f2]}` |
| Implication | `{"imp": [f1, f2]}` |
| Negation | `{"not": formula}` |
| False (⊥) | `{"atom": {"pred": "False", "args": []}}` |

## Term Encoding

| Type | Format |
|------|--------|
| Variable | `{"var": "x"}` |
| Function | `{"fun": {"name": "f", "args": [terms...]}}` |

## PWK_ND_PROP_EQ_v1 Ruleset

### Structural Rules

| Rule | Description | Premises |
|------|-------------|----------|
| ASSUME | Assert assumption | (must be in context) |
| REITERATE | Repeat formula | 1 node |

### Propositional Rules

| Rule | Description | Premises |
|------|-------------|----------|
| IMP_ELIM | A, A→B ⊢ B | 2 nodes |
| AND_INTRO | A, B ⊢ A∧B | 2 nodes |
| AND_ELIM_L | A∧B ⊢ A | 1 node |
| AND_ELIM_R | A∧B ⊢ B | 1 node |
| OR_INTRO_L | A ⊢ A∨B | 1 node |
| OR_INTRO_R | B ⊢ A∨B | 1 node |
| NOT_ELIM | A, ¬A ⊢ ⊥ | 2 nodes |

### Equality Rules

| Rule | Description | Premises |
|------|-------------|----------|
| EQ_REFL | ⊢ t=t | 0 nodes |
| EQ_SYMM | t1=t2 ⊢ t2=t1 | 1 node |
| EQ_TRANS | t1=t2, t2=t3 ⊢ t1=t3 | 2 nodes |
| EQ_SUBST_PRED | t1=t2, P(t1) ⊢ P(t2) | 2 nodes (unary only) |

## Kernel Behavior

1. **Fail-closed** on unsupported version
2. **Fail-closed** on unsupported ruleset
3. **Fail-closed** on any error
4. Pass ONLY if:
   - Conclusion node exists
   - All premises resolvable
   - All rules valid
   - Final formula equals goal exactly

## Canonicalization

For deterministic hashing:
- UTF-8 encoding
- Sorted object keys
- No whitespace
- No floats (integers only)

```python
from proofweave import compute_hash

hash_value = compute_hash(pwof)  # SHA-256 by default
```
