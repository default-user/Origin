"""MODULE 6: Tooling Interface (capability-gated tools)."""

from .files import FileAccessor, open_file
from .registry import Tool, ToolCapability, ToolRegistry, ToolResult
from .sandbox import CodeSandbox, execute_code_sandboxed
from .tests import TestRunner, run_tests
from .vault import VaultSearcher, search_vault

__all__ = [
    # Registry
    "ToolRegistry",
    "Tool",
    "ToolResult",
    "ToolCapability",
    # Tools
    "search_vault",
    "open_file",
    "run_tests",
    "execute_code_sandboxed",
    # Classes
    "VaultSearcher",
    "FileAccessor",
    "TestRunner",
    "CodeSandbox",
]


def create_default_registry(vault_path: str = ".") -> ToolRegistry:
    """Create a registry with default tools."""
    registry = ToolRegistry(
        granted_capabilities=[ToolCapability.READ]
    )

    # Register vault search
    registry.register(
        name="search_vault",
        description="Search the local knowledge vault",
        handler=lambda query, limit=10: search_vault(query, vault_path, limit),
        capabilities=[ToolCapability.READ],
        deterministic=True,
    )

    # Register file access
    registry.register(
        name="open_file",
        description="Open and read a file",
        handler=lambda path: open_file(path, [vault_path]),
        capabilities=[ToolCapability.READ],
        deterministic=True,
    )

    # Register test runner (requires EXECUTE)
    registry.register(
        name="run_tests",
        description="Run project tests",
        handler=lambda: run_tests(vault_path),
        capabilities=[ToolCapability.EXECUTE],
        deterministic=False,
    )

    # Register code sandbox (requires EXECUTE)
    registry.register(
        name="execute_code",
        description="Execute code in a sandbox",
        handler=execute_code_sandboxed,
        capabilities=[ToolCapability.EXECUTE],
        deterministic=True,
    )

    return registry
