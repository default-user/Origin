#!/usr/bin/env npx ts-node
/**
 * ORIGIN Search Index Builder
 * Builds knowledge/dist/search.json for client-side search
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

const DIST_DIR = path.join(__dirname, "..", "knowledge", "dist");
const PACKS_DIR = path.join(__dirname, "..", "knowledge", "packs");
const INDEX_PATH = path.join(DIST_DIR, "packs.index.json");
const OUTPUT_PATH = path.join(DIST_DIR, "search.json");

interface SearchEntry {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  content_preview: string;
  tokens: string[];
}

interface SearchIndex {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    entry_count: number;
  };
  entries: SearchEntry[];
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 2);
}

function loadContent(slug: string): string {
  const mdxPath = path.join(PACKS_DIR, slug, "content.mdx");
  if (fs.existsSync(mdxPath)) {
    const content = fs.readFileSync(mdxPath, "utf-8");
    // Strip markdown formatting for search
    return content
      .replace(/^#+ .*/gm, "")
      .replace(/\*\*([^*]+)\*\*/g, "$1")
      .replace(/\*([^*]+)\*/g, "$1")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
      .replace(/```[\s\S]*?```/g, "")
      .slice(0, 500);
  }
  return "";
}

async function main(): Promise<void> {
  console.log("ORIGIN Search Index Builder");
  console.log("===========================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load packs index
  if (!fs.existsSync(INDEX_PATH)) {
    console.error("Error: packs.index.json not found. Run build-index first.");
    process.exit(1);
  }

  const indexContent = fs.readFileSync(INDEX_PATH, "utf-8");
  const index = JSON.parse(indexContent);

  const entries: SearchEntry[] = [];

  for (const pack of index.packs) {
    const contentPreview = loadContent(pack.slug);

    // Build tokens from all searchable fields
    const allText = [
      pack.title,
      pack.summary,
      ...pack.tags,
      ...(pack.claims || []),
      contentPreview,
    ].join(" ");

    const tokens = [...new Set(tokenize(allText))];

    entries.push({
      id: pack.id,
      title: pack.title,
      summary: pack.summary,
      tags: pack.tags,
      content_preview: contentPreview.slice(0, 200) + "...",
      tokens,
    });

    console.log(`✓ Indexed ${pack.id}: ${tokens.length} tokens`);
  }

  // Build search index
  const searchIndex: SearchIndex = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      entry_count: entries.length,
    },
    entries,
  };

  // Write output
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(searchIndex, null, 2));

  console.log(`\n✓ Built search index with ${entries.length} entries.`);
  console.log(`✓ Written ${OUTPUT_PATH}`);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
