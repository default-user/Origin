#!/usr/bin/env npx ts-node
/**
 * ORIGIN Determinism Check
 * Verifies that the build pipeline produces identical outputs on consecutive runs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as crypto from "crypto";
import { execSync } from "child_process";

const ROOT_DIR = path.join(__dirname, "..");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const TEMP_DIR_1 = path.join(ROOT_DIR, ".determinism-check-1");
const TEMP_DIR_2 = path.join(ROOT_DIR, ".determinism-check-2");

const BUILD_ARTIFACTS = [
  "index.json",
  "graph.json",
  "search.json",
];

function hashFile(filePath: string): string {
  if (!fs.existsSync(filePath)) {
    return "MISSING";
  }

  const content = fs.readFileSync(filePath, "utf-8");
  // Parse and re-stringify to normalize (remove timestamp fields)
  try {
    const parsed = JSON.parse(content);
    // Remove timestamp-dependent fields
    if (parsed.metadata) {
      delete parsed.metadata.generated_at;
    }
    const normalized = JSON.stringify(parsed, Object.keys(parsed).sort());
    return crypto.createHash("sha256").update(normalized).digest("hex");
  } catch {
    // If not JSON, hash raw content
    return crypto.createHash("sha256").update(content).digest("hex");
  }
}

function copyDir(src: string, dst: string): void {
  if (!fs.existsSync(dst)) {
    fs.mkdirSync(dst, { recursive: true });
  }

  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const dstPath = path.join(dst, entry.name);

    if (entry.isDirectory()) {
      copyDir(srcPath, dstPath);
    } else {
      fs.copyFileSync(srcPath, dstPath);
    }
  }
}

function cleanDir(dir: string): void {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function runBuild(): void {
  execSync("npm run build:index", {
    cwd: ROOT_DIR,
    stdio: ["pipe", "pipe", "pipe"],
  });
  execSync("npm run build:graph", {
    cwd: ROOT_DIR,
    stdio: ["pipe", "pipe", "pipe"],
  });
  execSync("npm run build:search", {
    cwd: ROOT_DIR,
    stdio: ["pipe", "pipe", "pipe"],
  });
}

async function main(): Promise<void> {
  console.log("ORIGIN Determinism Check");
  console.log("========================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  console.log("This check verifies that the build pipeline produces");
  console.log("identical outputs on consecutive runs.\n");

  // Clean up
  cleanDir(TEMP_DIR_1);
  cleanDir(TEMP_DIR_2);

  try {
    // First run
    console.log("Run 1: Building...");
    runBuild();
    fs.mkdirSync(TEMP_DIR_1, { recursive: true });
    for (const artifact of BUILD_ARTIFACTS) {
      const src = path.join(BUILD_DIR, artifact);
      const dst = path.join(TEMP_DIR_1, artifact);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, dst);
      }
    }
    console.log("  Done.\n");

    // Second run
    console.log("Run 2: Building...");
    runBuild();
    fs.mkdirSync(TEMP_DIR_2, { recursive: true });
    for (const artifact of BUILD_ARTIFACTS) {
      const src = path.join(BUILD_DIR, artifact);
      const dst = path.join(TEMP_DIR_2, artifact);
      if (fs.existsSync(src)) {
        fs.copyFileSync(src, dst);
      }
    }
    console.log("  Done.\n");

    // Compare
    console.log("Comparing artifacts:");
    console.log("--------------------");

    let allMatch = true;
    const results: Array<{ artifact: string; match: boolean; hash1: string; hash2: string }> = [];

    for (const artifact of BUILD_ARTIFACTS) {
      const path1 = path.join(TEMP_DIR_1, artifact);
      const path2 = path.join(TEMP_DIR_2, artifact);

      const hash1 = hashFile(path1);
      const hash2 = hashFile(path2);

      const match = hash1 === hash2;
      allMatch = allMatch && match;

      results.push({ artifact, match, hash1, hash2 });

      const status = match ? "\u2713" : "\u2717";
      console.log(`  ${status} ${artifact}`);
      console.log(`      Run 1: ${hash1.slice(0, 16)}...`);
      console.log(`      Run 2: ${hash2.slice(0, 16)}...`);
    }

    console.log("\n---");

    if (allMatch) {
      console.log("\u2713 DETERMINISM CHECK PASSED");
      console.log("  All artifacts are identical across runs.");
    } else {
      console.log("\u2717 DETERMINISM CHECK FAILED");
      console.log("  Some artifacts differ between runs.");
      console.log("");
      console.log("  Failed artifacts:");
      for (const result of results.filter((r) => !r.match)) {
        console.log(`    - ${result.artifact}`);
      }
      process.exit(1);
    }
  } finally {
    // Clean up
    cleanDir(TEMP_DIR_1);
    cleanDir(TEMP_DIR_2);
  }
}

main().catch((err) => {
  console.error("Determinism check failed:", err);
  cleanDir(TEMP_DIR_1);
  cleanDir(TEMP_DIR_2);
  process.exit(1);
});
