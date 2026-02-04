# Determinism Guarantees

OI-FAR provides strong determinism guarantees: **same input always produces identical output**.

## Why Determinism Matters

1. **Reproducibility**: Results can be verified and audited
2. **Testing**: Golden outputs enable regression testing
3. **Trust**: Users can rely on consistent behavior
4. **Debugging**: Issues can be reliably reproduced

## Determinism Invariant

```
∀ query, state: run(query, state) == run(query, state)
```

Given the same:
- Query string
- Knowledge base state
- Session state

The output will be byte-for-byte identical.

## How Determinism is Achieved

### 1. No Randomness

OI-FAR uses no random number generators:
- No `random.random()` or `numpy.random`
- No shuffling of collections
- No sampling or Monte Carlo methods

### 2. Deterministic Sorting

All iterations use deterministic ordering:

```python
# Always sort by ID for consistent ordering
sorted_bricks = sorted(bricks, key=lambda b: b.id)

# Use tuple keys for multi-field sorting
sorted_items = sorted(items, key=lambda x: (-x.score, x.id))
```

### 3. Fixed Algorithm Parameters

All algorithms use fixed, explicit parameters:
- BM25 with k1=1.5, b=0.75
- Scoring weights are configurable but fixed per run
- No adaptive or learned parameters

### 4. Deterministic Hashing

Content hashes use SHA-256:

```python
import hashlib

def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()
```

### 5. Stable JSON Serialization

JSON output uses sorted keys:

```python
import json

json.dumps(data, sort_keys=True, indent=2)
```

## Verification

### Manual Check

```bash
# Run twice
python -m oi_far.cli run "What is Origin?" > out1.txt
python -m oi_far.cli run "What is Origin?" > out2.txt

# Compare
diff out1.txt out2.txt
# Should produce no output (files identical)
```

### Programmatic Check

```python
from oi_far import run

result1 = run("What is Origin?")
result2 = run("What is Origin?")

assert result1["output"] == result2["output"]
assert result1["status"] == result2["status"]
assert result1["confidence"] == result2["confidence"]
```

### Eval Suite Check

The evaluation suite includes determinism checks:

```python
from oi_far.eval import run_evaluation

results = run_evaluation(
    vault_path=".",
    prompts_path="eval/prompts",
    check_determinism_runs=5,  # Run each prompt 5 times
)

assert results["determinism_check"] == True
```

## Sources of Non-Determinism (Avoided)

OI-FAR explicitly avoids these common sources of non-determinism:

| Source | How Avoided |
|--------|-------------|
| `random` module | Not imported |
| Set iteration | Convert to sorted list |
| Dict iteration (Python <3.7) | Use Python 3.7+ |
| Floating point errors | Use exact comparisons where needed |
| Timestamps in output | Excluded from comparison |
| External API calls | Cached or disabled |
| LLM inference | Not used in core reasoning |

## Caveats

### Timestamps

Internal timestamps (for logging/metrics) are non-deterministic but excluded from output comparison:

```python
result = run("query")
# result["timing"]["total_ms"] may vary
# result["output"] is always identical
```

### Tool Results

Some tools produce non-deterministic results:
- `run_tests()`: Test execution times vary
- Network operations: Not used in core pipeline

These are marked with `deterministic=False`:

```python
result = registry.invoke("run_tests")
assert result.deterministic == False
```

### Knowledge Base State

Determinism assumes identical knowledge base:
- Same documents
- Same bricks
- Same index state

If knowledge changes, outputs may change.

## Golden Output Testing

Use golden outputs for regression testing:

```python
from oi_far.eval import generate_golden_outputs, verify_against_golden

# Generate (once, after verification)
generate_golden_outputs(".", "eval/prompts", "eval/golden_outputs")

# Verify (in CI)
result = verify_against_golden(".", "eval/prompts", "eval/golden_outputs")
if not result["passed"]:
    raise AssertionError(f"Output drift detected: {result['drifts']}")
```

## Debugging Non-Determinism

If determinism fails:

1. **Check for randomness**: Search code for `random`, `shuffle`, `sample`
2. **Check set usage**: Ensure sets are converted to sorted lists before iteration
3. **Check external calls**: Disable or mock network calls
4. **Check timestamps**: Exclude timing from comparisons
5. **Check float comparisons**: Use tolerance-based comparison if needed

```python
# Debug helper
def debug_diff(result1, result2):
    if result1["output"] != result2["output"]:
        # Find first difference
        for i, (c1, c2) in enumerate(zip(result1["output"], result2["output"])):
            if c1 != c2:
                print(f"First difference at position {i}")
                print(f"  Expected: {c1!r}")
                print(f"  Got: {c2!r}")
                break
```

## Performance Note

Determinism does not significantly impact performance:
- Sorting is O(n log n) which is acceptable
- No additional computation required
- Memory usage unchanged

The benefits of reproducibility far outweigh any minor overhead.
