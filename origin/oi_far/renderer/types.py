"""Renderer types."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RenderMode(Enum):
    """Output rendering modes."""
    GALLEY = "galley"  # Concise, human-scale
    BRIDGE = "bridge"  # Structured with headings/checklists


@dataclass
class RenderConfig:
    """Configuration for rendering."""
    mode: RenderMode = RenderMode.GALLEY
    max_length: int = 2000  # Max characters for galley
    include_sources: bool = True
    include_confidence: bool = False
    include_assumptions: bool = False
    include_unknowns: bool = True


@dataclass
class RenderedOutput:
    """Final rendered output."""
    text: str
    mode: RenderMode
    source_count: int
    has_unknowns: bool
    claim_ids: list[str] = field(default_factory=list)

    # Verification that no new claims were added
    original_claim_count: int = 0
    rendered_claim_count: int = 0
    new_claims_check_passed: bool = True

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "mode": self.mode.value,
            "source_count": self.source_count,
            "has_unknowns": self.has_unknowns,
            "new_claims_check_passed": self.new_claims_check_passed,
        }
