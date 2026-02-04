"""Retrieval pipeline types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ConflictType(Enum):
    """Types of conflicts detected during retrieval."""
    CONTRADICTION = "contradiction"  # Direct logical contradiction
    INCONSISTENCY = "inconsistency"  # Values don't match
    TEMPORAL = "temporal"  # Timeline conflicts
    SOURCE = "source"  # Sources disagree


@dataclass
class RetrievedBrick:
    """A brick retrieved with scoring information."""
    brick_id: str
    title: str
    summary: str
    claims: list[str]
    score: float
    score_breakdown: dict[str, float]
    provenance: dict[str, Any]
    confidence: float


@dataclass
class RetrievedSource:
    """A source document retrieved."""
    source_id: str
    title: str
    relevance_score: float
    excerpt: str
    path: str | None = None


@dataclass
class Conflict:
    """A detected conflict between retrieved items."""
    conflict_type: ConflictType
    item1_id: str
    item2_id: str
    description: str
    resolution_hint: str | None = None


@dataclass
class KnownUnknown:
    """Something we know we don't know."""
    topic: str
    question: str
    what_would_help: list[str]
    confidence_if_resolved: float = 0.0


@dataclass
class ActiveConstraint:
    """An active constraint from session state."""
    constraint_id: str
    description: str
    source: str  # "user", "system", "inferred"


@dataclass
class ContextPack:
    """
    Complete context package for reasoning.

    This is the output of the retrieval pipeline and input to the reasoning core.
    All fields are deterministically computed from the query and knowledge base.
    """
    # Query information
    query: str
    query_tokens: list[str]
    query_intent: str  # "define", "explain", "compare", "find", "prove", "unknown"

    # Retrieved content
    top_bricks: list[RetrievedBrick]
    top_sources: list[RetrievedSource]

    # Knowledge gaps and conflicts
    known_unknowns: list[KnownUnknown]
    conflicts: list[Conflict]

    # Session context
    active_constraints: list[ActiveConstraint]
    relevant_commitments: list[str]  # Commitment IDs

    # Metadata
    retrieval_timestamp: float = 0.0
    total_bricks_scanned: int = 0
    total_sources_scanned: int = 0

    def has_sufficient_context(self) -> bool:
        """Check if we have enough context to proceed."""
        return len(self.top_bricks) > 0 or len(self.top_sources) > 0

    def has_conflicts(self) -> bool:
        """Check if there are unresolved conflicts."""
        return len(self.conflicts) > 0

    def get_all_claims(self) -> list[str]:
        """Get all claims from retrieved bricks."""
        claims = []
        for brick in self.top_bricks:
            claims.extend(brick.claims)
        return claims

    def get_confidence_weighted_claims(self) -> list[tuple[str, float]]:
        """Get claims weighted by brick confidence and retrieval score."""
        weighted = []
        for brick in self.top_bricks:
            combined_confidence = brick.confidence * brick.score
            for claim in brick.claims:
                weighted.append((claim, combined_confidence))
        return sorted(weighted, key=lambda x: -x[1])

    def to_dict(self) -> dict:
        """Export to dictionary for serialization."""
        return {
            "query": self.query,
            "query_tokens": self.query_tokens,
            "query_intent": self.query_intent,
            "top_bricks": [
                {
                    "brick_id": b.brick_id,
                    "title": b.title,
                    "score": b.score,
                    "claims": b.claims,
                }
                for b in self.top_bricks
            ],
            "top_sources": [
                {
                    "source_id": s.source_id,
                    "title": s.title,
                    "relevance_score": s.relevance_score,
                }
                for s in self.top_sources
            ],
            "known_unknowns": [
                {
                    "topic": u.topic,
                    "question": u.question,
                    "what_would_help": u.what_would_help,
                }
                for u in self.known_unknowns
            ],
            "conflicts": [
                {
                    "type": c.conflict_type.value,
                    "items": [c.item1_id, c.item2_id],
                    "description": c.description,
                }
                for c in self.conflicts
            ],
            "has_sufficient_context": self.has_sufficient_context(),
            "total_bricks_scanned": self.total_bricks_scanned,
        }
