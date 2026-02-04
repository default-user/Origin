"""Test execution tools."""

import subprocess
import time
from pathlib import Path
from typing import Any

from .registry import ToolResult


class TestRunner:
    """
    Run tests in the repository.

    Executes test commands and captures results deterministically.
    """

    def __init__(
        self,
        project_root: str | Path = ".",
        timeout: int = 300,  # 5 minutes default
    ):
        self.project_root = Path(project_root).resolve()
        self.timeout = timeout

    def run_tests(
        self,
        test_command: str | None = None,
        test_path: str | None = None,
    ) -> ToolResult:
        """
        Run tests.

        Args:
            test_command: Custom test command (default: auto-detect)
            test_path: Specific test path to run

        Returns:
            ToolResult with test output
        """
        try:
            # Determine test command
            if test_command:
                cmd = test_command
            else:
                cmd = self._detect_test_command()

            if not cmd:
                return ToolResult(
                    success=False,
                    data=None,
                    error="Could not detect test command",
                )

            # Add specific path if provided
            if test_path:
                cmd = f"{cmd} {test_path}"

            # Run tests
            start_time = time.time()

            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            duration = time.time() - start_time

            # Parse output
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            return ToolResult(
                success=True,
                data={
                    "passed": passed,
                    "return_code": result.returncode,
                    "output": output[-10000:],  # Limit output size
                    "duration_seconds": duration,
                    "command": cmd,
                },
                deterministic=False,  # Test results can vary
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                data=None,
                error=f"Test timeout after {self.timeout} seconds",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    def _detect_test_command(self) -> str | None:
        """Detect the appropriate test command."""
        # Check for package.json (Node.js)
        if (self.project_root / "package.json").exists():
            return "npm test"

        # Check for pytest
        if (self.project_root / "pytest.ini").exists() or \
           (self.project_root / "pyproject.toml").exists():
            return "pytest"

        # Check for Cargo.toml (Rust)
        if (self.project_root / "Cargo.toml").exists():
            return "cargo test"

        # Check for go.mod (Go)
        if (self.project_root / "go.mod").exists():
            return "go test ./..."

        # Default for Python
        if (self.project_root / "setup.py").exists() or \
           any(self.project_root.glob("*.py")):
            return "python -m pytest"

        return None

    def run_golden_tests(self, golden_path: str | None = None) -> ToolResult:
        """
        Run golden tests specifically.

        Golden tests compare output against expected results.
        """
        try:
            golden_dir = Path(golden_path) if golden_path else \
                         self.project_root / "tests" / "golden"

            if not golden_dir.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Golden test directory not found: {golden_dir}",
                )

            # Run with npm if package.json exists
            if (self.project_root / "package.json").exists():
                cmd = "npm run test"
            else:
                cmd = f"python -m pytest {golden_dir}"

            result = subprocess.run(
                cmd,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )

            return ToolResult(
                success=True,
                data={
                    "passed": result.returncode == 0,
                    "output": result.stdout + result.stderr,
                    "command": cmd,
                },
                deterministic=False,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


def run_tests(
    project_root: str = ".",
    test_command: str | None = None,
) -> ToolResult:
    """Tool function for running tests."""
    runner = TestRunner(project_root)
    return runner.run_tests(test_command)
