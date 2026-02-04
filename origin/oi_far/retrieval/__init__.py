"""MODULE 3: Retrieval Pipeline (deterministic RAG)."""

from .retriever import DeterministicRetriever
from .scoring import DeterministicScorer, ScoringWeights
from .types import (
    ActiveConstraint,
    Conflict,
    ConflictType,
    ContextPack,
    KnownUnknown,
    RetrievedBrick,
    RetrievedSource,
)

__all__ = [
    "DeterministicRetriever",
    "DeterministicScorer",
    "ScoringWeights",
    "ContextPack",
    "RetrievedBrick",
    "RetrievedSource",
    "Conflict",
    "ConflictType",
    "KnownUnknown",
    "ActiveConstraint",
]
