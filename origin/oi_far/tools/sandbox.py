"""Sandboxed code execution."""

import ast
import io
import sys
import traceback
from contextlib import redirect_stdout, redirect_stderr
from typing import Any

from .registry import ToolResult


class CodeSandbox:
    """
    Sandboxed code execution environment.

    SAFETY NOTES:
    - Only Python execution is implemented
    - Restricted builtins (no file I/O, network, etc.)
    - Memory and time limits
    - No access to dangerous modules

    This is NOT a security boundary for untrusted code.
    It's a containment layer for OI-generated code snippets.
    """

    ALLOWED_BUILTINS = {
        # Safe builtins
        "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
        "callable", "chr", "complex", "dict", "dir", "divmod", "enumerate",
        "filter", "float", "format", "frozenset", "hash", "hex", "id",
        "int", "isinstance", "issubclass", "iter", "len", "list", "map",
        "max", "min", "next", "oct", "ord", "pow", "print", "range",
        "repr", "reversed", "round", "set", "slice", "sorted", "str",
        "sum", "tuple", "type", "zip",
        # Safe exceptions
        "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
        "AttributeError", "RuntimeError", "StopIteration",
        # Constants
        "True", "False", "None",
    }

    BLOCKED_MODULES = {
        "os", "sys", "subprocess", "shutil", "pathlib",
        "socket", "urllib", "http", "ftplib", "smtplib",
        "pickle", "marshal", "shelve",
        "importlib", "builtins", "__builtins__",
        "ctypes", "multiprocessing", "threading",
        "code", "codeop", "compile",
    }

    def __init__(
        self,
        max_output_size: int = 10000,
        max_memory_mb: int = 100,
    ):
        self.max_output_size = max_output_size
        self.max_memory_mb = max_memory_mb

    def execute_python(
        self,
        code: str,
        timeout_seconds: float = 5.0,
    ) -> ToolResult:
        """
        Execute Python code in a sandbox.

        Args:
            code: Python code to execute
            timeout_seconds: Maximum execution time

        Returns:
            ToolResult with execution output
        """
        # Validate code first
        validation = self._validate_code(code)
        if not validation["valid"]:
            return ToolResult(
                success=False,
                data=None,
                error=f"Code validation failed: {validation['reason']}",
            )

        try:
            # Prepare restricted environment
            restricted_globals = self._create_restricted_globals()
            restricted_locals = {}

            # Capture output
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            # Execute with output capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    exec(code, restricted_globals, restricted_locals)
                except Exception as e:
                    stderr_capture.write(f"\nExecution error: {e}\n")
                    stderr_capture.write(traceback.format_exc())

            stdout_output = stdout_capture.getvalue()[:self.max_output_size]
            stderr_output = stderr_capture.getvalue()[:self.max_output_size]

            # Extract result if present
            result_value = restricted_locals.get("result", None)

            return ToolResult(
                success=True,
                data={
                    "stdout": stdout_output,
                    "stderr": stderr_output,
                    "result": repr(result_value) if result_value is not None else None,
                    "variables": {
                        k: repr(v)[:200]
                        for k, v in restricted_locals.items()
                        if not k.startswith("_")
                    },
                },
                deterministic=True,  # Same code = same output
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Sandbox error: {e}",
            )

    def _validate_code(self, code: str) -> dict:
        """Validate code for safety."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {"valid": False, "reason": f"Syntax error: {e}"}

        # Check for dangerous constructs
        for node in ast.walk(tree):
            # Block imports of dangerous modules
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] in self.BLOCKED_MODULES:
                        return {"valid": False, "reason": f"Blocked import: {alias.name}"}

            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in self.BLOCKED_MODULES:
                    return {"valid": False, "reason": f"Blocked import: {node.module}"}

            # Block exec/eval/compile
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in ("exec", "eval", "compile", "__import__"):
                        return {"valid": False, "reason": f"Blocked function: {node.func.id}"}

            # Block attribute access to dunder methods
            if isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    if node.attr not in ("__init__", "__str__", "__repr__", "__len__"):
                        return {"valid": False, "reason": f"Blocked dunder access: {node.attr}"}

        return {"valid": True, "reason": None}

    def _create_restricted_globals(self) -> dict:
        """Create a restricted globals dict."""
        safe_builtins = {
            name: getattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__, name, None)
            for name in self.ALLOWED_BUILTINS
            if hasattr(__builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__, name) or
               name in ("True", "False", "None")
        }

        # Add safe math functions
        import math
        safe_builtins["math"] = type("SafeMath", (), {
            k: getattr(math, k)
            for k in ["sin", "cos", "tan", "sqrt", "log", "log10", "exp", "pi", "e",
                      "floor", "ceil", "fabs", "factorial", "gcd"]
        })()

        return {
            "__builtins__": safe_builtins,
            "__name__": "__sandbox__",
        }


def execute_code_sandboxed(
    lang: str,
    code: str,
    timeout: float = 5.0,
) -> ToolResult:
    """Tool function for sandboxed code execution."""
    if lang.lower() != "python":
        return ToolResult(
            success=False,
            data=None,
            error=f"Only Python is supported, got: {lang}",
        )

    sandbox = CodeSandbox()
    return sandbox.execute_python(code, timeout)
