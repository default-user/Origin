"""Knowledge substrate type definitions."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import hashlib
import json
import time


class BrickKind(Enum):
    """Types of knowledge bricks."""
    CONCEPT = "concept"      # Definition of a concept
    CLAIM = "claim"          # Factual assertion
    PROCEDURE = "procedure"  # How-to knowledge
    EXAMPLE = "example"      # Illustrative example
    CONSTRAINT = "constraint"  # Rule or limitation
    RELATION = "relation"    # Relationship between entities


@dataclass
class Claim:
    """A factual claim within a brick."""
    id: str
    text: str
    confidence: float  # 0.0 to 1.0
    source_refs: list[str] = field(default_factory=list)
    negation: bool = False  # True if this is a negative claim

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "confidence": self.confidence,
            "source_refs": self.source_refs,
            "negation": self.negation,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Claim":
        return cls(
            id=data["id"],
            text=data["text"],
            confidence=data.get("confidence", 1.0),
            source_refs=data.get("source_refs", []),
            negation=data.get("negation", False),
        )


@dataclass
class Definition:
    """A definition within a brick."""
    term: str
    text: str
    scope: str | None = None  # Domain/context for the definition

    def to_dict(self) -> dict:
        return {
            "term": self.term,
            "text": self.text,
            "scope": self.scope,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Definition":
        return cls(
            term=data["term"],
            text=data["text"],
            scope=data.get("scope"),
        )


@dataclass
class Link:
    """A link to another brick or external resource."""
    target_id: str
    relation: str  # "related", "parent", "child", "contradicts", "supports"
    strength: float = 1.0  # 0.0 to 1.0

    def to_dict(self) -> dict:
        return {
            "target_id": self.target_id,
            "relation": self.relation,
            "strength": self.strength,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Link":
        return cls(
            target_id=data["target_id"],
            relation=data["relation"],
            strength=data.get("strength", 1.0),
        )


@dataclass
class Provenance:
    """Source provenance for a brick."""
    source_id: str
    source_type: str  # "document", "pack", "external"
    path: str | None = None
    content_hash: str | None = None
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "path": self.path,
            "content_hash": self.content_hash,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Provenance":
        return cls(
            source_id=data["source_id"],
            source_type=data["source_type"],
            path=data.get("path"),
            content_hash=data.get("content_hash"),
            timestamp=data.get("timestamp", time.time()),
        )


@dataclass
class Brick:
    """
    A meaning-compressed unit of knowledge.

    Bricks are the atomic units of the knowledge substrate.
    Each brick contains claims, definitions, and links with full provenance.
    """
    id: str
    kind: BrickKind
    title: str
    summary: str
    claims: list[Claim] = field(default_factory=list)
    definitions: list[Definition] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    provenance: Provenance | None = None
    confidence: float = 1.0
    last_verified: float = field(default_factory=time.time)
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "summary": self.summary,
            "claims": [c.to_dict() for c in self.claims],
            "definitions": [d.to_dict() for d in self.definitions],
            "links": [l.to_dict() for l in self.links],
            "provenance": self.provenance.to_dict() if self.provenance else None,
            "confidence": self.confidence,
            "last_verified": self.last_verified,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Brick":
        return cls(
            id=data["id"],
            kind=BrickKind(data["kind"]),
            title=data["title"],
            summary=data["summary"],
            claims=[Claim.from_dict(c) for c in data.get("claims", [])],
            definitions=[Definition.from_dict(d) for d in data.get("definitions", [])],
            links=[Link.from_dict(l) for l in data.get("links", [])],
            provenance=Provenance.from_dict(data["provenance"]) if data.get("provenance") else None,
            confidence=data.get("confidence", 1.0),
            last_verified=data.get("last_verified", time.time()),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def content_hash(self) -> str:
        """Deterministic hash of brick content."""
        # Exclude timestamps for content-based hashing
        content = {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "summary": self.summary,
            "claims": [c.to_dict() for c in self.claims],
            "definitions": [d.to_dict() for d in self.definitions],
        }
        data = json.dumps(content, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(data.encode()).hexdigest()[:16]


@dataclass
class Document:
    """A raw document in the document store."""
    id: str
    title: str
    source_path: str | None = None
    source_type: str = "file"  # "file", "url", "pack"
    content: str = ""
    extracted_text: str = ""
    content_hash: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)
    brick_ids: list[str] = field(default_factory=list)  # Bricks derived from this doc

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "source_path": self.source_path,
            "source_type": self.source_type,
            "content": self.content,
            "extracted_text": self.extracted_text,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
            "brick_ids": self.brick_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        return cls(
            id=data["id"],
            title=data["title"],
            source_path=data.get("source_path"),
            source_type=data.get("source_type", "file"),
            content=data.get("content", ""),
            extracted_text=data.get("extracted_text", ""),
            content_hash=data.get("content_hash", ""),
            created_at=data.get("created_at", time.time()),
            updated_at=data.get("updated_at", time.time()),
            metadata=data.get("metadata", {}),
            brick_ids=data.get("brick_ids", []),
        )

    def compute_hash(self) -> str:
        """Compute content hash."""
        self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]
        return self.content_hash
