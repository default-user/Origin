#!/usr/bin/env npx ts-node
/**
 * ORIGIN Search Index Builder (Extended)
 * Builds both legacy search.json and new IR-based build/search.json
 * with inverted index and citation support for deterministic queries
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

import {
  IRIndex,
  IRSearch,
  SearchHit,
  Citation,
  Entity,
} from "../src/ir/types";
import { stableStringify, contentHash } from "../src/ir/utils";

const ROOT_DIR = path.join(__dirname, "..");
const LEGACY_DIST_DIR = path.join(ROOT_DIR, "knowledge", "dist");
const PACKS_DIR = path.join(ROOT_DIR, "knowledge", "packs");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const LEGACY_INDEX_PATH = path.join(LEGACY_DIST_DIR, "packs.index.json");
const IR_INDEX_PATH = path.join(BUILD_DIR, "index.json");
const LEGACY_OUTPUT_PATH = path.join(LEGACY_DIST_DIR, "search.json");
const IR_OUTPUT_PATH = path.join(BUILD_DIR, "search.json");

// Legacy interfaces
interface LegacySearchEntry {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  content_preview: string;
  tokens: string[];
}

interface LegacySearchIndex {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    entry_count: number;
  };
  entries: LegacySearchEntry[];
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 2);
}

function loadContent(slug: string): string {
  // Try multiple possible paths
  const possiblePaths = [
    path.join(PACKS_DIR, slug, "content.mdx"),
    path.join(ROOT_DIR, slug, "content.mdx"),
  ];

  for (const mdxPath of possiblePaths) {
    if (fs.existsSync(mdxPath)) {
      const content = fs.readFileSync(mdxPath, "utf-8");
      return content
        .replace(/^#+ .*/gm, "")
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/\*([^*]+)\*/g, "$1")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1")
        .replace(/```[\s\S]*?```/g, "")
        .slice(0, 500);
    }
  }
  return "";
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

function buildIRSearch(index: IRIndex): IRSearch {
  const invertedIndex: Record<string, SearchHit[]> = {};
  const entityLabels: Record<string, string[]> = {};

  // Process each entity
  for (const entity of index.entities) {
    // Skip sensitive/redacted entities in public search
    if (entity.sensitivity.level === "REDACTED") {
      continue;
    }

    // Build entity labels
    entityLabels[entity.id] = entity.labels;

    // Create citation for this entity
    const citation: Citation = {
      file: entity.provenance.file,
      yamlPath: entity.provenance.yamlPath,
      crystalId: entity.provenance.crystalId,
      contentHash: entity.provenance.contentHash,
    };

    // Collect all searchable text
    const searchableTexts: string[] = [...entity.labels];

    // Add attribute values if they're strings
    for (const [key, value] of Object.entries(entity.attrs)) {
      if (typeof value === "string") {
        searchableTexts.push(value);
      }
    }

    // Load content if this is a concept with a path
    if (entity.type === "Concept" && entity.attrs.path) {
      const slug = entity.attrs.slug as string;
      if (slug) {
        const content = loadContent(slug);
        if (content) {
          searchableTexts.push(content);
        }
      }
    }

    // Tokenize and build inverted index
    const allText = searchableTexts.join(" ");
    const tokens = [...new Set(tokenize(allText))];

    for (const token of tokens) {
      if (!invertedIndex[token]) {
        invertedIndex[token] = [];
      }

      // Calculate score based on where token appears
      let score = 1;
      if (entity.labels.some((l) => l.toLowerCase().includes(token))) {
        score = 10; // Higher score for label match
      } else if (
        entity.attrs.title &&
        (entity.attrs.title as string).toLowerCase().includes(token)
      ) {
        score = 8; // High score for title match
      } else if (
        entity.attrs.summary &&
        (entity.attrs.summary as string).toLowerCase().includes(token)
      ) {
        score = 5; // Medium score for summary match
      }

      invertedIndex[token].push({
        entityId: entity.id,
        score,
        citation,
      });
    }
  }

  // Sort inverted index entries for determinism
  const sortedInvertedIndex: Record<string, SearchHit[]> = {};
  for (const token of Object.keys(invertedIndex).sort()) {
    sortedInvertedIndex[token] = invertedIndex[token].sort((a, b) => {
      // Sort by score descending, then by entityId for stability
      const scoreCompare = b.score - a.score;
      if (scoreCompare !== 0) return scoreCompare;
      return a.entityId.localeCompare(b.entityId);
    });
  }

  // Sort entity labels
  const sortedEntityLabels: Record<string, string[]> = {};
  for (const entityId of Object.keys(entityLabels).sort()) {
    sortedEntityLabels[entityId] = entityLabels[entityId];
  }

  // Count unique tokens
  const tokenCount = Object.keys(sortedInvertedIndex).length;

  return {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      entry_count: Object.keys(sortedEntityLabels).length,
      token_count: tokenCount,
      content_hash: "", // Will be computed
    },
    invertedIndex: sortedInvertedIndex,
    entityLabels: sortedEntityLabels,
  };
}

