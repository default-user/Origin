"""Optional semantic index (deterministic given fixed model/version)."""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..types import Brick


@dataclass
class SemanticHit:
    """A hit from semantic search."""
    brick_id: str
    score: float
    embedding_hash: str


class SemanticIndex:
    """
    Optional semantic embedding index.

    This is ONLY deterministic if:
    1. A fixed embedding model/version is used
    2. The model produces deterministic outputs

    For strict determinism, prefer LexicalIndex.
    This class is a placeholder for optional semantic capabilities.
    """

    def __init__(
        self,
        storage_path: str | None = None,
        model_id: str = "deterministic-hash-v1",
    ):
        """
        Initialize semantic index.

        Args:
            storage_path: Path to persist index
            model_id: Embedding model identifier for traceability
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.model_id = model_id

        # Embeddings: brick_id -> (embedding_hash, vector)
        # For determinism, we use hash-based pseudo-embeddings
        self._embeddings: dict[str, tuple[str, list[float]]] = {}

        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load index from disk."""
        index_path = self.storage_path / "semantic.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)

            self.model_id = data.get("model_id", self.model_id)
            for item in data.get("embeddings", []):
                self._embeddings[item["brick_id"]] = (
                    item["embedding_hash"],
                    item["vector"],
                )

    def _save_to_disk(self) -> None:
        """Save index to disk."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        index_path = self.storage_path / "semantic.json"

        data = {
            "version": "1.0",
            "model_id": self.model_id,
            "embeddings": [
                {
                    "brick_id": brick_id,
                    "embedding_hash": emb_hash,
                    "vector": vector,
                }
                for brick_id, (emb_hash, vector) in self._embeddings.items()
            ],
        }

        with open(index_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _compute_deterministic_embedding(self, text: str) -> tuple[str, list[float]]:
        """
        Compute a deterministic pseudo-embedding from text.

        This uses hash-based dimensionality reduction:
        - Same text always produces same embedding
        - Different texts produce different embeddings (with high probability)

        NOT semantically meaningful - use for testing determinism only.
        Real semantic search requires a proper embedding model.
        """
        # Create hash-based embedding
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        emb_hash = text_hash[:16]

        # Convert hash to float vector (64 dimensions)
        vector = []
        for i in range(0, 64, 2):
            # Take pairs of hex chars and convert to float in [-1, 1]
            byte_val = int(text_hash[i:i+2], 16)
            vector.append((byte_val - 128) / 128.0)

        return emb_hash, vector

    def index_brick(self, brick: Brick) -> None:
        """Index a brick's semantic embedding."""
        # Combine title and summary for embedding
        text = f"{brick.title} {brick.summary}"

        emb_hash, vector = self._compute_deterministic_embedding(text)
        self._embeddings[brick.id] = (emb_hash, vector)

    def search(self, query: str, top_k: int = 10) -> list[SemanticHit]:
        """
        Search by semantic similarity.

        Args:
            query: Search query
            top_k: Maximum results

        Returns:
            List of SemanticHit sorted by score descending
        """
        query_hash, query_vector = self._compute_deterministic_embedding(query)

        results = []
        for brick_id, (emb_hash, vector) in self._embeddings.items():
            # Cosine similarity
            score = self._cosine_similarity(query_vector, vector)
            results.append(SemanticHit(
                brick_id=brick_id,
                score=score,
                embedding_hash=emb_hash,
            ))

        # Sort by score descending (deterministic for equal scores)
        results.sort(key=lambda h: (-h.score, h.brick_id))
        return results[:top_k]

    def _cosine_similarity(self, v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = sum(a * a for a in v1) ** 0.5
        norm2 = sum(b * b for b in v2) ** 0.5

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot / (norm1 * norm2)

    def index_all(self, bricks: Iterator[Brick]) -> int:
        """Index all bricks."""
        count = 0
        for brick in bricks:
            self.index_brick(brick)
            count += 1

        if self.storage_path:
            self._save_to_disk()

        return count

    def clear(self) -> None:
        """Clear the index."""
        self._embeddings.clear()
        if self.storage_path:
            self._save_to_disk()

    def stats(self) -> dict:
        """Get index statistics."""
        return {
            "model_id": self.model_id,
            "num_embeddings": len(self._embeddings),
            "embedding_dim": 64,
        }
