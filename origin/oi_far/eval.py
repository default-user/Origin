"""Evaluation harness for OI-FAR."""

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class EvalPrompt:
    """An evaluation prompt."""
    id: str
    category: str  # knowledge, reasoning, planning, formatting, contradiction
    prompt: str
    expected_behavior: str  # "answer", "unknown", "partial"
    expected_contains: list[str] = field(default_factory=list)
    expected_not_contains: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    """Result of evaluating a single prompt."""
    prompt_id: str
    passed: bool
    output: str
    status: str
    checks: dict[str, bool]
    deterministic: bool
    timing_ms: float
    error: str | None = None


def load_prompts(prompts_path: str | Path) -> list[EvalPrompt]:
    """Load evaluation prompts from YAML files."""
    prompts_path = Path(prompts_path)
    prompts = []

    if prompts_path.is_file():
        # Single file
        files = [prompts_path]
    else:
        # Directory
        files = list(prompts_path.glob("*.yaml")) + list(prompts_path.glob("*.yml"))

    for file_path in sorted(files):
        try:
            with open(file_path) as f:
                data = yaml.safe_load(f)

            if isinstance(data, list):
                for item in data:
                    prompts.append(EvalPrompt(
                        id=item.get("id", f"{file_path.stem}_{len(prompts)}"),
                        category=item.get("category", file_path.stem),
                        prompt=item["prompt"],
                        expected_behavior=item.get("expected_behavior", "answer"),
                        expected_contains=item.get("expected_contains", []),
                        expected_not_contains=item.get("expected_not_contains", []),
                        tags=item.get("tags", []),
                    ))
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}")

    return prompts


def check_output(
    output: str,
    status: str,
    prompt: EvalPrompt,
) -> dict[str, bool]:
    """Check if output meets expectations."""
    checks = {}

    # Check behavior
    if prompt.expected_behavior == "answer":
        checks["behavior"] = status == "complete"
    elif prompt.expected_behavior == "unknown":
        checks["behavior"] = status == "unknown" or "UNKNOWN" in output
    elif prompt.expected_behavior == "partial":
        checks["behavior"] = status in ("partial", "complete")
    else:
        checks["behavior"] = True

    # Check expected content
    output_lower = output.lower()
    for expected in prompt.expected_contains:
        checks[f"contains_{expected[:20]}"] = expected.lower() in output_lower

    # Check forbidden content
    for forbidden in prompt.expected_not_contains:
        checks[f"not_contains_{forbidden[:20]}"] = forbidden.lower() not in output_lower

    return checks


def check_determinism(
    runtime,
    prompt: EvalPrompt,
    first_output: str,
    runs: int = 3,
) -> bool:
    """Check that the same prompt produces identical output."""
    for _ in range(runs):
        result = runtime.run(prompt.prompt)
        if result["output"] != first_output:
            return False
    return True


