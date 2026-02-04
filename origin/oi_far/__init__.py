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
    "SessionState",
    "ContextPack",
    "AnswerPlan",
    "OIKernel",
]

from .kernel import SessionState, OIKernel
from .retrieval import ContextPack
from .reasoning import AnswerPlan


def run(query: str, session_id: str | None = None) -> str:
    """
    Main entry point: run a query through OI-FAR pipeline.

    Args:
        query: User query string
        session_id: Optional session ID for continuity

    Returns:
        Rendered response string
    """
    from .cli import execute_query
    return execute_query(query, session_id)
