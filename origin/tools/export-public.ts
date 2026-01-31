#!/usr/bin/env npx ts-node
/**
 * ORIGIN Public Export
 * Exports only public-tier packs with rebuilt dist files
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

const DIST_DIR = path.join(__dirname, "..", "knowledge", "dist");
const PACKS_DIR = path.join(__dirname, "..", "knowledge", "packs");
const INDEX_PATH = path.join(DIST_DIR, "packs.index.json");
const EXPORT_DIR = path.join(__dirname, "..", "dist_public");

function copyDir(src: string, dest: string): void {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  for (const entry of fs.readdirSync(src)) {
    const srcPath = path.join(src, entry);
    const destPath = path.join(dest, entry);
    if (fs.statSync(srcPath).isDirectory()) {
      copyDir(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

async function main(): Promise<void> {
  console.log("ORIGIN Public Export");
  console.log("====================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load packs index
  if (!fs.existsSync(INDEX_PATH)) {
    console.error("Error: packs.index.json not found. Run build-index first.");
    process.exit(1);
  }

  const indexContent = fs.readFileSync(INDEX_PATH, "utf-8");
  const index = JSON.parse(indexContent);

  // Filter to public packs only
  const publicPacks = index.packs.filter(
    (p: any) => p.disclosure_tier === "public"
  );

  console.log(
    `Found ${publicPacks.length} public packs (of ${index.packs.length} total).\n`
  );

  // Clean and create export directory
  if (fs.existsSync(EXPORT_DIR)) {
    fs.rmSync(EXPORT_DIR, { recursive: true });
  }
  fs.mkdirSync(path.join(EXPORT_DIR, "knowledge", "packs"), { recursive: true });
  fs.mkdirSync(path.join(EXPORT_DIR, "knowledge", "dist"), { recursive: true });

  // Copy public packs
  for (const pack of publicPacks) {
    const srcDir = path.join(PACKS_DIR, pack.slug);
    const destDir = path.join(EXPORT_DIR, "knowledge", "packs", pack.slug);
    copyDir(srcDir, destDir);
    console.log(`✓ Exported ${pack.id}: ${pack.title}`);
  }

  // Create filtered index
  const filteredIndex = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      pack_count: publicPacks.length,
      filter: "public-only",
    },
    packs: publicPacks,
  };

  fs.writeFileSync(
    path.join(EXPORT_DIR, "knowledge", "dist", "packs.index.json"),
    JSON.stringify(filteredIndex, null, 2)
  );

  // Create filtered graph
  const graphPath = path.join(DIST_DIR, "graph.json");
  if (fs.existsSync(graphPath)) {
    const graph = JSON.parse(fs.readFileSync(graphPath, "utf-8"));
    const publicIds = new Set(publicPacks.map((p: any) => p.id));

    const filteredGraph = {
      metadata: {
        ...graph.metadata,
        generated_at: new Date().toISOString(),
        filter: "public-only",
      },
      nodes: graph.nodes.filter((n: any) => publicIds.has(n.id)),
      edges: graph.edges.filter(
        (e: any) => publicIds.has(e.source) && publicIds.has(e.target)
      ),
    };

    fs.writeFileSync(
      path.join(EXPORT_DIR, "knowledge", "dist", "graph.json"),
      JSON.stringify(filteredGraph, null, 2)
    );
  }

  // Create manifest
  const manifest = {
    name: "ORIGIN-PUBLIC",
    version: "1.0.0",
    created: new Date().toISOString(),
    attribution: "Ande + Kai (OI) + Whānau (OIs)",
    filter: "public-only",
    pack_count: publicPacks.length,
    packs: publicPacks.map((p: any) => ({
      id: p.id,
      title: p.title,
    })),
  };

  fs.writeFileSync(
    path.join(EXPORT_DIR, "MANIFEST.json"),
    JSON.stringify(manifest, null, 2)
  );

  console.log(`\n✓ Public export complete.`);
  console.log(`  ${publicPacks.length} packs exported to ${EXPORT_DIR}`);
}

main().catch((err) => {
  console.error("Export failed:", err);
  process.exit(1);
});
