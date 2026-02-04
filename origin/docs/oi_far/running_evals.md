# Running OI-FAR Evaluations

This guide explains how to run the evaluation suite and interpret results.

## Quick Start

```bash
# Run full evaluation suite
python -m oi_far.cli eval

# Run with specific prompts
python -m oi_far.cli eval --prompts eval/prompts/knowledge.yaml

# Run from project root
cd origin && python -m oi_far.cli eval
```

## Evaluation Suite

The eval suite contains 200+ prompts across categories:

| Category | Count | Purpose |
|----------|-------|---------|
| Knowledge | 60 | Test broad knowledge retrieval |
| Reasoning | 50 | Multi-step reasoning chains |
| Formatting | 30 | Instruction following |
| Contradictions | 30 | Fabrication prevention |
| Planning | 30 | Process and how-to queries |

## Prompt Format

Prompts are YAML files:

```yaml
- id: know_001
  prompt: "What is the Holodeck?"
  expected_behavior: answer  # answer, unknown, partial
  expected_contains:
    - "holodeck"
  expected_not_contains:
    - "fabricated_term"
  tags:
    - knowledge
    - concept
```

### Expected Behaviors

- `answer`: Should provide a complete answer
- `unknown`: Should return UNKNOWN (for fabrication tests)
- `partial`: May provide partial information

## Running Evaluations

### Full Suite

```bash
python -m oi_far.cli eval
```

Output:
```
Evaluation Results:
  Total: 200
  Passed: 180
  Failed: 15
  Unknown: 5
  Determinism: PASS
```

### Specific Category

```bash
python -m oi_far.cli eval --prompts eval/prompts/contradictions.yaml
```

### Programmatic Usage

```python
from oi_far.eval import run_evaluation

results = run_evaluation(
    vault_path=".",
    prompts_path="eval/prompts",
    check_determinism_runs=3,
)

print(f"Pass rate: {results['pass_rate']:.1%}")
for cat, stats in results['by_category'].items():
    print(f"  {cat}: {stats['passed']}/{stats['total']}")
```

## Metrics

### Correctness
- Checks expected_contains strings appear
- Checks expected_not_contains strings don't appear
- Validates expected_behavior matches status

### Determinism
- Runs each prompt multiple times
- Compares outputs byte-for-byte
- Fails if any difference detected

### Rates
- **Pass Rate**: % of prompts that pass all checks
- **Unknown Rate**: % returning UNKNOWN status
- **Failure Rate**: % that fail (excluding unknowns)

## Golden Outputs

Generate reference outputs:

```bash
python -c "
from oi_far.eval import generate_golden_outputs
generate_golden_outputs('.', 'eval/prompts', 'eval/golden_outputs')
"
```

Verify against golden:

```python
from oi_far.eval import verify_against_golden

result = verify_against_golden(
    vault_path=".",
    prompts_path="eval/prompts",
    golden_path="eval/golden_outputs",
)

if not result['passed']:
    print(f"Drift detected in {result['drifts']} prompts")
    for drift in result['drift_details']:
        print(f"  - {drift['prompt_id']}")
```

## CI Integration

Add to your CI workflow:

```yaml
# .github/workflows/eval.yml
name: OI-FAR Evaluation

on: [push, pull_request]

jobs:
  eval:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pyyaml
      - name: Run evaluation
        run: python -m oi_far.cli eval
      - name: Check determinism
        run: |
          python -m oi_far.cli run "What is Origin?" > out1.txt
          python -m oi_far.cli run "What is Origin?" > out2.txt
          diff out1.txt out2.txt
```

## Adding Prompts

Create a new YAML file in `eval/prompts/`:

```yaml
# eval/prompts/my_tests.yaml
- id: my_001
  prompt: "My test query"
  expected_behavior: answer
  expected_contains: ["expected", "terms"]
  tags: [custom]
```

Guidelines:
- Use unique IDs with category prefix
- Include relevant tags
- Set realistic expectations
- Test edge cases

## Debugging Failures

When a prompt fails:

```python
from oi_far import get_runtime

runtime = get_runtime(".")
result = runtime.run("failing query")

# Examine result
print(f"Status: {result['status']}")
print(f"Confidence: {result['confidence']}")
print(f"Sources: {result['sources']}")
print(f"Critic passed: {result['critic_passed']}")
print(f"Output: {result['output']}")
```

Common failure causes:
1. **Missing knowledge**: Add relevant packs/bricks
2. **Low confidence**: Improve source quality
3. **Contradictions**: Resolve conflicting claims
4. **Format issues**: Adjust expected_contains patterns

## Interpreting Results

### Good Results
- High pass rate (>90%)
- Low unknown rate for knowledge prompts
- Determinism always passes
- Contradictions all pass (no fabrication)

### Warning Signs
- High unknown rate → Need more knowledge
- Failing contradictions → Fabrication issues
- Determinism failures → Non-deterministic code
- Low confidence → Weak sources

## Continuous Improvement

Use the growth loop to improve coverage:

```bash
# See recommendations
python -m oi_far.cli growth

# Add missing knowledge
# Re-run eval
python -m oi_far.cli eval
```

Track improvement over time by logging eval results.
