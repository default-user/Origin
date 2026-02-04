"""Commitment tracking for OI-FAR sessions."""

from dataclasses import dataclass, field
from typing import Any
import time


@dataclass
class Commitment:
    """A commitment made during the session."""
    id: str
    kind: str  # "claim", "action", "constraint"
    description: str
    source_turn: int
    status: str = "active"  # "active", "fulfilled", "violated", "withdrawn"
    evidence: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "description": self.description,
            "source_turn": self.source_turn,
            "status": self.status,
            "evidence": self.evidence,
            "created_at": self.created_at,
        }


class CommitmentTracker:
    """
    Tracks commitments made during a session.

    Commitments include:
    - Claims: factual assertions that must be backed by sources
    - Actions: promised actions that must be completed
    - Constraints: rules that must not be violated
    """

    def __init__(self):
        self.commitments: list[Commitment] = []
        self._counter = 0

    def add_claim(self, description: str, turn: int, evidence: list[str] | None = None) -> Commitment:
        """Add a claim commitment."""
        self._counter += 1
        commitment = Commitment(
            id=f"claim_{self._counter}",
            kind="claim",
            description=description,
            source_turn=turn,
            evidence=evidence or [],
        )
        self.commitments.append(commitment)
        return commitment

    def add_action(self, description: str, turn: int) -> Commitment:
        """Add an action commitment."""
        self._counter += 1
        commitment = Commitment(
            id=f"action_{self._counter}",
            kind="action",
            description=description,
            source_turn=turn,
        )
        self.commitments.append(commitment)
        return commitment

    def fulfill(self, commitment_id: str, evidence: list[str] | None = None) -> bool:
        """Mark a commitment as fulfilled."""
        for c in self.commitments:
            if c.id == commitment_id:
                c.status = "fulfilled"
                if evidence:
                    c.evidence.extend(evidence)
                return True
        return False

    def violate(self, commitment_id: str, reason: str) -> bool:
        """Mark a commitment as violated."""
        for c in self.commitments:
            if c.id == commitment_id:
                c.status = "violated"
                c.evidence.append(f"VIOLATION: {reason}")
                return True
        return False

    def withdraw(self, commitment_id: str, reason: str) -> bool:
        """Withdraw a commitment."""
        for c in self.commitments:
            if c.id == commitment_id:
                c.status = "withdrawn"
                c.evidence.append(f"WITHDRAWN: {reason}")
                return True
        return False

    def get_active(self) -> list[Commitment]:
        """Get all active commitments."""
        return [c for c in self.commitments if c.status == "active"]

    def get_violated(self) -> list[Commitment]:
        """Get all violated commitments."""
        return [c for c in self.commitments if c.status == "violated"]

    def check_consistency(self) -> tuple[bool, list[str]]:
        """
        Check if all commitments are consistent.

        Returns:
            (is_consistent, issues)
        """
        issues = []

        # Check for unfulfilled claims without evidence
        for c in self.commitments:
            if c.kind == "claim" and c.status == "active" and not c.evidence:
                issues.append(f"Claim '{c.id}' has no supporting evidence")

        # Check for violations
        violated = self.get_violated()
        for v in violated:
            issues.append(f"Commitment '{v.id}' was violated: {v.evidence}")

        return len(issues) == 0, issues

    def export(self) -> list[dict]:
        """Export all commitments."""
        return [c.to_dict() for c in self.commitments]
