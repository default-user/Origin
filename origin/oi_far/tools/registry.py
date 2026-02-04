"""Capability-gated tool registry."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
import time


class ToolCapability(Enum):
    """Tool capability levels."""
    READ = "read"  # Read-only access
    WRITE = "write"  # Can modify state
    EXECUTE = "execute"  # Can run code
    NETWORK = "network"  # Can access network


@dataclass
class ToolResult:
    """Result from a tool invocation."""
    success: bool
    data: Any
    error: str | None = None
    cached: bool = False
    timestamp: float = field(default_factory=time.time)
    deterministic: bool = True  # False if result may vary

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "cached": self.cached,
            "deterministic": self.deterministic,
        }


@dataclass
class Tool:
    """A registered tool."""
    name: str
    description: str
    capabilities_required: list[ToolCapability]
    handler: Callable[..., ToolResult]
    deterministic: bool = True
    cacheable: bool = True


class ToolRegistry:
    """
    Capability-gated tool registry.

    Tools are registered with required capabilities.
    Invocations are checked against granted capabilities.
    Results are cached for determinism where possible.
    """

    def __init__(self, granted_capabilities: list[ToolCapability] | None = None):
        self.granted = set(granted_capabilities or [ToolCapability.READ])
        self._tools: dict[str, Tool] = {}
        self._cache: dict[str, ToolResult] = {}
        self._invocation_log: list[dict] = []

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[..., ToolResult],
        capabilities: list[ToolCapability],
        deterministic: bool = True,
        cacheable: bool = True,
    ) -> None:
        """Register a tool."""
        self._tools[name] = Tool(
            name=name,
            description=description,
            capabilities_required=capabilities,
            handler=handler,
            deterministic=deterministic,
            cacheable=cacheable,
        )

    def invoke(
        self,
        name: str,
        **kwargs,
    ) -> ToolResult:
        """
        Invoke a tool by name.

        Args:
            name: Tool name
            **kwargs: Tool arguments

        Returns:
            ToolResult
        """
        # Check tool exists
        if name not in self._tools:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool not found: {name}",
            )

        tool = self._tools[name]

        # Check capabilities
        missing = set(tool.capabilities_required) - self.granted
        if missing:
            return ToolResult(
                success=False,
                data=None,
                error=f"Missing capabilities: {[c.value for c in missing]}",
            )

        # Check cache
        cache_key = self._make_cache_key(name, kwargs)
        if tool.cacheable and cache_key in self._cache:
            cached = self._cache[cache_key]
            return ToolResult(
                success=cached.success,
                data=cached.data,
                error=cached.error,
                cached=True,
                deterministic=cached.deterministic,
            )

        # Invoke
        try:
            result = tool.handler(**kwargs)

            # Cache if appropriate
            if tool.cacheable and result.success:
                self._cache[cache_key] = result

            # Log invocation
            self._invocation_log.append({
                "tool": name,
                "args": kwargs,
                "success": result.success,
                "timestamp": time.time(),
            })

            return result

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    def _make_cache_key(self, name: str, kwargs: dict) -> str:
        """Create deterministic cache key."""
        # Sort kwargs for determinism
        sorted_items = sorted(kwargs.items())
        return f"{name}:{sorted_items}"

    def list_tools(self) -> list[dict]:
        """List all registered tools."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "capabilities": [c.value for c in t.capabilities_required],
                "deterministic": t.deterministic,
                "available": all(c in self.granted for c in t.capabilities_required),
            }
            for t in self._tools.values()
        ]

    def grant_capability(self, capability: ToolCapability) -> None:
        """Grant a capability."""
        self.granted.add(capability)

    def revoke_capability(self, capability: ToolCapability) -> None:
        """Revoke a capability."""
        self.granted.discard(capability)

    def clear_cache(self) -> None:
        """Clear the result cache."""
        self._cache.clear()

    def get_invocation_log(self) -> list[dict]:
        """Get the invocation log."""
        return self._invocation_log.copy()