function buildLegacySearch(
  legacyIndex: Record<string, unknown>
): LegacySearchIndex {
  const packs = (legacyIndex.packs || []) as Array<Record<string, unknown>>;
  const entries: LegacySearchEntry[] = [];

  for (const pack of packs) {
    const slug = pack.slug as string;
    const contentPreview = loadContent(slug);

    const allText = [
      pack.title as string,
      pack.summary as string,
      ...((pack.tags as string[]) || []),
      ...((pack.claims as string[]) || []),
      contentPreview,
    ].join(" ");

    const tokens = [...new Set(tokenize(allText))];

    entries.push({
      id: pack.id as string,
      title: pack.title as string,
      summary: pack.summary as string,
      tags: (pack.tags as string[]) || [],
      content_preview: contentPreview.slice(0, 200) + "...",
      tokens,
    });
  }

  // Sort for determinism
  entries.sort((a, b) => a.id.localeCompare(b.id));

  return {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      entry_count: entries.length,
    },
    entries,
  };
}

async function main(): Promise<void> {
  console.log("ORIGIN Search Index Builder (Extended)");
  console.log("======================================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Try IR index first
  const irIndex = loadIRIndex();
  if (irIndex) {
    console.log("Building IR search index from build/index.json...");

    const irSearch = buildIRSearch(irIndex);

    // Compute content hash
    const hashableContent = {
      invertedIndex: irSearch.invertedIndex,
      entityLabels: irSearch.entityLabels,
    };
    irSearch.metadata.content_hash = contentHash(hashableContent);

    // Write IR search index
    fs.writeFileSync(IR_OUTPUT_PATH, stableStringify(irSearch));
    console.log(`\u2713 IR search index written to ${IR_OUTPUT_PATH}`);
    console.log(
      `  ${irSearch.metadata.entry_count} entities, ${irSearch.metadata.token_count} tokens`
    );
    console.log(`  Content hash: ${irSearch.metadata.content_hash.slice(0, 16)}`);
  } else {
    console.log("Warning: build/index.json not found. Skipping IR search.");
  }

  // Build legacy search
  const legacyIndex = loadLegacyIndex();
  if (legacyIndex) {
    console.log("\nBuilding legacy search index from packs.index.json...");

    const legacySearch = buildLegacySearch(legacyIndex);

    // Write legacy search index
    fs.writeFileSync(LEGACY_OUTPUT_PATH, JSON.stringify(legacySearch, null, 2));
    console.log(`\u2713 Legacy search index written to ${LEGACY_OUTPUT_PATH}`);
    console.log(`  ${legacySearch.metadata.entry_count} entries indexed.`);
  } else {
    console.error("Error: packs.index.json not found. Run build:index first.");
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
