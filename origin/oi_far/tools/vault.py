"""Vault search tool."""

import json
from pathlib import Path
from typing import Any

from .registry import ToolResult


class VaultSearcher:
    """
    Search the local knowledge vault.

    The vault is the Origin knowledge repository.
    Searches are deterministic given the same vault state.
    """

    def __init__(self, vault_path: str | Path):
        self.vault_path = Path(vault_path)
        self._index: dict[str, Any] | None = None

    def _load_index(self) -> dict[str, Any]:
        """Load or build the search index."""
        if self._index is not None:
            return self._index

        index_path = self.vault_path / "build" / "search.json"
        if index_path.exists():
            with open(index_path) as f:
                self._index = json.load(f)
        else:
            # Build minimal index from packs
            self._index = self._build_index()

        return self._index

    def _build_index(self) -> dict[str, Any]:
        """Build search index from packs."""
        index = {"inverted": {}, "entities": {}}

        packs_dir = self.vault_path / "knowledge" / "packs"
        if not packs_dir.exists():
            return index

        for pack_dir in sorted(packs_dir.iterdir()):
            if not pack_dir.is_dir():
                continue

            pack_yaml = pack_dir / "pack.yaml"
            if not pack_yaml.exists():
                continue

            try:
                import yaml
                with open(pack_yaml) as f:
                    pack = yaml.safe_load(f)

                pack_id = pack.get("id", pack_dir.name)
                title = pack.get("title", "")
                summary = pack.get("summary", "")
                tags = pack.get("tags", [])

                # Index entity
                index["entities"][pack_id] = {
                    "title": title,
                    "summary": summary,
                    "tags": tags,
                    "path": str(pack_yaml),
                }

                # Build inverted index
                text = f"{title} {summary} {' '.join(tags)}".lower()
                for word in text.split():
                    word = word.strip(".,;:!?\"'()[]")
                    if len(word) > 2:
                        if word not in index["inverted"]:
                            index["inverted"][word] = []
                        if pack_id not in index["inverted"][word]:
                            index["inverted"][word].append(pack_id)

            except Exception:
                continue

        return index

    def search(self, query: str, limit: int = 10) -> ToolResult:
        """
        Search the vault.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            ToolResult with matching entries
        """
        try:
            index = self._load_index()

            # Tokenize query
            query_tokens = query.lower().split()

            # Score each entity
            scores: dict[str, float] = {}
            inverted = index.get("inverted", {})

            for token in query_tokens:
                token = token.strip(".,;:!?\"'()[]")
                if token in inverted:
                    for entity_id in inverted[token]:
                        scores[entity_id] = scores.get(entity_id, 0) + 1

            # Sort by score (deterministic for ties)
            sorted_ids = sorted(scores.keys(), key=lambda x: (-scores[x], x))

            # Build results
            results = []
            entities = index.get("entities", {})

            for entity_id in sorted_ids[:limit]:
                entity = entities.get(entity_id, {})
                results.append({
                    "id": entity_id,
                    "title": entity.get("title", ""),
                    "summary": entity.get("summary", "")[:200],
                    "score": scores[entity_id],
                    "path": entity.get("path"),
                })

            return ToolResult(
                success=True,
                data={"results": results, "total": len(scores)},
                deterministic=True,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )

    def get_entity(self, entity_id: str) -> ToolResult:
        """Get a specific entity by ID."""
        try:
            index = self._load_index()
            entities = index.get("entities", {})

            if entity_id not in entities:
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Entity not found: {entity_id}",
                )

            entity = entities[entity_id]

            # Load full pack data if available
            pack_path = entity.get("path")
            if pack_path and Path(pack_path).exists():
                import yaml
                with open(pack_path) as f:
                    full_data = yaml.safe_load(f)
                return ToolResult(
                    success=True,
                    data=full_data,
                    deterministic=True,
                )

            return ToolResult(
                success=True,
                data=entity,
                deterministic=True,
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
            )


def search_vault(query: str, vault_path: str = ".", limit: int = 10) -> ToolResult:
    """Tool function for vault search."""
    searcher = VaultSearcher(vault_path)
    return searcher.search(query, limit)