def run_evaluation(
    vault_path: str | Path,
    prompts_path: str | Path | None = None,
    check_determinism_runs: int = 2,
) -> dict[str, Any]:
    """
    Run full evaluation suite.

    Args:
        vault_path: Path to vault
        prompts_path: Path to prompts (file or directory)
        check_determinism_runs: Number of runs for determinism check

    Returns:
        Evaluation results dictionary
    """
    from .cli import OIFarRuntime

    vault_path = Path(vault_path)
    runtime = OIFarRuntime(vault_path=vault_path)

    # Load prompts
    if prompts_path is None:
        prompts_path = vault_path / "eval" / "prompts"

    prompts = load_prompts(prompts_path)

    if not prompts:
        return {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "unknowns": 0,
            "determinism_check": True,
            "error": "No prompts found",
        }

    results: list[EvalResult] = []
    determinism_passed = True

    for prompt in prompts:
        try:
            start = time.time()
            result = runtime.run(prompt.prompt)
            timing = (time.time() - start) * 1000

            output = result["output"]
            status = result["status"]

            # Check output
            checks = check_output(output, status, prompt)

            # Check determinism
            is_deterministic = check_determinism(
                runtime, prompt, output, check_determinism_runs
            )
            if not is_deterministic:
                determinism_passed = False

            # Determine pass/fail
            passed = all(checks.values()) and is_deterministic

            results.append(EvalResult(
                prompt_id=prompt.id,
                passed=passed,
                output=output,
                status=status,
                checks=checks,
                deterministic=is_deterministic,
                timing_ms=timing,
            ))

        except Exception as e:
            results.append(EvalResult(
                prompt_id=prompt.id,
                passed=False,
                output="",
                status="error",
                checks={},
                deterministic=False,
                timing_ms=0,
                error=str(e),
            ))

    # Calculate metrics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed and r.status != "unknown")
    unknowns = sum(1 for r in results if r.status == "unknown")

    # Calculate by category
    by_category: dict[str, dict] = {}
    for prompt, result in zip(prompts, results):
        cat = prompt.category
        if cat not in by_category:
            by_category[cat] = {"total": 0, "passed": 0}
        by_category[cat]["total"] += 1
        if result.passed:
            by_category[cat]["passed"] += 1

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "unknowns": unknowns,
        "determinism_check": determinism_passed,
        "pass_rate": passed / total if total > 0 else 0,
        "by_category": by_category,
        "results": [
            {
                "id": r.prompt_id,
                "passed": r.passed,
                "status": r.status,
                "deterministic": r.deterministic,
                "timing_ms": r.timing_ms,
                "error": r.error,
            }
            for r in results
        ],
    }


def generate_golden_outputs(
    vault_path: str | Path,
    prompts_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    """
    Generate golden outputs for prompts.

    This creates reference outputs that future runs should match.
    """
    from .cli import OIFarRuntime

    vault_path = Path(vault_path)
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)

    runtime = OIFarRuntime(vault_path=vault_path)
    prompts = load_prompts(prompts_path)

    golden = {}
    for prompt in prompts:
        result = runtime.run(prompt.prompt)

        # Hash the output for quick comparison
        output_hash = hashlib.sha256(result["output"].encode()).hexdigest()[:16]

        golden[prompt.id] = {
            "prompt": prompt.prompt,
            "output": result["output"],
            "output_hash": output_hash,
            "status": result["status"],
            "confidence": result["confidence"],
        }

    # Save golden outputs
    golden_file = output_path / "golden_outputs.json"
    with open(golden_file, "w") as f:
        json.dump(golden, f, indent=2, sort_keys=True)

    return {
        "total": len(golden),
        "output_file": str(golden_file),
    }


def verify_against_golden(
    vault_path: str | Path,
    prompts_path: str | Path,
    golden_path: str | Path,
) -> dict[str, Any]:
    """
    Verify current outputs against golden outputs.

    This is used in CI to detect output drift.
    """
    from .cli import OIFarRuntime

    vault_path = Path(vault_path)
    golden_path = Path(golden_path)

    # Load golden outputs
    golden_file = golden_path / "golden_outputs.json"
    if not golden_file.exists():
        return {"error": "Golden outputs not found", "passed": False}

    with open(golden_file) as f:
        golden = json.load(f)

    runtime = OIFarRuntime(vault_path=vault_path)
    prompts = load_prompts(prompts_path)

    drifts = []
    for prompt in prompts:
        if prompt.id not in golden:
            continue

        result = runtime.run(prompt.prompt)
        expected = golden[prompt.id]

        # Compare hash
        output_hash = hashlib.sha256(result["output"].encode()).hexdigest()[:16]

        if output_hash != expected["output_hash"]:
            drifts.append({
                "prompt_id": prompt.id,
                "expected_hash": expected["output_hash"],
                "actual_hash": output_hash,
                "expected_output": expected["output"][:200],
                "actual_output": result["output"][:200],
            })

    return {
        "total_checked": len([p for p in prompts if p.id in golden]),
        "drifts": len(drifts),
        "drift_details": drifts,
        "passed": len(drifts) == 0,
    }
