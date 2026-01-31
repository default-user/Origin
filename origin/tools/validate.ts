#!/usr/bin/env npx ts-node
/**
 * ORIGIN Pack Validator
 * Validates all pack.yaml files against schema/pack.schema.json
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";
import Ajv from "ajv";
import addFormats from "ajv-formats";

const PACKS_DIR = path.join(__dirname, "..", "knowledge", "packs");
const SCHEMA_PATH = path.join(__dirname, "..", "schema", "pack.schema.json");

interface ValidationResult {
  pack: string;
  valid: boolean;
  errors: string[];
}

async function loadSchema(): Promise<object> {
  const schemaContent = fs.readFileSync(SCHEMA_PATH, "utf-8");
  return JSON.parse(schemaContent);
}

async function loadPackYaml(packDir: string): Promise<object | null> {
  const yamlPath = path.join(packDir, "pack.yaml");
  if (!fs.existsSync(yamlPath)) {
    return null;
  }
  const content = fs.readFileSync(yamlPath, "utf-8");
  return yaml.load(content) as object;
}

async function validatePack(
  packDir: string,
  ajv: Ajv
): Promise<ValidationResult> {
  const packName = path.basename(packDir);
  const result: ValidationResult = {
    pack: packName,
    valid: false,
    errors: [],
  };

  try {
    const packData = await loadPackYaml(packDir);
    if (!packData) {
      result.errors.push("pack.yaml not found");
      return result;
    }

    const validate = ajv.getSchema("pack");
    if (!validate) {
      result.errors.push("Schema not loaded");
      return result;
    }

    const valid = validate(packData);
    if (valid) {
      result.valid = true;
    } else {
      result.errors = (validate.errors || []).map(
        (e) => `${e.instancePath} ${e.message}`
      );
    }
  } catch (err) {
    result.errors.push(`Parse error: ${(err as Error).message}`);
  }

  return result;
}

async function main(): Promise<void> {
  console.log("ORIGIN Pack Validator");
  console.log("=====================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load schema
  const schema = await loadSchema();
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);
  ajv.addSchema(schema, "pack");

  // Find all pack directories
  const packDirs = fs
    .readdirSync(PACKS_DIR)
    .filter((name) => {
      const fullPath = path.join(PACKS_DIR, name);
      return fs.statSync(fullPath).isDirectory();
    })
    .map((name) => path.join(PACKS_DIR, name));

  console.log(`Found ${packDirs.length} packs to validate.\n`);

  // Validate each pack
  const results: ValidationResult[] = [];
  for (const packDir of packDirs) {
    const result = await validatePack(packDir, ajv);
    results.push(result);

    const status = result.valid ? "✓" : "✗";
    console.log(`${status} ${result.pack}`);
    if (!result.valid) {
      result.errors.forEach((e) => console.log(`    ${e}`));
    }
  }

  // Summary
  const valid = results.filter((r) => r.valid).length;
  const invalid = results.filter((r) => !r.valid).length;

  console.log("\n---");
  console.log(`Valid: ${valid}/${results.length}`);
  console.log(`Invalid: ${invalid}/${results.length}`);

  if (invalid > 0) {
    process.exit(1);
  }

  console.log("\nAll packs validated successfully.");
}

main().catch((err) => {
  console.error("Validation failed:", err);
  process.exit(1);
});
