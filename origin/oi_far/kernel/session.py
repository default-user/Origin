"""OI Kernel - Session management and state transitions."""

import hashlib
import time
import uuid
from typing import Any

from .types import (
    SessionState,
    UserPrefs,
    StyleMode,
    Thread,
    Constraint,
    MemoryHandle,
)


class OIKernel:
    """
    OI Kernel: Manages session state and coordinates pipeline execution.

    All state transitions are explicit and logged for traceability.
    """

    def __init__(self, session_id: str | None = None):
        """Initialize kernel with new or existing session."""
        if session_id is None:
            session_id = self._generate_session_id()

        self.session = SessionState(id=session_id)
        self._add_default_constraints()

    @staticmethod
    def _generate_session_id() -> str:
        """Generate deterministic session ID."""
        # Use timestamp + random for uniqueness
        return f"oi_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    def _add_default_constraints(self) -> None:
        """Add default safety constraints."""
        defaults = [
            Constraint(
                id="c_no_fabrication",
                kind="content",
                description="Never invent facts, sources, or citations",
            ),
            Constraint(
                id="c_fail_closed",
                kind="safety",
                description="Output UNKNOWN if answer cannot be justified from knowledge",
            ),
            Constraint(
                id="c_traceable",
                kind="content",
                description="Every claim must have source provenance",
            ),
            Constraint(
                id="c_deterministic",
                kind="safety",
                description="Same input must produce identical output",
            ),
        ]
        for c in defaults:
            self.session.constraints.append(c)
        self.session.log_transition("add_default_constraints", {
            "count": len(defaults),
        })

    def set_intent(self, intent: str) -> None:
        """Set the current session intent."""
        old_intent = self.session.intent
        self.session.intent = intent
        self.session.log_transition("set_intent", {
            "old": old_intent,
            "new": intent,
        })

    def add_constraint(self, constraint: Constraint) -> None:
        """Add a constraint to the session."""
        self.session.constraints.append(constraint)
        self.session.log_transition("add_constraint", constraint.to_dict())

    def remove_constraint(self, constraint_id: str) -> bool:
        """Remove a constraint by ID."""
        for i, c in enumerate(self.session.constraints):
            if c.id == constraint_id:
                removed = self.session.constraints.pop(i)
                self.session.log_transition("remove_constraint", removed.to_dict())
                return True
        return False

    def add_thread(self, description: str, parent_id: str | None = None) -> Thread:
        """Add a new thread/todo."""
        thread = Thread(
            id=f"t_{len(self.session.threads)}_{int(time.time())}",
            description=description,
            status="pending",
            parent_id=parent_id,
        )
        self.session.threads.append(thread)
        self.session.log_transition("add_thread", thread.to_dict())
        return thread

    def update_thread(self, thread_id: str, status: str) -> bool:
        """Update thread status."""
        for thread in self.session.threads:
            if thread.id == thread_id:
                old_status = thread.status
                thread.status = status
                thread.updated_at = time.time()
                self.session.log_transition("update_thread", {
                    "id": thread_id,
                    "old_status": old_status,
                    "new_status": status,
                })
                return True
        return False

    def set_style(self, mode: StyleMode) -> None:
        """Set output style mode."""
        old_mode = self.session.user_prefs.style_mode
        self.session.user_prefs.style_mode = mode
        self.session.log_transition("set_style", {
            "old": old_mode.value,
            "new": mode.value,
        })

    def store_memory(self, kind: str, content: str, summary: str) -> MemoryHandle:
        """Store a memory handle."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        handle = MemoryHandle(
            id=f"m_{len(self.session.memory_handles)}_{int(time.time())}",
            kind=kind,
            content_hash=content_hash,
            summary=summary,
        )
        self.session.memory_handles.append(handle)
        self.session.log_transition("store_memory", handle.to_dict())
        return handle

    def begin_turn(self, query: str) -> None:
        """Begin a new turn in the session."""
        self.session.turn_count += 1
        self.session.log_transition("begin_turn", {
            "turn": self.session.turn_count,
            "query_hash": hashlib.sha256(query.encode()).hexdigest()[:16],
            "query_length": len(query),
        })

    def end_turn(self, success: bool, output_hash: str) -> None:
        """End the current turn."""
        self.session.log_transition("end_turn", {
            "turn": self.session.turn_count,
            "success": success,
            "output_hash": output_hash,
        })

    def get_active_constraints(self) -> list[Constraint]:
        """Get all active constraints."""
        return [c for c in self.session.constraints if c.active]

    def get_state(self) -> SessionState:
        """Get current session state."""
        return self.session

    def export_state(self) -> dict:
        """Export session state as dictionary."""
        return self.session.to_dict()

    def import_state(self, data: dict) -> None:
        """Import session state from dictionary."""
        self.session = SessionState.from_dict(data)
        self.session.log_transition("import_state", {
            "id": data.get("id"),
            "turn_count": data.get("turn_count", 0),
        })
