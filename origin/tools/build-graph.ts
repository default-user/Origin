#!/usr/bin/env npx ts-node
/**
 * ORIGIN Graph Builder (Extended)
 * Builds both legacy graph.json and new IR-based build/graph.json
 * with adjacency lists, typed relations, and provenance pointers
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

import {
  IRIndex,
  IRGraph,
  AdjacencyEntry,
  GraphNode,
  Entity,
  Edge,
  RelationType,
} from "../src/ir/types";
import { stableStringify, contentHash } from "../src/ir/utils";

const ROOT_DIR = path.join(__dirname, "..");
const LEGACY_DIST_DIR = path.join(ROOT_DIR, "knowledge", "dist");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const LEGACY_INDEX_PATH = path.join(LEGACY_DIST_DIR, "packs.index.json");
const IR_INDEX_PATH = path.join(BUILD_DIR, "index.json");
const LEGACY_OUTPUT_PATH = path.join(LEGACY_DIST_DIR, "graph.json");
const IR_OUTPUT_PATH = path.join(BUILD_DIR, "graph.json");

// Legacy interfaces for backward compatibility
interface LegacyGraphNode {
  id: string;
  title: string;
  summary: string;
  status: string;
  tier: string;
  tags: string[];
}

interface LegacyGraphEdge {
  source: string;
  target: string;
  type: "parent" | "child" | "related";
}

interface LegacyGraph {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    node_count: number;
    edge_count: number;
  };
  nodes: LegacyGraphNode[];
  edges: LegacyGraphEdge[];
}

function loadIRIndex(): IRIndex | null {
  if (!fs.existsSync(IR_INDEX_PATH)) {
    return null;
  }
  const content = fs.readFileSync(IR_INDEX_PATH, "utf-8");
  return JSON.parse(content) as IRIndex;
}

function loadLegacyIndex(): Record<string, unknown> | null {
  if (!fs.existsSync(LEGACY_INDEX_PATH)) {
    return null;
  }
  const content = fs.readFileSync(LEGACY_INDEX_PATH, "utf-8");
  return JSON.parse(content);
}

function buildIRGraph(index: IRIndex): IRGraph {
  const adjacency: Record<string, AdjacencyEntry[]> = {};
  const nodes: Record<string, GraphNode> = {};

  // Build node map from entities
  for (const entity of index.entities) {
    nodes[entity.id] = {
      id: entity.id,
      type: entity.type,
      labels: entity.labels,
      sensitivity: entity.sensitivity.level,
    };
    // Initialize adjacency list
    adjacency[entity.id] = [];
  }

  // Build adjacency lists from edges
  for (const edge of index.edges) {
    // Ensure source node exists in adjacency
    if (!adjacency[edge.src]) {
      adjacency[edge.src] = [];
    }

    adjacency[edge.src].push({
      target: edge.dst,
      rel: edge.rel,
      attrs: edge.attrs,
      provenance: edge.provenance,
    });
  }

  // Sort adjacency lists for determinism
  for (const nodeId of Object.keys(adjacency).sort()) {
    adjacency[nodeId].sort((a, b) => {
      const relCompare = a.rel.localeCompare(b.rel);
      if (relCompare !== 0) return relCompare;
      return a.target.localeCompare(b.target);
    });
  }

  // Build the graph with sorted keys
  const sortedAdjacency: Record<string, AdjacencyEntry[]> = {};
  for (const key of Object.keys(adjacency).sort()) {
    sortedAdjacency[key] = adjacency[key];
  }

  const sortedNodes: Record<string, GraphNode> = {};
  for (const key of Object.keys(nodes).sort()) {
    sortedNodes[key] = nodes[key];
  }

  return {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      node_count: Object.keys(nodes).length,
      edge_count: index.edges.length,
      content_hash: "", // Will be computed
    },
    adjacency: sortedAdjacency,
    nodes: sortedNodes,
  };
}

function buildLegacyGraph(legacyIndex: Record<string, unknown>): LegacyGraph {
  const packs = (legacyIndex.packs || []) as Array<Record<string, unknown>>;
  const nodes: LegacyGraphNode[] = [];
  const edges: LegacyGraphEdge[] = [];
  const edgeSet = new Set<string>();

  for (const pack of packs) {
    // Build node
    nodes.push({
      id: pack.id as string,
      title: pack.title as string,
      summary: pack.summary as string,
      status: pack.status as string,
      tier: pack.disclosure_tier as string,
      tags: (pack.tags as string[]) || [],
    });

    const packId = pack.id as string;

    // Build parent edges
    for (const parentId of (pack.parents || []) as string[]) {
      const edgeKey = `${parentId}->${packId}:parent`;
      if (!edgeSet.has(edgeKey)) {
        edges.push({
          source: parentId,
          target: packId,
          type: "parent",
        });
        edgeSet.add(edgeKey);
      }
    }

    // Build child edges
    for (const childId of (pack.children || []) as string[]) {
      const edgeKey = `${packId}->${childId}:child`;
      if (!edgeSet.has(edgeKey)) {
        edges.push({
          source: packId,
          target: childId,
          type: "child",
        });
        edgeSet.add(edgeKey);
      }
    }

    // Build related edges
    for (const relatedId of (pack.related || []) as string[]) {
      const edgeKey1 = `${packId}->${relatedId}:related`;
      const edgeKey2 = `${relatedId}->${packId}:related`;
      if (!edgeSet.has(edgeKey1) && !edgeSet.has(edgeKey2)) {
        edges.push({
          source: packId,
          target: relatedId,
          type: "related",
        });
        edgeSet.add(edgeKey1);
      }
    }
  }

  // Sort for determinism
  nodes.sort((a, b) => a.id.localeCompare(b.id));
  edges.sort((a, b) => {
    const srcCompare = a.source.localeCompare(b.source);
    if (srcCompare !== 0) return srcCompare;
    const typeCompare = a.type.localeCompare(b.type);
    if (typeCompare !== 0) return typeCompare;
    return a.target.localeCompare(b.target);
  });

  return {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      node_count: nodes.length,
      edge_count: edges.length,
    },
    nodes,
    edges,
  };
}

async function main(): Promise<void> {
  console.log("ORIGIN Graph Builder (Extended)");
  console.log("===============================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Try IR index first
  const irIndex = loadIRIndex();
  if (irIndex) {
    console.log("Building IR graph from build/index.json...");

    const irGraph = buildIRGraph(irIndex);

    // Compute content hash
    const hashableContent = {
      adjacency: irGraph.adjacency,
      nodes: irGraph.nodes,
    };
    irGraph.metadata.content_hash = contentHash(hashableContent);

    // Write IR graph
    fs.writeFileSync(IR_OUTPUT_PATH, stableStringify(irGraph));
    console.log(`\u2713 IR graph written to ${IR_OUTPUT_PATH}`);
    console.log(
      `  ${irGraph.metadata.node_count} nodes, ${irGraph.metadata.edge_count} edges`
    );
    console.log(`  Content hash: ${irGraph.metadata.content_hash.slice(0, 16)}`);
  } else {
    console.log("Warning: build/index.json not found. Skipping IR graph.");
  }

  // Build legacy graph
  const legacyIndex = loadLegacyIndex();
  if (legacyIndex) {
    console.log("\nBuilding legacy graph from packs.index.json...");

    const legacyGraph = buildLegacyGraph(legacyIndex);

    // Write legacy graph
    fs.writeFileSync(LEGACY_OUTPUT_PATH, JSON.stringify(legacyGraph, null, 2));
    console.log(`\u2713 Legacy graph written to ${LEGACY_OUTPUT_PATH}`);
    console.log(
      `  ${legacyGraph.metadata.node_count} nodes, ${legacyGraph.metadata.edge_count} edges`
    );
  } else {
    console.error("Error: packs.index.json not found. Run build:index first.");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
