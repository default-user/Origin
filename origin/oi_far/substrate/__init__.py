"""MODULE 2: Knowledge Substrate - Document and Brick storage with indexes."""

from .types import Document, Brick, BrickKind, Claim, Definition, Link
from .document_store import DocumentStore
from .brick_store import BrickStore
from .brick_compiler import BrickCompiler

__all__ = [
    "Document",
    "Brick",
    "BrickKind",
    "Claim",
    "Definition",
    "Link",
    "DocumentStore",
    "BrickStore",
    "BrickCompiler",
]
