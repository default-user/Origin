#!/usr/bin/env npx ts-node
/**
 * ORIGIN Index Builder (Extended)
 * Builds both legacy packs.index.json and new IR-based build/index.json
 * with full provenance tracking for deterministic reasoning
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

import {
  Entity,
  Edge,
  Fact,
  Provenance,
  Sensitivity,
  SensitivityLevel,
  IRIndex,
  CrystalRootsConfig,
  EntityType,
  RelationType,
} from "../src/ir/types";
import {
  stableStringify,
  contentHash,
  createProvenance,
  deriveSensitivityLevel,
  sortEntities,
  sortEdges,
  sortFacts,
  generateEntityId,
} from "../src/ir/utils";

const ROOT_DIR = path.join(__dirname, "..");
const CONFIG_PATH = path.join(ROOT_DIR, "config", "crystal_roots.json");
const LEGACY_DIST_DIR = path.join(ROOT_DIR, "knowledge", "dist");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const LEGACY_OUTPUT_PATH = path.join(LEGACY_DIST_DIR, "packs.index.json");
const IR_OUTPUT_PATH = path.join(BUILD_DIR, "index.json");

// Legacy interface for backward compatibility
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

interface LoadedCrystal {
  file: string;
  crystalId: string | null;
  crystalRoot: string;
  data: Record<string, unknown>;
  dirName: string;
}

function loadConfig(): CrystalRootsConfig {
  if (fs.existsSync(CONFIG_PATH)) {
    const content = fs.readFileSync(CONFIG_PATH, "utf-8");
    return JSON.parse(content) as CrystalRootsConfig;
  }
  return {
    roots: ["knowledge/packs"],
    defaultSchema: "schema/pack.schema.json",
  };
}

function discoverCrystals(rootPath: string): LoadedCrystal[] {
  const crystals: LoadedCrystal[] = [];
  const fullRootPath = path.join(ROOT_DIR, rootPath);

  if (!fs.existsSync(fullRootPath)) {
    console.warn(`Warning: Crystal root not found: ${fullRootPath}`);
    return [];
  }

  const dirs = fs.readdirSync(fullRootPath).sort();

  for (const dirName of dirs) {
    const dirPath = path.join(fullRootPath, dirName);
    if (fs.statSync(dirPath).isDirectory()) {
      const yamlPath = path.join(dirPath, "pack.yaml");
      if (fs.existsSync(yamlPath)) {
        try {
          const content = fs.readFileSync(yamlPath, "utf-8");
          const data = yaml.load(content) as Record<string, unknown>;
          crystals.push({
            file: path.relative(ROOT_DIR, yamlPath),
            crystalId: (data.id as string) || null,
            crystalRoot: rootPath,
            data,
            dirName,
          });
        } catch (err) {
          console.warn(`  Warning: Failed to load ${yamlPath}`);
        }
      }
    }
  }

  return crystals;
}

function deriveSensitivity(data: Record<string, unknown>): Sensitivity {
  const sens = data.sensitivity as Record<string, unknown> | undefined;
  const piiRisk = (sens?.pii_risk as string) || "none";
  const containsPersonal = (sens?.contains_personal as boolean) || false;
  const redacted = (sens?.redacted as boolean) || false;

  return {
    level: deriveSensitivityLevel(piiRisk, containsPersonal, redacted),
    pii_risk: piiRisk as "none" | "low" | "medium" | "high",
    contains_personal: containsPersonal,
    redacted,
  };
}

function extractEntities(crystal: LoadedCrystal): Entity[] {
  const entities: Entity[] = [];
  const data = crystal.data;
  const crystalId = crystal.crystalId;
  const sensitivity = deriveSensitivity(data);

  // Main concept entity
  const conceptId = crystalId || generateEntityId(null, crystal.file, "Concept");
  entities.push({
    id: conceptId,
    type: "Concept",
    labels: [
      data.title as string,
      ...(data.tags as string[] || []),
    ].filter(Boolean),
    attrs: {
      title: data.title,
      summary: data.summary,
      authorship: data.authorship,
      disclosure_tier: data.disclosure_tier,
      status: data.status,
      created_date: data.created_date,
      updated_date: data.updated_date,
      slug: crystal.dirName,
      path: `${crystal.crystalRoot}/${crystal.dirName}`,
    },
    provenance: createProvenance(
      crystal.file,
      ".",
      data,
      crystalId,
      crystal.crystalRoot
    ),
    sensitivity,
  });

  // Claim entities
  const claims = (data.claims as string[]) || [];
  claims.forEach((claim, idx) => {
    const claimId = generateEntityId(crystalId, `claims[${idx}]`, "Claim");
    entities.push({
      id: claimId,
      type: "Claim",
      labels: [claim.slice(0, 100)],
      attrs: {
        text: claim,
        index: idx,
        parentConcept: conceptId,
      },
      provenance: createProvenance(
        crystal.file,
        `claims[${idx}]`,
        claim,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  // Test entities
  const tests = (data.tests_or_falsifiers as Array<Record<string, unknown>>) || [];
  tests.forEach((test, idx) => {
    const testId = generateEntityId(crystalId, `tests[${idx}]`, "Test");
    entities.push({
      id: testId,
      type: "Test",
      labels: [test.name as string].filter(Boolean),
      attrs: {
        name: test.name,
        description: test.description,
        falsification_condition: test.falsification_condition,
        index: idx,
        parentConcept: conceptId,
      },
      provenance: createProvenance(
        crystal.file,
        `tests_or_falsifiers[${idx}]`,
        test,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  // Tag entities (pseudo-entities for graph traversal)
  const tags = (data.tags as string[]) || [];
  tags.forEach((tag) => {
    const tagId = `tag:${tag}`;
    // Only add if not already in our list
    if (!entities.some((e) => e.id === tagId)) {
      entities.push({
        id: tagId,
        type: "Tag",
        labels: [tag],
        attrs: { name: tag },
        provenance: createProvenance(
          crystal.file,
          `tags`,
          tag,
          crystalId,
          crystal.crystalRoot
        ),
        sensitivity: {
          level: "PUBLIC",
          pii_risk: "none",
          contains_personal: false,
          redacted: false,
        },
      });
    }
  });

  return entities;
}

function extractEdges(crystal: LoadedCrystal, entities: Entity[]): Edge[] {
  const edges: Edge[] = [];
  const data = crystal.data;
  const crystalId = crystal.crystalId;
  const conceptId = crystalId || entities.find((e) => e.type === "Concept")?.id;
  if (!conceptId) return edges;

  const sensitivity = deriveSensitivity(data);

  // Parent edges
  const parents = (data.parents as string[]) || [];
  parents.forEach((parentId) => {
    edges.push({
      src: parentId,
      rel: "parent",
      dst: conceptId,
      attrs: {},
      provenance: createProvenance(
        crystal.file,
        "parents",
        parents,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  // Child edges
  const children = (data.children as string[]) || [];
  children.forEach((childId) => {
    edges.push({
      src: conceptId,
      rel: "child",
      dst: childId,
      attrs: {},
      provenance: createProvenance(
        crystal.file,
        "children",
        children,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  // Related edges
  const related = (data.related as string[]) || [];
  related.forEach((relatedId) => {
    edges.push({
      src: conceptId,
      rel: "related",
      dst: relatedId,
      attrs: {},
      provenance: createProvenance(
        crystal.file,
        "related",
        related,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  // Claim edges
  const claims = entities.filter((e) => e.type === "Claim");
  claims.forEach((claim) => {
    edges.push({
      src: conceptId,
      rel: "claims",
      dst: claim.id,
      attrs: {},
      provenance: claim.provenance,
      sensitivity,
    });
  });

  // Test edges
  const tests = entities.filter((e) => e.type === "Test");
  tests.forEach((test) => {
    edges.push({
      src: conceptId,
      rel: "tests",
      dst: test.id,
      attrs: {},
      provenance: test.provenance,
      sensitivity,
    });
  });

  // Tag edges
  const tags = (data.tags as string[]) || [];
  tags.forEach((tag) => {
    edges.push({
      src: conceptId,
      rel: "tagged",
      dst: `tag:${tag}`,
      attrs: {},
      provenance: createProvenance(
        crystal.file,
        "tags",
        tags,
        crystalId,
        crystal.crystalRoot
      ),
      sensitivity,
    });
  });

  return edges;
}

function extractFacts(crystal: LoadedCrystal, entities: Entity[]): Fact[] {
  const facts: Fact[] = [];
  const data = crystal.data;
  const crystalId = crystal.crystalId;
  const conceptId = crystalId || entities.find((e) => e.type === "Concept")?.id;
  if (!conceptId) return facts;

  const sensitivity = deriveSensitivity(data);
  const prov = createProvenance(
    crystal.file,
    ".",
    data,
    crystalId,
    crystal.crystalRoot
  );

  // Type fact
  facts.push({
    predicate: "type",
    args: [conceptId, "Concept"],
    derived: false,
    provenance: [prov],
    sensitivity,
  });

  // Title fact
  if (data.title) {
    facts.push({
      predicate: "hasTitle",
      args: [conceptId, data.title as string],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  }

  // Summary fact
  if (data.summary) {
    facts.push({
      predicate: "hasSummary",
      args: [conceptId, data.summary as string],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  }

  // Status fact
  if (data.status) {
    facts.push({
      predicate: "hasStatus",
      args: [conceptId, data.status as string],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  }

  // Disclosure tier fact
  if (data.disclosure_tier) {
    facts.push({
      predicate: "hasTier",
      args: [conceptId, data.disclosure_tier as string],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  }

  // Tag facts
  const tags = (data.tags as string[]) || [];
  tags.forEach((tag, idx) => {
    facts.push({
      predicate: "hasTag",
      args: [conceptId, tag],
      derived: false,
      provenance: [
        createProvenance(
          crystal.file,
          `tags[${idx}]`,
          tag,
          crystalId,
          crystal.crystalRoot
        ),
      ],
      sensitivity,
    });
  });

  // Edge facts for parent/child/related
  const parents = (data.parents as string[]) || [];
  parents.forEach((parentId) => {
    facts.push({
      predicate: "edge",
      args: [parentId, "parent", conceptId],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  });

  const children = (data.children as string[]) || [];
  children.forEach((childId) => {
    facts.push({
      predicate: "edge",
      args: [conceptId, "child", childId],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  });

  const related = (data.related as string[]) || [];
  related.forEach((relatedId) => {
    facts.push({
      predicate: "edge",
      args: [conceptId, "related", relatedId],
      derived: false,
      provenance: [prov],
      sensitivity,
    });
  });

  // Claim facts
  const claims = (data.claims as string[]) || [];
  claims.forEach((claim, idx) => {
    const claimId = generateEntityId(crystalId, `claims[${idx}]`, "Claim");
    facts.push({
      predicate: "claims",
      args: [conceptId, claimId],
      derived: false,
      provenance: [
        createProvenance(
          crystal.file,
          `claims[${idx}]`,
          claim,
          crystalId,
          crystal.crystalRoot
        ),
      ],
      sensitivity,
    });
    facts.push({
      predicate: "claimText",
      args: [claimId, claim],
      derived: false,
      provenance: [
        createProvenance(
          crystal.file,
          `claims[${idx}]`,
          claim,
          crystalId,
          crystal.crystalRoot
        ),
      ],
      sensitivity,
    });
  });

  return facts;
}

function buildLegacyIndex(crystals: LoadedCrystal[]): PacksIndex {
  const packs: PackMetadata[] = [];

  for (const crystal of crystals) {
    const data = crystal.data;
    packs.push({
      id: (data.id as string) || "",
      title: (data.title as string) || "",
      summary: (data.summary as string) || "",
      authorship: (data.authorship as string) || "Ande + Kai (OI) + Whānau (OIs)",
      disclosure_tier: (data.disclosure_tier as string) || "public",
      tags: (data.tags as string[]) || [],
      created_date: (data.created_date as string) || "",
      updated_date: (data.updated_date as string) || "",
      status: (data.status as string) || "draft",
      parents: (data.parents as string[]) || [],
      children: (data.children as string[]) || [],
      related: (data.related as string[]) || [],
      claims: (data.claims as string[]) || [],
      tests_or_falsifiers:
        (data.tests_or_falsifiers as PackMetadata["tests_or_falsifiers"]) || [],
      slug: crystal.dirName,
      path: `${crystal.crystalRoot}/${crystal.dirName}`,
    });
  }

  return {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      pack_count: packs.length,
    },
    packs,
  };
}

async function main(): Promise<void> {
  console.log("ORIGIN Index Builder (Extended)");
  console.log("===============================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Ensure directories exist
  if (!fs.existsSync(LEGACY_DIST_DIR)) {
    fs.mkdirSync(LEGACY_DIST_DIR, { recursive: true });
  }
  if (!fs.existsSync(BUILD_DIR)) {
    fs.mkdirSync(BUILD_DIR, { recursive: true });
  }

  // Load configuration
  const config = loadConfig();
  console.log(`Loaded ${config.roots.length} crystal root(s).\n`);

  // Collect all crystals
  const allCrystals: LoadedCrystal[] = [];
  for (const rootPath of config.roots.sort()) {
    console.log(`Processing root: ${rootPath}`);
    const crystals = discoverCrystals(rootPath);
    console.log(`  Found ${crystals.length} crystal(s).\n`);
    allCrystals.push(...crystals);
  }

  // Sort crystals by ID for determinism
  allCrystals.sort((a, b) => {
    const idA = a.crystalId || a.dirName;
    const idB = b.crystalId || b.dirName;
    return idA.localeCompare(idB);
  });

  // Extract IR elements
  let allEntities: Entity[] = [];
  let allEdges: Edge[] = [];
  let allFacts: Fact[] = [];

  for (const crystal of allCrystals) {
    const entities = extractEntities(crystal);
    const edges = extractEdges(crystal, entities);
    const facts = extractFacts(crystal, entities);

    allEntities.push(...entities);
    allEdges.push(...edges);
    allFacts.push(...facts);

    const id = crystal.crystalId || crystal.dirName;
    console.log(`\u2713 ${id}: ${entities.length} entities, ${edges.length} edges, ${facts.length} facts`);
  }

  // Deduplicate and sort for determinism
  // Deduplicate entities by ID
  const entityMap = new Map<string, Entity>();
  for (const entity of allEntities) {
    if (!entityMap.has(entity.id)) {
      entityMap.set(entity.id, entity);
    }
  }
  allEntities = sortEntities(Array.from(entityMap.values()));

  // Deduplicate edges
  const edgeSet = new Set<string>();
  const uniqueEdges: Edge[] = [];
  for (const edge of allEdges) {
    const key = `${edge.src}|${edge.rel}|${edge.dst}`;
    if (!edgeSet.has(key)) {
      edgeSet.add(key);
      uniqueEdges.push(edge);
    }
  }
  allEdges = sortEdges(uniqueEdges);

  // Deduplicate facts
  const factSet = new Set<string>();
  const uniqueFacts: Fact[] = [];
  for (const fact of allFacts) {
    const key = `${fact.predicate}(${fact.args.join(",")})`;
    if (!factSet.has(key)) {
      factSet.add(key);
      uniqueFacts.push(fact);
    }
  }
  allFacts = sortFacts(uniqueFacts);

  // Build IR index
  const irIndex: IRIndex = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      entity_count: allEntities.length,
      edge_count: allEdges.length,
      fact_count: allFacts.length,
      content_hash: "", // Will be computed after
    },
    entities: allEntities,
    edges: allEdges,
    facts: allFacts,
  };

  // Compute content hash (excluding the hash itself and timestamp for determinism check)
  const hashableContent = {
    entities: allEntities,
    edges: allEdges,
    facts: allFacts,
  };
  irIndex.metadata.content_hash = contentHash(hashableContent);

  // Write IR index
  fs.writeFileSync(IR_OUTPUT_PATH, stableStringify(irIndex));
  console.log(`\n\u2713 IR index written to ${IR_OUTPUT_PATH}`);
  console.log(`  ${allEntities.length} entities, ${allEdges.length} edges, ${allFacts.length} facts`);
  console.log(`  Content hash: ${irIndex.metadata.content_hash.slice(0, 16)}`);

  // Build and write legacy index for backward compatibility
  const legacyIndex = buildLegacyIndex(allCrystals);
  fs.writeFileSync(LEGACY_OUTPUT_PATH, JSON.stringify(legacyIndex, null, 2));
  console.log(`\n\u2713 Legacy index written to ${LEGACY_OUTPUT_PATH}`);
  console.log(`  ${legacyIndex.packs.length} packs indexed.`);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
