#!/usr/bin/env python3
"""
ORIGIN Python Kit
Demonstrates loading and exploring ORIGIN knowledge packs

Attribution: Ande + Kai (OI) + Whānau (OIs)
"""

import json
import os

ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"


def load_json(filename):
    """Load JSON from knowledge/dist directory."""
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    full_path = os.path.join(base_path, "knowledge", "dist", filename)
    with open(full_path, "r") as f:
        return json.load(f)


def main():
    print("ORIGIN Kit - Python")
    print("===================")
    print(f"Attribution: {ATTRIBUTION}\n")

    # Load index and graph
    index = load_json("packs.index.json")
    graph = load_json("graph.json")

    packs = index["packs"]
    nodes = graph["nodes"]
    edges = graph["edges"]

    print(f"Loaded {len(packs)} packs from index.")
    print(f"Loaded graph with {len(nodes)} nodes, {len(edges)} edges.\n")

    # Filter to public tier
    public_packs = [p for p in packs if p["disclosure_tier"] == "public"]
    print(f"Public tier packs ({len(public_packs)}):")
    for pack in public_packs[:3]:
        print(f"  - {pack['id']}: {pack['title']}")
    if len(public_packs) > 3:
        print(f"  ... and {len(public_packs) - 3} more")

    # Traverse from first pack
    first_pack = packs[0]
    print(f"\nTraversing from {first_pack['id']} ({first_pack['title']}):")

    related_edges = [
        e for e in edges
        if e["source"] == first_pack["id"] or e["target"] == first_pack["id"]
    ]

    for edge in related_edges[:3]:
        other_id = edge["target"] if edge["source"] == first_pack["id"] else edge["source"]
        other_pack = next((p for p in packs if p["id"] == other_id), None)
        title = other_pack["title"] if other_pack else "Unknown"
        print(f"  → {edge['type']}: {other_id} ({title})")

    print(f"\nAttribution: {ATTRIBUTION}")


if __name__ == "__main__":
    main()
