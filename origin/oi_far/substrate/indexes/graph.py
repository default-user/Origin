"""Graph index for entity/topic/claim relationships."""

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from ..types import Brick, Link


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    kind: str
    title: str
    tags: list[str]


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    source: str
    target: str
    relation: str
    strength: float = 1.0


@dataclass
class GraphPath:
    """A path through the knowledge graph."""
    nodes: list[str]
    edges: list[str]  # Edge relations
    total_strength: float


class GraphIndex:
    """
    Graph index for entity/topic/claim relationships.

    Supports:
    - Adjacency lookup
    - Path finding
    - Clustering by topic/tag
    """

    def __init__(self, storage_path: str | None = None):
        """
        Initialize graph index.

        Args:
            storage_path: Path to persist index. If None, in-memory only.
        """
        self.storage_path = Path(storage_path) if storage_path else None

        # Node storage
        self._nodes: dict[str, GraphNode] = {}

        # Adjacency lists: node_id -> [(target_id, relation, strength)]
        self._outgoing: dict[str, list[tuple[str, str, float]]] = defaultdict(list)
        self._incoming: dict[str, list[tuple[str, str, float]]] = defaultdict(list)

        # Tag index: tag -> [node_ids]
        self._by_tag: dict[str, list[str]] = defaultdict(list)

        # Kind index: kind -> [node_ids]
        self._by_kind: dict[str, list[str]] = defaultdict(list)

        if self.storage_path and self.storage_path.exists():
            self._load_from_disk()

    def _load_from_disk(self) -> None:
        """Load index from disk."""
        index_path = self.storage_path / "graph.json"
        if index_path.exists():
            with open(index_path) as f:
                data = json.load(f)

            for node_data in data.get("nodes", []):
                node = GraphNode(
                    id=node_data["id"],
                    kind=node_data["kind"],
                    title=node_data["title"],
                    tags=node_data.get("tags", []),
                )
                self._nodes[node.id] = node
                self._by_kind[node.kind].append(node.id)
                for tag in node.tags:
                    self._by_tag[tag].append(node.id)

            for edge_data in data.get("edges", []):
                source = edge_data["source"]
                target = edge_data["target"]
                relation = edge_data["relation"]
                strength = edge_data.get("strength", 1.0)

                self._outgoing[source].append((target, relation, strength))
                self._incoming[target].append((source, relation, strength))

    def _save_to_disk(self) -> None:
        """Save index to disk."""
        if not self.storage_path:
            return

        self.storage_path.mkdir(parents=True, exist_ok=True)
        index_path = self.storage_path / "graph.json"

        # Collect all edges
        edges = []
        for source, targets in self._outgoing.items():
            for target, relation, strength in targets:
                edges.append({
                    "source": source,
                    "target": target,
                    "relation": relation,
                    "strength": strength,
                })

        data = {
            "version": "1.0",
            "nodes": [
                {
                    "id": n.id,
                    "kind": n.kind,
                    "title": n.title,
                    "tags": n.tags,
                }
                for n in self._nodes.values()
            ],
            "edges": edges,
        }

        with open(index_path, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)

    def index_brick(self, brick: Brick) -> None:
        """Index a brick as a graph node with edges."""
        # Remove old entries
        self._remove_node(brick.id)

        # Add node
        node = GraphNode(
            id=brick.id,
            kind=brick.kind.value,
            title=brick.title,
            tags=brick.tags,
        )
        self._nodes[brick.id] = node

        # Index by kind and tags
        self._by_kind[node.kind].append(brick.id)
        for tag in brick.tags:
            self._by_tag[tag].append(brick.id)

        # Add edges from brick links
        for link in brick.links:
            self.add_edge(brick.id, link.target_id, link.relation, link.strength)

    def _remove_node(self, node_id: str) -> None:
        """Remove a node and its edges."""
        if node_id not in self._nodes:
            return

        node = self._nodes.pop(node_id)

        # Remove from kind index
        if node.kind in self._by_kind and node_id in self._by_kind[node.kind]:
            self._by_kind[node.kind].remove(node_id)

        # Remove from tag index
        for tag in node.tags:
            if tag in self._by_tag and node_id in self._by_tag[tag]:
                self._by_tag[tag].remove(node_id)

        # Remove outgoing edges
        if node_id in self._outgoing:
            for target, relation, _ in self._outgoing[node_id]:
                if target in self._incoming:
                    self._incoming[target] = [
                        e for e in self._incoming[target]
                        if e[0] != node_id
                    ]
            del self._outgoing[node_id]

        # Remove incoming edges
        if node_id in self._incoming:
            for source, relation, _ in self._incoming[node_id]:
                if source in self._outgoing:
                    self._outgoing[source] = [
                        e for e in self._outgoing[source]
                        if e[0] != node_id
                    ]
            del self._incoming[node_id]

    def add_edge(
        self,
        source: str,
        target: str,
        relation: str,
        strength: float = 1.0,
    ) -> None:
        """Add an edge to the graph."""
        # Check for duplicates
        for t, r, s in self._outgoing[source]:
            if t == target and r == relation:
                return  # Already exists

        self._outgoing[source].append((target, relation, strength))
        self._incoming[target].append((source, relation, strength))

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "outgoing",
        relation: str | None = None,
    ) -> list[tuple[str, str, float]]:
        """
        Get neighbors of a node.

        Args:
            node_id: Source node ID
            direction: "outgoing", "incoming", or "both"
            relation: Optional filter by relation type

        Returns:
            List of (neighbor_id, relation, strength)
        """
        results = []

        if direction in ("outgoing", "both"):
            for target, rel, strength in self._outgoing.get(node_id, []):
                if relation is None or rel == relation:
                    results.append((target, rel, strength))

        if direction in ("incoming", "both"):
            for source, rel, strength in self._incoming.get(node_id, []):
                if relation is None or rel == relation:
                    results.append((source, rel, strength))

        return results

    def get_by_tag(self, tag: str) -> list[str]:
        """Get all node IDs with a specific tag."""
        return list(self._by_tag.get(tag, []))

    def get_by_kind(self, kind: str) -> list[str]:
        """Get all node IDs of a specific kind."""
        return list(self._by_kind.get(kind, []))

    def find_path(
        self,
        start: str,
        end: str,
        max_depth: int = 5,
    ) -> GraphPath | None:
        """
        Find a path between two nodes using BFS.

        Args:
            start: Starting node ID
            end: Target node ID
            max_depth: Maximum path length

        Returns:
            GraphPath if found, None otherwise
        """
        if start not in self._nodes or end not in self._nodes:
            return None

        if start == end:
            return GraphPath(nodes=[start], edges=[], total_strength=1.0)

        # BFS
        queue = [(start, [start], [], 1.0)]
        visited = {start}

        while queue:
            current, path, edges, strength = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor, relation, edge_strength in self._outgoing.get(current, []):
                if neighbor in visited:
                    continue

                new_path = path + [neighbor]
                new_edges = edges + [relation]
                new_strength = strength * edge_strength

                if neighbor == end:
                    return GraphPath(
                        nodes=new_path,
                        edges=new_edges,
                        total_strength=new_strength,
                    )

                visited.add(neighbor)
                queue.append((neighbor, new_path, new_edges, new_strength))

        return None

    def find_common_neighbors(self, node_ids: list[str]) -> list[str]:
        """Find nodes connected to all given nodes."""
        if not node_ids:
            return []

        # Get neighbors for first node
        common = set()
        for target, _, _ in self._outgoing.get(node_ids[0], []):
            common.add(target)
        for source, _, _ in self._incoming.get(node_ids[0], []):
            common.add(source)

        # Intersect with neighbors of other nodes
        for node_id in node_ids[1:]:
            neighbors = set()
            for target, _, _ in self._outgoing.get(node_id, []):
                neighbors.add(target)
            for source, _, _ in self._incoming.get(node_id, []):
                neighbors.add(source)
            common &= neighbors

        return list(common)

    def get_subgraph(
        self,
        seed_ids: list[str],
        max_depth: int = 2,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """
        Get a subgraph around seed nodes.

        Args:
            seed_ids: Starting node IDs
            max_depth: Maximum distance from seeds

        Returns:
            (nodes, edges) in the subgraph
        """
        visited = set(seed_ids)
        frontier = list(seed_ids)

        for _ in range(max_depth):
            new_frontier = []
            for node_id in frontier:
                for target, _, _ in self._outgoing.get(node_id, []):
                    if target not in visited:
                        visited.add(target)
                        new_frontier.append(target)
                for source, _, _ in self._incoming.get(node_id, []):
                    if source not in visited:
                        visited.add(source)
                        new_frontier.append(source)
            frontier = new_frontier

        # Collect nodes and edges
        nodes = [self._nodes[nid] for nid in visited if nid in self._nodes]
        edges = []
        for source in visited:
            for target, relation, strength in self._outgoing.get(source, []):
                if target in visited:
                    edges.append(GraphEdge(
                        source=source,
                        target=target,
                        relation=relation,
                        strength=strength,
                    ))

        return nodes, edges

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
        self._nodes.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._by_tag.clear()
        self._by_kind.clear()

        if self.storage_path:
            self._save_to_disk()

    def stats(self) -> dict:
        """Get index statistics."""
        total_edges = sum(len(e) for e in self._outgoing.values())
        return {
            "num_nodes": len(self._nodes),
            "num_edges": total_edges,
            "num_tags": len(self._by_tag),
            "num_kinds": len(self._by_kind),
        }
