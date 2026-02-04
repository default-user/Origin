"""MODULE 5: Renderer (deterministic output generation)."""

from .claim_checker import ClaimChecker
from .renderer import DeterministicRenderer
from .templates import BridgeTemplate, FailedTemplate, GalleyTemplate
from .types import RenderConfig, RenderedOutput, RenderMode

__all__ = [
    "DeterministicRenderer",
    "RenderConfig",
    "RenderMode",
    "RenderedOutput",
    "ClaimChecker",
    "GalleyTemplate",
    "BridgeTemplate",
    "FailedTemplate",
]
