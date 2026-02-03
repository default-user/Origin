#!/usr/bin/env npx ts-node
/**
 * ORIGIN Pack Validator (Extended)
 * Validates crystals from all configured roots against schemas
 * Produces deterministic report artifact at build/reports/validate.json
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";
import Ajv from "ajv";
import addFormats from "ajv-formats";

import {
  ValidationReport,
  ValidationResult,
  ValidationError,
  CrystalRootsConfig,
} from "../src/ir/types";
import { stableStringify, contentHash } from "../src/ir/utils";

const ROOT_DIR = path.join(__dirname, "..");
const CONFIG_PATH = path.join(ROOT_DIR, "config", "crystal_roots.json");
const REPORTS_DIR = path.join(ROOT_DIR, "build", "reports");
const OUTPUT_PATH = path.join(REPORTS_DIR, "validate.json");

// Legacy fallback paths
const LEGACY_PACKS_DIR = path.join(ROOT_DIR, "knowledge", "packs");
const LEGACY_SCHEMA_PATH = path.join(ROOT_DIR, "schema", "pack.schema.json");

interface LoadedCrystal {
  file: string;
  yamlPath: string;
  crystalId: string | null;
  crystalRoot: string;
  data: unknown;
}

function loadConfig(): CrystalRootsConfig {
  if (fs.existsSync(CONFIG_PATH)) {
    const content = fs.readFileSync(CONFIG_PATH, "utf-8");
    return JSON.parse(content) as CrystalRootsConfig;
  }
  // Legacy fallback
  return {
    roots: ["knowledge/packs"],
    defaultSchema: "schema/pack.schema.json",
  };
}

function loadSchema(schemaPath: string): object {
  const fullPath = path.join(ROOT_DIR, schemaPath);
  if (!fs.existsSync(fullPath)) {
    throw new Error(`Schema not found: ${fullPath}`);
  }
  const schemaContent = fs.readFileSync(fullPath, "utf-8");
  const schema = JSON.parse(schemaContent) as Record<string, unknown>;
  // Remove $schema to avoid meta-schema validation issues with AJV
  delete schema.$schema;
  return schema;
}

function discoverCrystals(rootPath: string, crystalRoot: string): string[] {
  const crystals: string[] = [];
  const fullRootPath = path.join(ROOT_DIR, rootPath);

  if (!fs.existsSync(fullRootPath)) {
    console.warn(`Warning: Crystal root not found: ${fullRootPath}`);
    return [];
  }

  const dirs = fs.readdirSync(fullRootPath).sort(); // Deterministic order

  for (const dirName of dirs) {
    const dirPath = path.join(fullRootPath, dirName);
    if (fs.statSync(dirPath).isDirectory()) {
      const yamlPath = path.join(dirPath, "pack.yaml");
      if (fs.existsSync(yamlPath)) {
        crystals.push(yamlPath);
      }
    }
  }

  return crystals;
}

function loadCrystal(filePath: string, crystalRoot: string): LoadedCrystal | null {
  try {
    const content = fs.readFileSync(filePath, "utf-8");
    const data = yaml.load(content);
    const relativePath = path.relative(ROOT_DIR, filePath);
    const crystalId = (data as Record<string, unknown>)?.id as string | null;

    return {
      file: relativePath,
      yamlPath: ".",
      crystalId: crystalId || null,
      crystalRoot,
      data,
    };
  } catch (err) {
    return null;
  }
}

function validateCrystal(
  crystal: LoadedCrystal,
  ajv: Ajv,
  schemaId: string
): ValidationResult {
  const result: ValidationResult = {
    file: crystal.file,
    yamlPath: crystal.yamlPath,
    crystalId: crystal.crystalId,
    crystalRoot: crystal.crystalRoot,
    valid: false,
    errors: [],
  };

  try {
    const validate = ajv.getSchema(schemaId);
    if (!validate) {
      result.errors.push({
        path: "",
        message: `Schema '${schemaId}' not loaded`,
      });
      return result;
    }

    const valid = validate(crystal.data);
    if (valid) {
      result.valid = true;
    } else {
      // Sort errors for determinism
      const errors = (validate.errors || [])
        .map((e) => ({
          path: e.instancePath || "",
          message: e.message || "Unknown error",
          schemaPath: e.schemaPath,
        }))
        .sort((a, b) => {
          const pathCompare = a.path.localeCompare(b.path);
          if (pathCompare !== 0) return pathCompare;
          return (a.message || "").localeCompare(b.message || "");
        });
      result.errors = errors;
    }
  } catch (err) {
    result.errors.push({
      path: "",
      message: `Parse error: ${(err as Error).message}`,
    });
  }

  return result;
}

async function main(): Promise<void> {
  console.log("ORIGIN Pack Validator (Extended)");
  console.log("================================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Ensure reports directory exists
  if (!fs.existsSync(REPORTS_DIR)) {
    fs.mkdirSync(REPORTS_DIR, { recursive: true });
  }

  // Load configuration
  const config = loadConfig();
  console.log(`Loaded ${config.roots.length} crystal root(s).\n`);

  // Setup AJV
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);

  // Load default schema
  const defaultSchemaPath = config.defaultSchema || "schema/pack.schema.json";
  const defaultSchema = loadSchema(defaultSchemaPath);
  ajv.addSchema(defaultSchema, "pack");

  // Load schema overrides
  for (const [rootPath, schemaPath] of Object.entries(config.schemaOverrides || {})) {
    const schema = loadSchema(schemaPath);
    const schemaId = `schema:${rootPath}`;
    ajv.addSchema(schema, schemaId);
  }

  // Discover and validate all crystals
  const allResults: ValidationResult[] = [];
  let totalCrystals = 0;

  for (const rootPath of config.roots.sort()) {
    // Sorted for determinism
    console.log(`Processing root: ${rootPath}`);

    const schemaId =
      config.schemaOverrides?.[rootPath] ? `schema:${rootPath}` : "pack";

    const crystalFiles = discoverCrystals(rootPath, rootPath);
    console.log(`  Found ${crystalFiles.length} crystal(s).\n`);

    for (const filePath of crystalFiles) {
      const crystal = loadCrystal(filePath, rootPath);
      if (!crystal) {
        allResults.push({
          file: path.relative(ROOT_DIR, filePath),
          yamlPath: ".",
          crystalId: null,
          crystalRoot: rootPath,
          valid: false,
          errors: [{ path: "", message: "Failed to load crystal file" }],
        });
        totalCrystals++;
        continue;
      }

      const result = validateCrystal(crystal, ajv, schemaId);
      allResults.push(result);
      totalCrystals++;

      const status = result.valid ? "\u2713" : "\u2717";
      const id = result.crystalId || path.basename(path.dirname(filePath));
      console.log(`  ${status} ${id}`);
      if (!result.valid) {
        result.errors.forEach((e) =>
          console.log(`      ${e.path} ${e.message}`)
        );
      }
    }
  }

  // Sort results for determinism
  allResults.sort((a, b) => {
    const rootCompare = a.crystalRoot.localeCompare(b.crystalRoot);
    if (rootCompare !== 0) return rootCompare;
    return a.file.localeCompare(b.file);
  });

  // Build report
  const validCount = allResults.filter((r) => r.valid).length;
  const invalidCount = allResults.filter((r) => !r.valid).length;

  const report: ValidationReport = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      total_crystals: totalCrystals,
      valid_count: validCount,
      invalid_count: invalidCount,
    },
    results: allResults,
  };

  // Write report with deterministic formatting
  fs.writeFileSync(OUTPUT_PATH, stableStringify(report));

  // Summary
  console.log("\n---");
  console.log(`Valid: ${validCount}/${totalCrystals}`);
  console.log(`Invalid: ${invalidCount}/${totalCrystals}`);
  console.log(`\n\u2713 Report written to ${OUTPUT_PATH}`);
  console.log(`  Content hash: ${contentHash(report).slice(0, 16)}`);

  if (invalidCount > 0) {
    process.exit(1);
  }

  console.log("\nAll crystals validated successfully.");
}

main().catch((err) => {
  console.error("Validation failed:", err);
  process.exit(1);
});
