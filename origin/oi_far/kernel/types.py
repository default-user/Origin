"""Kernel type definitions for OI-FAR."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib
import json
import time


class StyleMode(Enum):
    """Output style modes."""
    GALLEY = "galley"    # Concise, human-scale
    BRIDGE = "bridge"    # Structured, headings/checklists


@dataclass
class Constraint:
    """An active constraint on the session."""
    id: str
    kind: str  # "format", "content", "scope", "safety"
    description: str
    active: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "description": self.description,
            "active": self.active,
        }


@dataclass
class Thread:
    """A tracked thread/todo in the session."""
    id: str
    description: str
    status: str  # "pending", "in_progress", "completed", "blocked"
    parent_id: str | None = None
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "description": self.description,
            "status": self.status,
            "parent_id": self.parent_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class MemoryHandle:
    """Reference to stored memory/context."""
    id: str
    kind: str  # "fact", "preference", "context"
    content_hash: str
    summary: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "content_hash": self.content_hash,
            "summary": self.summary,
            "created_at": self.created_at,
        }


@dataclass
class UserPrefs:
    """User preferences for the session."""
    style_mode: StyleMode = StyleMode.GALLEY
    verbosity: int = 1  # 0=minimal, 1=normal, 2=detailed
    show_sources: bool = True
    show_confidence: bool = False
    max_response_length: int = 2000

    def to_dict(self) -> dict:
        return {
            "style_mode": self.style_mode.value,
            "verbosity": self.verbosity,
            "show_sources": self.show_sources,
            "show_confidence": self.show_confidence,
            "max_response_length": self.max_response_length,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserPrefs":
        return cls(
            style_mode=StyleMode(data.get("style_mode", "galley")),
            verbosity=data.get("verbosity", 1),
            show_sources=data.get("show_sources", True),
            show_confidence=data.get("show_confidence", False),
            max_response_length=data.get("max_response_length", 2000),
        )


@dataclass
class SessionState:
    """Complete session state for OI-FAR kernel."""
    id: str
    intent: str | None = None
    constraints: list[Constraint] = field(default_factory=list)
    threads: list[Thread] = field(default_factory=list)
    user_prefs: UserPrefs = field(default_factory=UserPrefs)
    memory_handles: list[MemoryHandle] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    turn_count: int = 0

    # Transition log for traceability
    transitions: list[dict] = field(default_factory=list)

    # Commitment tracker (set by OIKernel)
    commitment_tracker: Any = None

    def __post_init__(self):
        """Initialize commitment tracker if not set."""
        if self.commitment_tracker is None:
            from .commitments import CommitmentTracker
            self.commitment_tracker = CommitmentTracker()

    def to_dict(self) -> dict:
        """Serialize to dictionary (deterministic)."""
        return {
            "id": self.id,
            "intent": self.intent,
            "constraints": [c.to_dict() for c in self.constraints],
            "threads": [t.to_dict() for t in self.threads],
            "user_prefs": self.user_prefs.to_dict(),
            "memory_handles": [m.to_dict() for m in self.memory_handles],
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "turn_count": self.turn_count,
            "transitions": self.transitions,
        }

    def content_hash(self) -> str:
        """Deterministic hash of session state."""
        # Sort keys for determinism
        data = json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Deserialize from dictionary."""
        return cls(
            id=data["id"],
            intent=data.get("intent"),
            constraints=[
                Constraint(**c) for c in data.get("constraints", [])
            ],
            threads=[Thread(**t) for t in data.get("threads", [])],
            user_prefs=UserPrefs.from_dict(data.get("user_prefs", {})),
            memory_handles=[
                MemoryHandle(**m) for m in data.get("memory_handles", [])
            ],
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            turn_count=data.get("turn_count", 0),
            transitions=data.get("transitions", []),
        )

    def log_transition(self, action: str, details: dict[str, Any]) -> None:
        """Log a state transition for traceability."""
        self.transitions.append({
            "timestamp": time.time(),
            "turn": self.turn_count,
            "action": action,
            "details": details,
            "state_hash": self.content_hash(),
        })
        self.updated_at = time.time()
