# ProofWeave Specification (PWOF v1 + PWK)

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## 1. Overview

ProofWeave defines:
1. **PWOF v1**: Canonical JSON proof object format
2. **PWK**: Trusted kernel checker

### Trust Boundary

The PWK Kernel is **TRUSTED**. Everything else is **UNTRUSTED**:
- Proof engines
- Tactics
- LLM suggestions
- Renderers
- User input

## 2. PWOF v1 JSON Schema

### 2.1 Top-Level Structure

```json
{
  "pwof_version": "1",
  "ruleset_id": "PWK_ND_PROP_EQ_v1",
  "context": { ... },
  "goal": { ... },
  "proof": { ... },
  "who": { ... },   // optional
  "why": { ... }    // optional
}
```

### 2.2 Context

```json
{
  "assumptions": [<formula>, ...]
}
```

### 2.3 Goal

```json
{
  "formula": <formula>
}
```

### 2.4 Proof

```json
{
  "nodes": [<proof_node>, ...],
  "conclusion": "<node_id>"
}
```

### 2.5 Proof Node

```json
{
  "id": "<string>",
  "rule": "<rule_id>",
  "premises": ["<node_id>", ...],
  "formula": <formula>,
  "justification": { ... }  // optional
}
```

## 3. Formula Encoding

### 3.1 Atoms

```json
{"atom": {"pred": "<predicate>", "args": [<term>, ...]}}
```

### 3.2 Equality

```json
{"eq": {"left": <term>, "right": <term>}}
```

### 3.3 Connectives

| Connective | Format |
|------------|--------|
| Conjunction | `{"and": [<formula>, <formula>]}` |
| Disjunction | `{"or": [<formula>, <formula>]}` |
| Implication | `{"imp": [<formula>, <formula>]}` |
| Negation | `{"not": <formula>}` |

### 3.4 False (Bottom)

```json
{"atom": {"pred": "False", "args": []}}
```

### 3.5 Quantifiers (Reserved for v1.1+)

```json
{"all": {"var": "<name>", "body": <formula>}}
{"ex": {"var": "<name>", "body": <formula>}}
```

**Note**: v1 kernel MUST reject quantifiers (fail-closed).

## 4. Term Encoding

### 4.1 Variables

```json
{"var": "<name>"}
```

### 4.2 Functions

```json
{"fun": {"name": "<name>", "args": [<term>, ...]}}
```

## 5. PWK_ND_PROP_EQ_v1 Ruleset

### 5.1 Structural Rules

#### ASSUME

Formula must exactly match a context assumption.

- Premises: none
- Formula: must be in `context.assumptions`

#### REITERATE

Repeat a previously derived formula.

- Premises: exactly 1 node
- Formula: must equal premise formula

### 5.2 Propositional Rules

#### IMP_ELIM (Modus Ponens)

From A and A→B, derive B.

- Premises: 2 nodes (p1, p2)
- One premise: A
- Other premise: `{"imp": [A, B]}`
- Conclusion: B

#### AND_INTRO

From A and B, derive A∧B.

- Premises: 2 nodes
- Formula: `{"and": [premise1, premise2]}`

#### AND_ELIM_L

From A∧B, derive A.

- Premises: 1 node with `{"and": [A, B]}`
- Formula: A

#### AND_ELIM_R

From A∧B, derive B.

- Premises: 1 node with `{"and": [A, B]}`
- Formula: B

#### OR_INTRO_L

From A, derive A∨B.

- Premises: 1 node with formula A
- Formula: `{"or": [A, B]}`

#### OR_INTRO_R

From B, derive A∨B.

- Premises: 1 node with formula B
- Formula: `{"or": [A, B]}`

#### NOT_ELIM

From A and ¬A, derive ⊥.

- Premises: 2 nodes
- One: some formula A
- Other: `{"not": A}`
- Conclusion: `{"atom": {"pred": "False", "args": []}}`

### 5.3 Equality Rules

#### EQ_REFL

Derive t=t (reflexivity).

- Premises: none
- Formula: `{"eq": {"left": t, "right": t}}` where left equals right

#### EQ_SYMM

From t1=t2, derive t2=t1.

