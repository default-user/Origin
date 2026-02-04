"""File access tools."""

import os
from pathlib import Path
from typing import Any

from .registry import ToolResult


class FileAccessor:
    """
    Safe file access within allowed paths.

    Enforces path restrictions and provides deterministic file access.
    """

    def __init__(self, allowed_roots: list[str | Path] | None = None):
        """
        Initialize file accessor.

        Args:
            allowed_roots: List of allowed root directories.
                          If None, current directory is used.
        """
        if allowed_roots:
            self.allowed_roots = [Path(r).resolve() for r in allowed_roots]
        else:
            self.allowed_roots = [Path.cwd()]

    def _is_allowed(self, path: Path) -> bool:
        """Check if path is within allowed roots."""
        resolved = path.resolve()
        return any(
            resolved == root or root in resolved.parents
            for root in self.allowed_roots
        )

    def open_file(self, path: str, max_size: int = 1024 * 1024) -> ToolResult:
        """
        Open and read a file.

        Args:
            path: File path
            max_size: Maximum file size in bytes (default 1MB)

        Returns:
            ToolResult with file content
        """
        try:
            file_path = Path(path)

            # Security check
            if not self._is_allowed(file_path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path not allowed: {path}",
                )

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {path}",
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Not a file: {path}",
                )

            # Size check
            size = file_path.stat().st_size
            if size > max_size:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File too large: {size} bytes (max {max_size})",
                )

            # Read file
            content = file_path.read_text(encoding="utf-8")

            return ToolResult(
                success=True,
                data={
                    "path": str(file_path),
                    "content": content,
                    "size": size,
                    "extension": file_path.suffix,
                },
                deterministic=True,
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                data=None,
                error=f"Cannot decode file as UTF-8: {path}",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    def list_directory(self, path: str, pattern: str = "*") -> ToolResult:
        """
        List directory contents.

        Args:
            path: Directory path
            pattern: Glob pattern for filtering

        Returns:
            ToolResult with file listing
        """
        try:
            dir_path = Path(path)

            # Security check
            if not self._is_allowed(dir_path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path not allowed: {path}",
                )

            if not dir_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Directory not found: {path}",
                )

            if not dir_path.is_dir():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Not a directory: {path}",
                )

            # List contents
            entries = []
            for entry in sorted(dir_path.glob(pattern)):
                entries.append({
                    "name": entry.name,
                    "path": str(entry),
                    "is_dir": entry.is_dir(),
                    "size": entry.stat().st_size if entry.is_file() else None,
                })

            return ToolResult(
                success=True,
                data={
                    "path": str(dir_path),
                    "entries": entries,
                    "count": len(entries),
                },
                deterministic=True,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    def file_exists(self, path: str) -> ToolResult:
        """Check if a file exists."""
        try:
            file_path = Path(path)

            if not self._is_allowed(file_path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path not allowed: {path}",
                )

            exists = file_path.exists()
            is_file = file_path.is_file() if exists else False

            return ToolResult(
                success=True,
                data={
                    "exists": exists,
                    "is_file": is_file,
                    "path": str(file_path),
                },
                deterministic=True,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


def open_file(path: str, allowed_roots: list[str] | None = None) -> ToolResult:
    """Tool function for opening files."""
    accessor = FileAccessor(allowed_roots)
    return accessor.open_file(path)
