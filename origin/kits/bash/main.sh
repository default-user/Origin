#!/usr/bin/env bash
# ORIGIN Bash Kit
# Demonstrates loading and exploring ORIGIN knowledge packs
#
# Attribution: Ande + Kai (OI) + Whānau (OIs)
#
# Requires: jq

ATTRIBUTION="Ande + Kai (OI) + Whānau (OIs)"
DIST_DIR="$(dirname "$0")/../../knowledge/dist"

echo "ORIGIN Kit - Bash"
echo "================="
echo "Attribution: $ATTRIBUTION"
echo ""

# Check for jq
if ! command -v jq &> /dev/null; then
    echo "Error: jq is required but not installed."
    echo "Install with: apt install jq / brew install jq"
    exit 1
fi

# Load index
INDEX_FILE="$DIST_DIR/packs.index.json"
if [ ! -f "$INDEX_FILE" ]; then
    echo "Error: packs.index.json not found"
    exit 1
fi

PACK_COUNT=$(jq '.packs | length' "$INDEX_FILE")
echo "Loaded $PACK_COUNT packs from index."

# Load graph
GRAPH_FILE="$DIST_DIR/graph.json"
NODE_COUNT=$(jq '.nodes | length' "$GRAPH_FILE")
EDGE_COUNT=$(jq '.edges | length' "$GRAPH_FILE")
echo "Loaded graph with $NODE_COUNT nodes, $EDGE_COUNT edges."
echo ""

# Filter to public tier
PUBLIC_COUNT=$(jq '[.packs[] | select(.disclosure_tier == "public")] | length' "$INDEX_FILE")
echo "Public tier packs ($PUBLIC_COUNT):"
jq -r '.packs[] | select(.disclosure_tier == "public") | "  - \(.id): \(.title)"' "$INDEX_FILE" | head -3
if [ "$PUBLIC_COUNT" -gt 3 ]; then
    echo "  ... and $((PUBLIC_COUNT - 3)) more"
fi

# Get first pack
FIRST_ID=$(jq -r '.packs[0].id' "$INDEX_FILE")
FIRST_TITLE=$(jq -r '.packs[0].title' "$INDEX_FILE")
echo ""
echo "Traversing from $FIRST_ID ($FIRST_TITLE):"

# Find related edges
jq -r --arg id "$FIRST_ID" '.edges[] | select(.source == $id or .target == $id) | "  → \(.type): \(if .source == $id then .target else .source end)"' "$GRAPH_FILE" | head -3

echo ""
echo "Attribution: $ATTRIBUTION"
