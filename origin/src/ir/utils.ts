/**
 * ORIGIN IR Utilities
 * Deterministic utilities for stable hashing, ID generation, and sorting
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as crypto from "crypto";
import {
  Entity,
  Edge,
  Fact,
  Sensitivity,
  SensitivityLevel,
  Provenance,
} from "./types";

// ============================================================================
// Stable JSON Stringify (sorted keys for deterministic hashing)
// ============================================================================

export function stableStringify(obj: unknown): string {
  return JSON.stringify(obj, sortedReplacer);
}

function sortedReplacer(_key: string, value: unknown): unknown {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const sorted: Record<string, unknown> = {};
    const keys = Object.keys(value as Record<string, unknown>).sort();
    for (const k of keys) {
      sorted[k] = (value as Record<string, unknown>)[k];
    }
    return sorted;
  }
  return value;
}

// ============================================================================
// Stable Hashing
// ============================================================================

export function stableHash(content: string): string {
  return crypto.createHash("sha256").update(content, "utf8").digest("hex");
}

export function contentHash(obj: unknown): string {
  return stableHash(stableStringify(obj));
}

// ============================================================================
// Stable ID Generation
// ============================================================================

export function generateEntityId(
  crystalId: string | null,
  yamlPath: string,
  entityType: string
): string {
  if (crystalId) {
    // Sanitize yamlPath for ID usage
    const pathPart = yamlPath.replace(/[^a-zA-Z0-9_]/g, "_");
    return `${crystalId}:${entityType}:${pathPart}`;
  }
  // Fallback: hash-based ID
  return `${entityType}:${stableHash(yamlPath).slice(0, 16)}`;
}

export function generateFactId(predicate: string, args: string[]): string {
  const argsStr = args.join(",");
  return `fact:${predicate}(${stableHash(argsStr).slice(0, 12)})`;
}

// ============================================================================
// Deterministic Sorting
// ============================================================================

export function sortEntities(entities: Entity[]): Entity[] {
  return [...entities].sort((a, b) => {
    const typeCompare = a.type.localeCompare(b.type);
    if (typeCompare !== 0) return typeCompare;
    return a.id.localeCompare(b.id);
  });
}

export function sortEdges(edges: Edge[]): Edge[] {
  return [...edges].sort((a, b) => {
    const srcCompare = a.src.localeCompare(b.src);
    if (srcCompare !== 0) return srcCompare;
    const relCompare = a.rel.localeCompare(b.rel);
    if (relCompare !== 0) return relCompare;
    return a.dst.localeCompare(b.dst);
  });
}

export function sortFacts(facts: Fact[]): Fact[] {
  return [...facts].sort((a, b) => {
    const predCompare = a.predicate.localeCompare(b.predicate);
    if (predCompare !== 0) return predCompare;
    const argsA = a.args.join(",");
    const argsB = b.args.join(",");
    return argsA.localeCompare(argsB);
  });
}

// ============================================================================
// Sensitivity Utilities
// ============================================================================

const SENSITIVITY_ORDER: Record<SensitivityLevel, number> = {
  PUBLIC: 0,
  SENSITIVE: 1,
  REDACTED: 2,
};

export function maxSensitivity(...levels: SensitivityLevel[]): SensitivityLevel {
  let max: SensitivityLevel = "PUBLIC";
  for (const level of levels) {
    if (SENSITIVITY_ORDER[level] > SENSITIVITY_ORDER[max]) {
      max = level;
    }
  }
  return max;
}

export function mergeSensitivity(...sensitivities: Sensitivity[]): Sensitivity {
  const levels = sensitivities.map((s) => s.level);
  const maxLevel = maxSensitivity(...levels);

  // PII risk: take highest
  const piiOrder = { none: 0, low: 1, medium: 2, high: 3 };
  let maxPii: "none" | "low" | "medium" | "high" = "none";
  for (const s of sensitivities) {
    if (piiOrder[s.pii_risk] > piiOrder[maxPii]) {
      maxPii = s.pii_risk;
    }
  }

  return {
    level: maxLevel,
    pii_risk: maxPii,
    contains_personal: sensitivities.some((s) => s.contains_personal),
    redacted: sensitivities.some((s) => s.redacted),
  };
}

export function deriveSensitivityLevel(
  piiRisk: string,
  containsPersonal: boolean,
  redacted: boolean
): SensitivityLevel {
  if (redacted) return "REDACTED";
  if (piiRisk === "high" || piiRisk === "medium") return "SENSITIVE";
  if (containsPersonal) return "SENSITIVE";
  return "PUBLIC";
}

export function createDefaultSensitivity(): Sensitivity {
  return {
    level: "PUBLIC",
    pii_risk: "none",
    contains_personal: false,
    redacted: false,
  };
}

// ============================================================================
// Provenance Utilities
// ============================================================================

export function createProvenance(
  file: string,
  yamlPath: string,
  content: unknown,
  crystalId: string | null,
  crystalRoot: string
): Provenance {
  return {
    file,
    yamlPath,
    contentHash: contentHash(content),
    crystalId,
    crystalRoot,
  };
}

export function mergeProvenances(provenances: Provenance[]): Provenance[] {
  // Deduplicate by contentHash
  const seen = new Set<string>();
  const result: Provenance[] = [];
  for (const p of provenances) {
    if (!seen.has(p.contentHash)) {
      seen.add(p.contentHash);
      result.push(p);
    }
  }
  // Sort for determinism
  return result.sort((a, b) => {
    const fileCompare = a.file.localeCompare(b.file);
    if (fileCompare !== 0) return fileCompare;
    return a.yamlPath.localeCompare(b.yamlPath);
  });
}

// ============================================================================
// Privacy Boundary Check
// ============================================================================

export function isAccessible(
  sensitivity: Sensitivity,
  allowSensitive: boolean,
  allowRedacted: boolean
): boolean {
  if (sensitivity.level === "REDACTED") {
    return allowRedacted;
  }
  if (sensitivity.level === "SENSITIVE") {
    return allowSensitive;
  }
  return true; // PUBLIC is always accessible
}

export function filterByPrivacy<T extends { sensitivity: Sensitivity }>(
  items: T[],
  allowSensitive: boolean,
  allowRedacted: boolean
): T[] {
  return items.filter((item) =>
    isAccessible(item.sensitivity, allowSensitive, allowRedacted)
  );
}
