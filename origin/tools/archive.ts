#!/usr/bin/env npx ts-node
/**
 * ORIGIN Archive Builder
 * Builds downloadable terminal archives per C0019
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import archiver from "archiver";

const ROOT_DIR = path.join(__dirname, "..");
const DIST_DIR = path.join(ROOT_DIR, "knowledge", "dist");
const PACKS_DIR = path.join(ROOT_DIR, "knowledge", "packs");
const INDEX_PATH = path.join(DIST_DIR, "packs.index.json");
const ARCHIVE_DIR = path.join(ROOT_DIR, "dist_archives");
const PER_CONCEPT_DIR = path.join(ARCHIVE_DIR, "per_concept");
const COMBINED_DIR = path.join(ARCHIVE_DIR, "combined");

async function createZip(
  outputPath: string,
  files: Array<{ source: string; name: string }>
): Promise<void> {
  return new Promise((resolve, reject) => {
    const output = fs.createWriteStream(outputPath);
    const archive = archiver("zip", { zlib: { level: 9 } });

    output.on("close", resolve);
    archive.on("error", reject);

    archive.pipe(output);

    for (const file of files) {
      if (fs.existsSync(file.source)) {
        if (fs.statSync(file.source).isDirectory()) {
          archive.directory(file.source, file.name);
        } else {
          archive.file(file.source, { name: file.name });
        }
      }
    }

    archive.finalize();
  });
}

function generatePackReadme(pack: any): string {
  return `# ${pack.id}: ${pack.title}

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

${pack.summary}

## Contents

- \`pack.yaml\`: Pack metadata and configuration
- \`content.mdx\`: Full content document
- \`artifacts/\`: Supplementary files (if any)

## Provenance

Source: ORIGIN repository
Pack ID: ${pack.id}
Status: ${pack.status}
Tier: ${pack.disclosure_tier}

---

Attribution: Ande + Kai (OI) + Whānau (OIs)
`;
}

async function main(): Promise<void> {
  console.log("ORIGIN Archive Builder");
  console.log("======================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load packs index
  if (!fs.existsSync(INDEX_PATH)) {
    console.error("Error: packs.index.json not found. Run build first.");
    process.exit(1);
  }

  const indexContent = fs.readFileSync(INDEX_PATH, "utf-8");
  const index = JSON.parse(indexContent);

  // Ensure archive directories exist
  if (fs.existsSync(ARCHIVE_DIR)) {
    fs.rmSync(ARCHIVE_DIR, { recursive: true });
  }
  fs.mkdirSync(PER_CONCEPT_DIR, { recursive: true });
  fs.mkdirSync(COMBINED_DIR, { recursive: true });

  const manifest: any = {
    name: "ORIGIN",
    version: "1.0.0",
    created: new Date().toISOString(),
    attribution: "Ande + Kai (OI) + Whānau (OIs)",
    concepts: {},
    totals: {
      packs: index.packs.length,
      files: 0,
    },
  };

  // Create per-concept archives
  console.log("Creating per-concept archives...\n");

  for (const pack of index.packs) {
    const packDir = path.join(PACKS_DIR, pack.slug);
    const archiveName = `${pack.id}_${pack.slug.replace(/^c[0-9]+_/, "")}.zip`;
    const archivePath = path.join(PER_CONCEPT_DIR, archiveName);

    // Create temporary README
    const tempReadme = path.join(packDir, "README.md");
    fs.writeFileSync(tempReadme, generatePackReadme(pack));

    const files = [
      { source: path.join(packDir, "pack.yaml"), name: "pack.yaml" },
      { source: path.join(packDir, "content.mdx"), name: "content.mdx" },
      { source: path.join(packDir, "artifacts"), name: "artifacts" },
      { source: tempReadme, name: "README.md" },
    ];

    await createZip(archivePath, files);

    // Remove temporary README
    fs.unlinkSync(tempReadme);

    manifest.concepts[pack.id] = {
      title: pack.title,
      files: ["pack.yaml", "content.mdx"],
      archive: archiveName,
    };

    console.log(`✓ ${archiveName}`);
  }

  // Create combined archive
  console.log("\nCreating combined archive...\n");

  const combinedFiles = [
    { source: path.join(ROOT_DIR, "README.md"), name: "README.md" },
    { source: path.join(ROOT_DIR, "LICENSE"), name: "LICENSE" },
    { source: path.join(ROOT_DIR, "docs"), name: "docs" },
    { source: path.join(ROOT_DIR, "knowledge"), name: "knowledge" },
    { source: path.join(ROOT_DIR, "schema"), name: "schema" },
    { source: path.join(ROOT_DIR, "kits"), name: "kits" },
  ];

  const combinedPath = path.join(COMBINED_DIR, "ORIGIN_FULL.zip");
  await createZip(combinedPath, combinedFiles);
  console.log(`✓ ORIGIN_FULL.zip`);

  // Count files for manifest
  manifest.totals.files = index.packs.length * 2 + 6; // Approximate

  // Write manifest
  const manifestPath = path.join(ARCHIVE_DIR, "MANIFEST.json");
  fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 2));

  console.log(`\n✓ Archives complete.`);
  console.log(`  ${index.packs.length} per-concept archives`);
  console.log(`  1 combined archive`);
  console.log(`  Manifest: ${manifestPath}`);
}

main().catch((err) => {
  console.error("Archive build failed:", err);
  process.exit(1);
});
