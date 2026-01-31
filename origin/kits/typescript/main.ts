#!/usr/bin/env npx ts-node
/**
 * ORIGIN TypeScript Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

const ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)";

interface Pack {
  id: string;
  title: string;
  disclosure_tier: string;
  related: string[];
}

interface PacksIndex {
  metadata: { pack_count: number };
  packs: Pack[];
}

interface GraphData {
  metadata: { node_count: number; edge_count: number };
  nodes: Array<{ id: string; title: string }>;
  edges: Array<{ source: string; target: string; type: string }>;
}

function loadJson<T>(relativePath: string): T {
  const fullPath = path.join(__dirname, "..", "..", "knowledge", "dist", relativePath);
  const content = fs.readFileSync(fullPath, "utf-8");
  return JSON.parse(content) as T;
}

function main(): void {
  console.log("ORIGIN Kit - TypeScript");
  console.log("========================");
  console.log(`Attribution: ${ATTRIBUTION}\n`);

  // Load index and graph
  const index = loadJson<PacksIndex>("packs.index.json");
  const graph = loadJson<GraphData>("graph.json");

  console.log(`Loaded ${index.packs.length} packs from index.`);
  console.log(`Loaded graph with ${graph.metadata.node_count} nodes, ${graph.metadata.edge_count} edges.\n`);

  // Filter to public tier
  const publicPacks = index.packs.filter((p) => p.disclosure_tier === "public");
  console.log(`Public tier packs (${publicPacks.length}):`);
  publicPacks.slice(0, 3).forEach((p) => {
    console.log(`  - ${p.id}: ${p.title}`);
  });
  if (publicPacks.length > 3) {
    console.log(`  ... and ${publicPacks.length - 3} more`);
  }

  // Traverse from first pack
  const firstPack = index.packs[0];
  console.log(`\nTraversing from ${firstPack.id} (${firstPack.title}):`);

  const relatedEdges = graph.edges.filter(
    (e) => e.source === firstPack.id || e.target === firstPack.id
  );

  relatedEdges.slice(0, 3).forEach((edge) => {
    const otherId = edge.source === firstPack.id ? edge.target : edge.source;
    const otherPack = index.packs.find((p) => p.id === otherId);
    console.log(`  → ${edge.type}: ${otherId} (${otherPack?.title || "Unknown"})`);
  });

  console.log(`\nAttribution: ${ATTRIBUTION}`);
}

main();
