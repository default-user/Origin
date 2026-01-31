#!/usr/bin/env npx ts-node
/**
 * ORIGIN Graph Builder
 * Builds knowledge/dist/graph.json from pack relationships
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

const DIST_DIR = path.join(__dirname, "..", "knowledge", "dist");
const INDEX_PATH = path.join(DIST_DIR, "packs.index.json");
const OUTPUT_PATH = path.join(DIST_DIR, "graph.json");

interface GraphNode {
  id: string;
  title: string;
  summary: string;
  status: string;
  tier: string;
  tags: string[];
}

interface GraphEdge {
  source: string;
  target: string;
  type: "parent" | "child" | "related";
}

interface Graph {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    node_count: number;
    edge_count: number;
  };
  nodes: GraphNode[];
  edges: GraphEdge[];
}

async function main(): Promise<void> {
  console.log("ORIGIN Graph Builder");
  console.log("====================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load packs index
  if (!fs.existsSync(INDEX_PATH)) {
    console.error("Error: packs.index.json not found. Run build-index first.");
    process.exit(1);
  }

  const indexContent = fs.readFileSync(INDEX_PATH, "utf-8");
  const index = JSON.parse(indexContent);

  const nodes: GraphNode[] = [];
  const edges: GraphEdge[] = [];
  const edgeSet = new Set<string>(); // Prevent duplicates

  // Build nodes
  for (const pack of index.packs) {
    nodes.push({
      id: pack.id,
      title: pack.title,
      summary: pack.summary,
      status: pack.status,
      tier: pack.disclosure_tier,
      tags: pack.tags,
    });

    // Build edges from parents
    for (const parentId of pack.parents || []) {
      const edgeKey = `${parentId}->${pack.id}:parent`;
      if (!edgeSet.has(edgeKey)) {
        edges.push({
          source: parentId,
          target: pack.id,
          type: "parent",
        });
        edgeSet.add(edgeKey);
      }
    }

    // Build edges from children
    for (const childId of pack.children || []) {
      const edgeKey = `${pack.id}->${childId}:child`;
      if (!edgeSet.has(edgeKey)) {
        edges.push({
          source: pack.id,
          target: childId,
          type: "child",
        });
        edgeSet.add(edgeKey);
      }
    }

    // Build edges from related
    for (const relatedId of pack.related || []) {
      const edgeKey1 = `${pack.id}->${relatedId}:related`;
      const edgeKey2 = `${relatedId}->${pack.id}:related`;
      if (!edgeSet.has(edgeKey1) && !edgeSet.has(edgeKey2)) {
        edges.push({
          source: pack.id,
          target: relatedId,
          type: "related",
        });
        edgeSet.add(edgeKey1);
      }
    }
  }

  // Build graph
  const graph: Graph = {
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

  // Write output
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(graph, null, 2));

  console.log(`✓ Built graph with ${nodes.length} nodes and ${edges.length} edges.`);
  console.log(`✓ Written ${OUTPUT_PATH}`);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
