"""Knowledge substrate indexes for fast retrieval."""

from .lexical import LexicalIndex
from .graph import GraphIndex

__all__ = ["LexicalIndex", "GraphIndex"]