- Premises: 1 node with `{"eq": {"left": t1, "right": t2}}`
- Formula: `{"eq": {"left": t2, "right": t1}}`

#### EQ_TRANS

From t1=t2 and t2=t3, derive t1=t3.

- Premises: 2 nodes with equalities sharing middle term
- Formula: `{"eq": {"left": t1, "right": t3}}`

#### EQ_SUBST_PRED

From t1=t2 and P(t1), derive P(t2).

- Premises: 2 nodes
- One: equality `{"eq": {"left": t1, "right": t2}}`
- Other: unary atom `{"atom": {"pred": "P", "args": [t1]}}`
- Formula: `{"atom": {"pred": "P", "args": [t2]}}`
- **Limitation**: Unary predicates only in v1

## 6. Kernel Verification Algorithm

```
function pwk_check(pwof):
  1. IF pwof.pwof_version != "1" THEN FAIL
  2. IF pwof.ruleset_id not in SUPPORTED_RULESETS THEN FAIL
  3. assumptions = pwof.context.assumptions
  4. goal_formula = pwof.goal.formula
  5. nodes = pwof.proof.nodes
  6. conclusion_id = pwof.proof.conclusion
  7. IF nodes is empty THEN FAIL
  8. IF conclusion_id is empty THEN FAIL
  9. derived = {}
  10. FOR each node in nodes:
      a. FOR each premise_id in node.premises:
         IF premise_id not in derived THEN FAIL
      b. IF not check_rule(node, assumptions, derived) THEN FAIL
      c. derived[node.id] = node.formula
  11. IF conclusion_id not in derived THEN FAIL
  12. IF derived[conclusion_id] != goal_formula THEN FAIL
  13. RETURN PASS
```

## 7. Canonicalization

### 7.1 Rules

1. UTF-8 encoding
2. JSON with sorted object keys (recursive)
3. Arrays preserve order
4. No floats (integers only)
5. No whitespace
6. IDs are stable strings

### 7.2 Hash Computation

```python
canonical_bytes = canonicalize(pwof)
hash = sha256(canonical_bytes).hexdigest()
```

TODO: blake3 preferred if available.

## 8. Error Handling

The kernel is **fail-closed**:

- Unsupported version → FAIL
- Unsupported ruleset → FAIL
- Missing conclusion → FAIL
- Unresolved premise → FAIL
- Invalid rule application → FAIL
- Goal mismatch → FAIL
- Any exception → FAIL

## 9. CLI Commands

| Command | Exit Code | Description |
|---------|-----------|-------------|
| `pwk check <file>` | 0=PASS, 1=FAIL | Verify proof |
| `pwk hash <file>` | 0 | Output canonical hash |
| `pwk info <file>` | 0 | Display proof info |
| `pwk selftest` | 0=PASS, 1=FAIL | Run self-tests |

## 10. Sample Proofs

### 10.1 Modus Ponens (PASS)

```json
{
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
      {"id": "n1", "rule": "ASSUME", "premises": [],
       "formula": {"atom": {"pred": "A", "args": []}}},
      {"id": "n2", "rule": "ASSUME", "premises": [],
       "formula": {"imp": [
         {"atom": {"pred": "A", "args": []}},
         {"atom": {"pred": "B", "args": []}}
       ]}},
      {"id": "n3", "rule": "IMP_ELIM", "premises": ["n1", "n2"],
       "formula": {"atom": {"pred": "B", "args": []}}}
    ],
    "conclusion": "n3"
  }
}
```

### 10.2 Invalid Proof (FAIL)

```json
{
  "pwof_version": "1",
  "ruleset_id": "PWK_ND_PROP_EQ_v1",
  "context": {"assumptions": []},
  "goal": {"formula": {"atom": {"pred": "P", "args": []}}},
  "proof": {
    "nodes": [
      {"id": "n1", "rule": "ASSUME", "premises": [],
       "formula": {"atom": {"pred": "P", "args": []}}}
    ],
    "conclusion": "n1"
  }
}
```

Fails because ASSUME requires formula to be in context.assumptions.

## 11. Attribution

Original design: Ande → Kai
Licensed under Weaver Commons License (WCL-1.0)
