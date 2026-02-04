"""Reasoning core types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class StepType(Enum):
    """Types of plan steps."""
    RETRIEVE = "retrieve"  # Fetch more information
    DEFINE = "define"  # Define a term/concept
    COMPARE = "compare"  # Compare items
    DEDUCE = "deduce"  # Apply logical deduction
    VERIFY = "verify"  # Verify a claim
    SYNTHESIZE = "synthesize"  # Combine information
    FORMAT = "format"  # Format output
    UNKNOWN = "unknown"  # Cannot determine step type


class AnswerStatus(Enum):
    """Status of an answer."""
    COMPLETE = "complete"  # Fully answered
    PARTIAL = "partial"  # Partially answered
    UNKNOWN = "unknown"  # Cannot answer
    FAILED = "failed"  # Processing failed


@dataclass
class Assumption:
    """An explicit assumption made during reasoning."""
    id: str
    description: str
    confidence: float
    what_would_refute: str
    source: str  # "inferred", "user", "default"


@dataclass
class PlanStep:
    """A single step in a reasoning plan."""
    step_id: str
    step_type: StepType
    description: str
    inputs: list[str]  # IDs of required inputs (bricks, prior steps)
    expected_output: str
    constraints: list[str] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "step_type": self.step_type.value,
            "description": self.description,
            "inputs": self.inputs,
            "expected_output": self.expected_output,
            "constraints": self.constraints,
            "assumptions": [
                {"id": a.id, "description": a.description, "confidence": a.confidence}
                for a in self.assumptions
            ],
        }


@dataclass
class StepResult:
    """Result of executing a plan step."""
    step_id: str
    success: bool
    output: Any
    claims_used: list[str]  # Claim IDs used
    confidence: float
    error: str | None = None


@dataclass
class AnswerComponent:
    """A component of the final answer."""
    component_type: str  # "claim", "definition", "comparison", "list", "unknown"
    content: str
    supporting_bricks: list[str]  # Brick IDs
    confidence: float
    assumptions: list[str] = field(default_factory=list)


@dataclass
class AnswerPlan:
    """
    Complete plan for an answer.

    This is the output of the Solver and input to the Renderer.
    Contains all information needed to generate the final response.
    """
    query: str
    intent: str
    status: AnswerStatus

    # Answer components (ordered)
    components: list[AnswerComponent]

    # Supporting evidence
    source_bricks: list[str]  # Brick IDs
    source_claims: list[str]  # Claim texts

    # Assumptions and unknowns
    assumptions: list[Assumption]
    unknowns: list[str]  # What we don't know

    # Execution trace
    plan_steps: list[PlanStep]
    step_results: list[StepResult]

    # Confidence metrics
    overall_confidence: float
    claim_coverage: float  # Fraction of answer backed by claims

    # Metadata
    reasoning_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "intent": self.intent,
            "status": self.status.value,
            "components": [
                {
                    "type": c.component_type,
                    "content": c.content,
                    "confidence": c.confidence,
                    "supporting_bricks": c.supporting_bricks,
                }
                for c in self.components
            ],
            "source_bricks": self.source_bricks,
            "assumptions": [
                {"id": a.id, "description": a.description, "confidence": a.confidence}
                for a in self.assumptions
            ],
            "unknowns": self.unknowns,
            "overall_confidence": self.overall_confidence,
            "claim_coverage": self.claim_coverage,
            "plan_steps": [s.to_dict() for s in self.plan_steps],
        }


@dataclass
class CriticFix:
    """A fix suggested by the critic."""
    fix_type: str  # "add_source", "remove_claim", "add_assumption", "flag_unknown"
    target: str  # What to fix
    description: str
    severity: str  # "error", "warning", "suggestion"


@dataclass
class CriticResult:
    """Result of critic evaluation."""
    passed: bool
    fixes: list[CriticFix]

    # Detailed analysis
    contradiction_count: int
    unsupported_claim_count: int
    missing_assumptions: list[str]

    # What would resolve issues
    needed_sources: list[str]
    needed_claims: list[str]

    # Ledger of explicit unknowns
    assumption_ledger: list[Assumption]

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "fixes": [
                {
                    "fix_type": f.fix_type,
                    "target": f.target,
                    "description": f.description,
                    "severity": f.severity,
                }
                for f in self.fixes
            ],
            "contradiction_count": self.contradiction_count,
            "unsupported_claim_count": self.unsupported_claim_count,
            "missing_assumptions": self.missing_assumptions,
            "needed_sources": self.needed_sources,
            "needed_claims": self.needed_claims,
        }
