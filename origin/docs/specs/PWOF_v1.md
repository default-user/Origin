# PWOF v1 Specification

**Version**: 1.0
**Attribution**: Ande → Kai
**License**: WCL-1.0

## Overview

PWOF (ProofWeave Object Format) is a canonical JSON format for representing formal proofs.

## Trust Boundary

```
TRUSTED:   PWK Kernel (proof checker)
UNTRUSTED: Everything else (engines, tactics, LLMs, renderers)
```

## Top-Level Schema

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
    "nodes": [<node>, ...],
    "conclusion": "<node_id>"
  },
  "who": { ... },
  "why": { ... }
}
```

## Formula Encoding

### Atoms

```json
{"atom": {"pred": "<predicate>", "args": [<term>, ...]}}
```

### Equality

```json
{"eq": {"left": <term>, "right": <term>}}
```

### Connectives

| Type | Format |
|------|--------|
| And | `{"and": [<f1>, <f2>]}` |
| Or | `{"or": [<f1>, <f2>]}` |
| Implication | `{"imp": [<f1>, <f2>]}` |
| Negation | `{"not": <formula>}` |

### False (Bottom)

```json
{"atom": {"pred": "False", "args": []}}
```

### Quantifiers (Reserved for v1.1+)

```json
{"all": {"var": "<name>", "body": <formula>}}
{"ex": {"var": "<name>", "body": <formula>}}
```

v1 kernel MUST reject quantifiers.

## Term Encoding

### Variables

```json
{"var": "<name>"}
```

### Functions

```json
{"fun": {"name": "<name>", "args": [<term>, ...]}}
```

## Proof Node

```json
{
  "id": "<unique_id>",
  "rule": "<rule_name>",
  "premises": ["<node_id>", ...],
  "formula": <formula>,
  "justification": { ... }
}
```

## Canonicalization

For deterministic hashing:
1. UTF-8 encoding
2. Sorted object keys (recursive)
3. No whitespace
4. No floats (integers only)

```python
canonical = json.dumps(obj, sort_keys=True, separators=(',', ':'))
hash = sha256(canonical.encode('utf-8')).hexdigest()
```

## Reference

See `origin/modules/proofweave/` and `PWK_RULESET_v1.md` for implementation.
