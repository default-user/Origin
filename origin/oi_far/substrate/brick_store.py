"""Brick store for meaning-compressed knowledge units."""

import json
from pathlib import Path
from typing import Iterator

from .types import Brick, BrickKind, Claim, Link


class BrickStore:
    """
    Store for meaning-compressed knowledge bricks.

    Bricks are the atomic units of structured knowledge.
    They contain claims, definitions, and links with provenance.
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize brick store.

        Args:
            storage_path: Path to persist bricks. If None, in-memory only.
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self._bricks: dict[str, Brick] = {}
        self._by_kind: dict[BrickKind, list[str]] = {k: [] for k in BrickKind}
        self._by_tag: dict[str, list[str]] = {}
        self._claim_index: dict[str, str] = {}  # claim_id -> brick_id

        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load bricks from disk storage."""
        index_path = self.storage_path / "bricks.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)
            for brick_data in data.get("bricks", []):
                brick = Brick.from_dict(brick_data)
                self._index_brick(brick)

    def _save_to_disk(self) -> None:
        """Save bricks to disk storage."""
        if not self.storage_path:
            return
        self.storage_path.mkdir(parents=True, exist_ok=True)
        index_path = self.storage_path / "bricks.json"
        data = {
            "version": "1.0",
            "bricks": [brick.to_dict() for brick in self._bricks.values()],
        }
        with open(index_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def _index_brick(self, brick: Brick) -> None:
        """Index a brick for fast lookup."""
        self._bricks[brick.id] = brick
        self._by_kind[brick.kind].append(brick.id)

        for tag in brick.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            self._by_tag[tag].append(brick.id)

        for claim in brick.claims:
            self._claim_index[claim.id] = brick.id

    def _unindex_brick(self, brick: Brick) -> None:
        """Remove brick from indexes."""
        if brick.id in self._by_kind.get(brick.kind, []):
            self._by_kind[brick.kind].remove(brick.id)

        for tag in brick.tags:
            if tag in self._by_tag and brick.id in self._by_tag[tag]:
                self._by_tag[tag].remove(brick.id)

        for claim in brick.claims:
            if claim.id in self._claim_index:
                del self._claim_index[claim.id]

    def add(self, brick: Brick) -> str:
        """
        Add a brick to the store.

        Returns:
            Brick ID
        """
        # Remove old version if exists
        if brick.id in self._bricks:
            self._unindex_brick(self._bricks[brick.id])

        self._index_brick(brick)

        if self.storage_path:
            self._save_to_disk()

        return brick.id

    def get(self, brick_id: str) -> Brick | None:
        """Get brick by ID."""
        return self._bricks.get(brick_id)

    def get_by_claim(self, claim_id: str) -> Brick | None:
        """Get brick containing a specific claim."""
        brick_id = self._claim_index.get(claim_id)
        if brick_id:
            return self._bricks.get(brick_id)
        return None

    def get_by_kind(self, kind: BrickKind) -> list[Brick]:
        """Get all bricks of a specific kind."""
        return [self._bricks[bid] for bid in self._by_kind.get(kind, [])]

    def get_by_tag(self, tag: str) -> list[Brick]:
        """Get all bricks with a specific tag."""
        return [self._bricks[bid] for bid in self._by_tag.get(tag, [])]

    def remove(self, brick_id: str) -> bool:
        """Remove brick by ID."""
        if brick_id in self._bricks:
            brick = self._bricks.pop(brick_id)
            self._unindex_brick(brick)
            if self.storage_path:
                self._save_to_disk()
            return True
        return False

    def list_all(self) -> list[Brick]:
        """List all bricks."""
        return list(self._bricks.values())

    def count(self) -> int:
        """Count bricks in store."""
        return len(self._bricks)

    def iterate(self) -> Iterator[Brick]:
        """Iterate over all bricks."""
        yield from self._bricks.values()

    def find_related(self, brick_id: str, relation: str | None = None) -> list[Brick]:
        """
        Find bricks related to the given brick.

        Args:
            brick_id: Source brick ID
            relation: Optional filter by relation type
        """
        brick = self.get(brick_id)
        if not brick:
            return []

        related = []
        for link in brick.links:
            if relation is None or link.relation == relation:
                target = self.get(link.target_id)
                if target:
                    related.append(target)

        return related

    def find_contradictions(self, brick: Brick) -> list[tuple[Brick, Claim, Claim]]:
        """
        Find bricks with claims that contradict the given brick.

        Returns list of (other_brick, other_claim, this_claim) tuples.
        """
        contradictions = []

        for claim in brick.claims:
            # Look for links marked as contradictions
            for link in brick.links:
                if link.relation == "contradicts":
                    other = self.get(link.target_id)
                    if other:
                        for other_claim in other.claims:
                            contradictions.append((other, other_claim, claim))

            # Look for negations
            if claim.negation:
                # Find positive claims that match
                claim_text_lower = claim.text.lower()
                for other in self._bricks.values():
                    if other.id == brick.id:
                        continue
                    for other_claim in other.claims:
                        if not other_claim.negation and self._claims_match(claim_text_lower, other_claim.text.lower()):
                            contradictions.append((other, other_claim, claim))

        return contradictions

    def _claims_match(self, text1: str, text2: str) -> bool:
        """Check if two claim texts are about the same thing."""
        # Simple word overlap heuristic
        words1 = set(text1.split())
        words2 = set(text2.split())
        overlap = len(words1 & words2)
        union = len(words1 | words2)
        if union == 0:
            return False
        return overlap / union > 0.5

    def search_claims(self, query: str) -> list[tuple[Brick, Claim, float]]:
        """
        Search claims by text.

        Returns list of (brick, claim, score) tuples sorted by score descending.
        """
        query_lower = query.lower()
        query_words = set(query_lower.split())

        results = []
        for brick in self._bricks.values():
            for claim in brick.claims:
                claim_lower = claim.text.lower()
                claim_words = set(claim_lower.split())

                # Score by word overlap
                overlap = len(query_words & claim_words)
                if overlap > 0:
                    score = overlap / len(query_words)
                    # Boost by claim confidence
                    score *= claim.confidence
                    results.append((brick, claim, score))

        # Sort by score descending
        results.sort(key=lambda x: x[2], reverse=True)
        return results

    def get_all_claims(self) -> list[tuple[Brick, Claim]]:
        """Get all claims from all bricks."""
        claims = []
        for brick in self._bricks.values():
            for claim in brick.claims:
                claims.append((brick, claim))
        return claims

    def clear(self) -> None:
        """Clear all bricks."""
        self._bricks.clear()
        self._by_kind = {k: [] for k in BrickKind}
        self._by_tag.clear()
        self._claim_index.clear()
        if self.storage_path:
            self._save_to_disk()
