#!/usr/bin/env python3
"""
OI-FAR Proxy - Interface layer for proxying requests through OI-FAR.

This module provides a conversational proxy interface to OI-FAR, allowing
an external agent (like Claude) to act as a proxy that routes queries
through the deterministic OI-FAR pipeline.

Usage:
    from origin.oi_far.proxy import OIFarProxy

    proxy = OIFarProxy()
    result = proxy.query("What is the Holodeck?")
    print(result)
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, TYPE_CHECKING

from .renderer import RenderMode

if TYPE_CHECKING:
    from .cli import OIFarRuntime


class ProxyMode(Enum):
    """Proxy operation modes."""
    QUERY = "query"          # Standard query-response
    SEARCH = "search"        # Search vault only
    EXPLAIN = "explain"      # Detailed explanation with sources
    VERIFY = "verify"        # Verify a claim
    COMPARE = "compare"      # Compare concepts


@dataclass
class ProxyRequest:
    """Request to the OI-FAR proxy."""
    content: str
    mode: ProxyMode = ProxyMode.QUERY
    include_sources: bool = True
    include_confidence: bool = True
    bridge_mode: bool = False
    max_results: int = 10
    metadata: dict = field(default_factory=dict)


@dataclass
class ProxyResponse:
    """Response from the OI-FAR proxy."""
    output: str
    status: str
    confidence: float
    sources: list
    deterministic: bool
    critic_passed: bool
    mode: str
    timing_ms: float
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "output": self.output,
            "status": self.status,
            "confidence": self.confidence,
            "sources": self.sources,
            "deterministic": self.deterministic,
            "critic_passed": self.critic_passed,
            "mode": self.mode,
            "timing_ms": self.timing_ms,
            "metadata": self.metadata,
        }

    def __str__(self) -> str:
        lines = [self.output]

        if self.sources:
            lines.append("")
            lines.append("Sources:")
            for src in self.sources[:5]:
                if isinstance(src, dict):
                    lines.append(f"  - {src.get('title', src.get('id', 'unknown'))}")
                else:
                    lines.append(f"  - {src}")

        if self.confidence < 1.0:
            lines.append("")
            lines.append(f"Confidence: {self.confidence:.0%}")

        if self.status != "complete":
            lines.append(f"Status: {self.status}")

        return "\n".join(lines)


class OIFarProxy:
    """
    Proxy interface to OI-FAR.

    Acts as an intermediary between an external agent and the OI-FAR
    deterministic intelligence pipeline. Provides:

    - Query routing through deterministic retrieval + reasoning
    - Source attribution for all answers
    - Confidence scoring
    - Fail-closed semantics (returns UNKNOWN rather than fabricating)

    Example:
        proxy = OIFarProxy()

        # Simple query
        response = proxy.query("What is determinism in computing?")
        print(response)

        # Search only
        results = proxy.search("determinism")

        # Verify a claim
        result = proxy.verify("All OI-FAR outputs are deterministic")
    """

    def __init__(
        self,
        vault_path: str | Path = ".",
        default_bridge_mode: bool = False,
    ):
        """
        Initialize the OI-FAR proxy.

        Args:
            vault_path: Path to the knowledge vault
            default_bridge_mode: Use bridge mode by default (structured output)
        """
        self.vault_path = Path(vault_path).resolve()
        self.default_bridge_mode = default_bridge_mode
        self._runtime = None
        self._bridge_runtime = None

    def _get_runtime(self, bridge_mode: bool = False) -> "OIFarRuntime":
        """Get or create runtime instance."""
        from .cli import OIFarRuntime
        if bridge_mode:
            if self._bridge_runtime is None:
                self._bridge_runtime = OIFarRuntime(
                    vault_path=self.vault_path,
                    mode=RenderMode.BRIDGE,
                )
            return self._bridge_runtime
        else:
            if self._runtime is None:
                self._runtime = OIFarRuntime(
                    vault_path=self.vault_path,
                    mode=RenderMode.GALLEY,
                )
            return self._runtime

    def query(
        self,
        content: str,
        bridge_mode: bool | None = None,
    ) -> ProxyResponse:
        """
        Run a query through OI-FAR.

        Args:
            content: The query text
            bridge_mode: Use structured output (None = use default)

        Returns:
            ProxyResponse with answer and metadata
        """
        if bridge_mode is None:
            bridge_mode = self.default_bridge_mode

        runtime = self._get_runtime(bridge_mode)
        result = runtime.run(content)

        return ProxyResponse(
            output=result["output"],
            status=result["status"],
            confidence=result["confidence"],
            sources=result["sources"],
            deterministic=result["deterministic"],
            critic_passed=result["critic_passed"],
            mode=result["mode"],
            timing_ms=result["timing"]["total_ms"],
        )

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search the knowledge vault.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching bricks
        """
        runtime = self._get_runtime()
        result = runtime.search(query, limit=limit)

        if result.get("success"):
            return result["data"]["results"]
        return []

    def verify(self, claim: str) -> ProxyResponse:
        """
        Verify a claim against the knowledge vault.

        Args:
            claim: The claim to verify

        Returns:
            ProxyResponse with verification result
        """
        # Frame as verification query
        query = f"Verify the following claim: {claim}"
        return self.query(query)

    def explain(self, topic: str) -> ProxyResponse:
        """
        Get a detailed explanation of a topic.

        Args:
            topic: The topic to explain

        Returns:
            ProxyResponse with explanation
        """
        query = f"Explain: {topic}"
        return self.query(query, bridge_mode=True)

    def compare(self, concept_a: str, concept_b: str) -> ProxyResponse:
        """
        Compare two concepts.

        Args:
            concept_a: First concept
            concept_b: Second concept

        Returns:
            ProxyResponse with comparison
        """
        query = f"Compare {concept_a} and {concept_b}"
        return self.query(query, bridge_mode=True)

    def process(self, request: ProxyRequest) -> ProxyResponse:
        """
        Process a structured proxy request.

        Args:
            request: ProxyRequest with query and options

        Returns:
            ProxyResponse with result
        """
        if request.mode == ProxyMode.SEARCH:
            results = self.search(request.content, limit=request.max_results)
            return ProxyResponse(
                output=json.dumps(results, indent=2),
                status="complete",
                confidence=1.0,
                sources=[],
                deterministic=True,
                critic_passed=True,
                mode="search",
                timing_ms=0,
            )
        elif request.mode == ProxyMode.VERIFY:
            return self.verify(request.content)
        elif request.mode == ProxyMode.EXPLAIN:
            return self.explain(request.content)
        elif request.mode == ProxyMode.COMPARE:
            # Parse "A vs B" or "A and B"
            parts = request.content.replace(" vs ", " and ").split(" and ")
            if len(parts) >= 2:
                return self.compare(parts[0].strip(), parts[1].strip())
            return self.query(request.content, bridge_mode=request.bridge_mode)
        else:
            return self.query(request.content, bridge_mode=request.bridge_mode)

    def get_status(self) -> dict:
        """Get proxy status information."""
        runtime = self._get_runtime()
        return {
            "vault_path": str(self.vault_path),
            "brick_count": runtime.brick_store.count(),
            "document_count": runtime.document_store.count(),
            "session_turns": len(runtime._history),
            "default_mode": "bridge" if self.default_bridge_mode else "galley",
        }


