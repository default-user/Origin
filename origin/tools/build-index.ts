#!/usr/bin/env npx ts-node
/**
 * ORIGIN Index Builder
 * Builds knowledge/dist/packs.index.json from pack.yaml files
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

const PACKS_DIR = path.join(__dirname, "..", "knowledge", "packs");
const DIST_DIR = path.join(__dirname, "..", "knowledge", "dist");
const OUTPUT_PATH = path.join(DIST_DIR, "packs.index.json");

interface PackMetadata {
  id: string;
  title: string;
  summary: string;
  authorship: string;
  disclosure_tier: string;
  tags: string[];
  created_date: string;
  updated_date: string;
  status: string;
  parents: string[];
  children: string[];
  related: string[];
  claims: string[];
  tests_or_falsifiers: Array<{
    name: string;
    description: string;
    falsification_condition: string;
  }>;
  slug: string;
  path: string;
}

interface PacksIndex {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    pack_count: number;
  };
  packs: PackMetadata[];
}

async function loadPackYaml(packDir: string): Promise<object | null> {
  const yamlPath = path.join(packDir, "pack.yaml");
  if (!fs.existsSync(yamlPath)) {
    return null;
  }
  const content = fs.readFileSync(yamlPath, "utf-8");
  return yaml.load(content) as object;
}

async function main(): Promise<void> {
  console.log("ORIGIN Index Builder");
  console.log("====================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Ensure dist directory exists
  if (!fs.existsSync(DIST_DIR)) {
    fs.mkdirSync(DIST_DIR, { recursive: true });
  }

  // Find all pack directories
  const packDirs = fs
    .readdirSync(PACKS_DIR)
    .filter((name) => {
      const fullPath = path.join(PACKS_DIR, name);
      return fs.statSync(fullPath).isDirectory();
    })
    .sort();

  console.log(`Found ${packDirs.length} packs.\n`);

  const packs: PackMetadata[] = [];

  for (const dirName of packDirs) {
    const packDir = path.join(PACKS_DIR, dirName);
    const packData = (await loadPackYaml(packDir)) as any;

    if (!packData) {
      console.log(`⚠ ${dirName}: no pack.yaml`);
      continue;
    }

    const metadata: PackMetadata = {
      id: packData.id || "",
      title: packData.title || "",
      summary: packData.summary || "",
      authorship: packData.authorship || "Ande + Kai (OI) + Whānau (OIs)",
      disclosure_tier: packData.disclosure_tier || "public",
      tags: packData.tags || [],
      created_date: packData.created_date || "",
      updated_date: packData.updated_date || "",
      status: packData.status || "draft",
      parents: packData.parents || [],
      children: packData.children || [],
      related: packData.related || [],
      claims: packData.claims || [],
      tests_or_falsifiers: packData.tests_or_falsifiers || [],
      slug: dirName,
      path: `knowledge/packs/${dirName}`,
    };

    packs.push(metadata);
    console.log(`✓ ${metadata.id}: ${metadata.title}`);
  }

  // Build index
  const index: PacksIndex = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      pack_count: packs.length,
    },
    packs,
  };

  // Write output
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(index, null, 2));

  console.log(`\n✓ Written ${OUTPUT_PATH}`);
  console.log(`  ${packs.length} packs indexed.`);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
