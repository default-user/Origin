"""
OI-FAR: Ongoing-Intelligence Frontier Approximation Runtime

Deterministic intelligence system that approximates frontier LLM capability surface
using explicit knowledge + deterministic retrieval + deterministic planning/solving
+ audited rendering.

Core principles:
- Deterministic-first: core planning/reasoning uses deterministic algorithms
- Fail-closed: output UNKNOWN when answer cannot be justified
- Traceability: every answer reconstructable from sources + transforms
- No fabrication: never invent facts, sources, or citations
- Safety/integrity: sandboxed execution, capability-gated tools
"""

__version__ = "0.1.0"
__all__ = [
    "run",
    "OIFarRuntime",
    "SessionState",
    "ContextPack",
    "AnswerPlan",
]

from .kernel import SessionState
from .retrieval import ContextPack
from .reasoning import AnswerPlan


def run(query: str, vault_path: str = ".", mode: str = "galley") -> dict:
    """
    Main entry point: run a query through OI-FAR pipeline.

    Args:
        query: User query string
        vault_path: Path to knowledge vault
        mode: Output mode ("galley" or "bridge")

    Returns:
        Result dictionary with output and metadata
    """
    from .cli import OIFarRuntime
    from .renderer import RenderMode

    render_mode = RenderMode.BRIDGE if mode == "bridge" else RenderMode.GALLEY
    runtime = OIFarRuntime(vault_path=vault_path, mode=render_mode)
    return runtime.run(query)


def get_runtime(vault_path: str = "."):
    """Get an OI-FAR runtime instance."""
    from .cli import OIFarRuntime
    return OIFarRuntime(vault_path=vault_path)