# Singleton proxy instance for convenience
_proxy_instance: OIFarProxy | None = None


def get_proxy(vault_path: str = ".") -> OIFarProxy:
    """Get or create the singleton proxy instance."""
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OIFarProxy(vault_path=vault_path)
    return _proxy_instance


def proxy_query(query: str, vault_path: str = ".") -> str:
    """
    Convenience function to run a query through OI-FAR proxy.

    Args:
        query: The query to run
        vault_path: Path to knowledge vault

    Returns:
        Answer string
    """
    proxy = get_proxy(vault_path)
    response = proxy.query(query)
    return str(response)


# Interactive proxy for REPL usage
def interactive_proxy(vault_path: str = "."):
    """
    Start an interactive OI-FAR proxy session.

    Commands:
        /search <query>  - Search the vault
        /verify <claim>  - Verify a claim
        /explain <topic> - Detailed explanation
        /compare <a> and <b> - Compare concepts
        /status          - Show proxy status
        /quit            - Exit
    """
    import sys

    print("OI-FAR Proxy - Deterministic Intelligence Interface")
    print("Type /help for commands, /quit to exit")
    print()

    proxy = OIFarProxy(vault_path=vault_path)

    while True:
        try:
            user_input = input("proxy> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not user_input:
            continue

        if user_input.startswith("/"):
            cmd_parts = user_input[1:].split(maxsplit=1)
            cmd = cmd_parts[0].lower()
            arg = cmd_parts[1] if len(cmd_parts) > 1 else ""

            if cmd in ("quit", "exit", "q"):
                break
            elif cmd == "help":
                print(interactive_proxy.__doc__)
            elif cmd == "status":
                status = proxy.get_status()
                for k, v in status.items():
                    print(f"  {k}: {v}")
            elif cmd == "search" and arg:
                results = proxy.search(arg)
                for r in results:
                    print(f"  [{r.get('score', 0):.1f}] {r.get('title', r.get('id'))}")
            elif cmd == "verify" and arg:
                response = proxy.verify(arg)
                print(response)
            elif cmd == "explain" and arg:
                response = proxy.explain(arg)
                print(response)
            elif cmd == "compare" and arg:
                response = proxy.compare(*arg.split(" and ")[:2])
                print(response)
            else:
                print(f"Unknown command: {cmd}")
        else:
            # Regular query
            response = proxy.query(user_input)
            print(response)

        print()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Run a single query
        query = " ".join(sys.argv[1:])
        print(proxy_query(query))
    else:
        # Start interactive mode
        interactive_proxy()
