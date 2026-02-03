#!/usr/bin/env npx ts-node
/**
 * ORIGIN Query Tool
 * Deterministic question answering without LLM inference
 * Supports: define, relate, find, prove
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

import {
  IRIndex,
  IRGraph,
  IRSearch,
  QueryResult,
  Citation,
  TraceStep,
  Entity,
  Fact,
  Rule,
} from "../src/ir/types";
import { stableStringify, filterByPrivacy } from "../src/ir/utils";
import {
  loadRulesFromDirectory,
  runRuleEngine,
  queryFacts,
  hasFact,
} from "../src/rules/engine";

const ROOT_DIR = path.join(__dirname, "..");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const RULES_DIR = path.join(ROOT_DIR, "rules");
const TRACES_DIR = path.join(BUILD_DIR, "traces");

const INDEX_PATH = path.join(BUILD_DIR, "index.json");
const GRAPH_PATH = path.join(BUILD_DIR, "graph.json");
const SEARCH_PATH = path.join(BUILD_DIR, "search.json");

// ============================================================================
// Data Loading
// ============================================================================

function loadIndex(): IRIndex | null {
  if (!fs.existsSync(INDEX_PATH)) return null;
  return JSON.parse(fs.readFileSync(INDEX_PATH, "utf-8"));
}

function loadGraph(): IRGraph | null {
  if (!fs.existsSync(GRAPH_PATH)) return null;
  return JSON.parse(fs.readFileSync(GRAPH_PATH, "utf-8"));
}

function loadSearch(): IRSearch | null {
  if (!fs.existsSync(SEARCH_PATH)) return null;
  return JSON.parse(fs.readFileSync(SEARCH_PATH, "utf-8"));
}

// ============================================================================
// Query Parsing
// ============================================================================

interface ParsedQuery {
  type: "define" | "relate" | "find" | "prove" | "unknown";
  terms: string[];
  predicates?: Array<{ predicate: string; args: string[] }>;
  raw: string;
}

function parseQuery(query: string): ParsedQuery {
  const trimmed = query.trim();

  // define <term>
  const defineMatch = trimmed.match(/^define\s+(.+)$/i);
  if (defineMatch) {
    return {
      type: "define",
      terms: [defineMatch[1].trim()],
      raw: trimmed,
    };
  }

  // relate <A> <B> or relate <A> to <B>
  const relateMatch = trimmed.match(/^relate\s+(\S+)\s+(?:to\s+)?(\S+)$/i);
  if (relateMatch) {
    return {
      type: "relate",
      terms: [relateMatch[1].trim(), relateMatch[2].trim()],
      raw: trimmed,
    };
  }

  // find <Type> where <predicate>(...) and ...
  const findMatch = trimmed.match(/^find\s+(\S+)\s+where\s+(.+)$/i);
  if (findMatch) {
    const entityType = findMatch[1].trim();
    const conditions = findMatch[2].trim();

    // Parse predicates: predicate(arg1, arg2) and predicate2(...)
    const predicates: Array<{ predicate: string; args: string[] }> = [];
    const predRegex = /(\w+)\(([^)]*)\)/g;
    let match;
    while ((match = predRegex.exec(conditions)) !== null) {
      predicates.push({
        predicate: match[1],
        args: match[2].split(",").map((a) => a.trim()),
      });
    }

    return {
      type: "find",
      terms: [entityType],
      predicates,
      raw: trimmed,
    };
  }

  // prove <predicate>(<args>)
  const proveMatch = trimmed.match(/^prove\s+(\w+)\(([^)]*)\)$/i);
  if (proveMatch) {
    const predicate = proveMatch[1];
    const args = proveMatch[2].split(",").map((a) => a.trim());
    return {
      type: "prove",
      terms: args,
      predicates: [{ predicate, args }],
      raw: trimmed,
    };
  }

  return {
    type: "unknown",
    terms: [trimmed],
    raw: trimmed,
  };
}

// ============================================================================
// Query Handlers
// ============================================================================

function handleDefine(
  term: string,
  index: IRIndex,
  search: IRSearch,
  allowSensitive: boolean
): QueryResult {
  const trace: TraceStep[] = [];
  const citations: Citation[] = [];
  const artifactsUsed = [INDEX_PATH, SEARCH_PATH];

  trace.push({
    stepType: "search",
    details: `Searching for term: "${term}"`,
  });

  // Tokenize the search term
  const tokens = term
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, " ")
    .split(/\s+/)
    .filter((t) => t.length > 2);

  // Find matching entities via inverted index
  const entityScores = new Map<string, number>();
  const entityCitations = new Map<string, Citation>();
  const entityTokenMatches = new Map<string, Set<string>>();

  for (const token of tokens) {
    const hits = search.invertedIndex[token] || [];
    for (const hit of hits) {
      const current = entityScores.get(hit.entityId) || 0;
      entityScores.set(hit.entityId, current + hit.score);
      if (!entityCitations.has(hit.entityId)) {
        entityCitations.set(hit.entityId, hit.citation);
      }
      // Track which tokens matched for coverage calculation
      if (!entityTokenMatches.has(hit.entityId)) {
        entityTokenMatches.set(hit.entityId, new Set());
      }
      entityTokenMatches.get(hit.entityId)!.add(token);
    }
  }

  // Also check for exact ID match
  const exactEntity = index.entities.find(
    (e) => e.id.toLowerCase() === term.toLowerCase()
  );
  if (exactEntity) {
    entityScores.set(exactEntity.id, (entityScores.get(exactEntity.id) || 0) + 100);
    // Exact match gets full token coverage
    if (!entityTokenMatches.has(exactEntity.id)) {
      entityTokenMatches.set(exactEntity.id, new Set(tokens));
    }
  }

  // Filter entities by token coverage - require at least 50% of search tokens to match
  // This prevents false positives from single-token partial matches
  const MIN_TOKEN_COVERAGE = 0.5;
  const filteredEntityScores = new Map<string, number>();
  for (const [entityId, score] of entityScores) {
    const matchedTokens = entityTokenMatches.get(entityId)?.size || 0;
    const coverage = tokens.length > 0 ? matchedTokens / tokens.length : 0;
    if (coverage >= MIN_TOKEN_COVERAGE) {
      filteredEntityScores.set(entityId, score);
    }
  }

  // Sort by score
  const rankedEntitiesWithScores = Array.from(filteredEntityScores.entries())
    .sort((a, b) => b[1] - a[1]);

  // Minimum score threshold: require at least one strong match
  const MIN_SCORE_THRESHOLD = 1.0;
  const topScore = rankedEntitiesWithScores[0]?.[1] || 0;

  if (rankedEntitiesWithScores.length === 0 || topScore < MIN_SCORE_THRESHOLD) {
    trace.push({
      stepType: "lookup",
      details: rankedEntitiesWithScores.length === 0
        ? "No matching entities found"
        : `Best match score (${topScore.toFixed(2)}) below threshold (${MIN_SCORE_THRESHOLD})`,
    });

    return {
      answer: "UNKNOWN",
      unknownReason: `No definition found for term: "${term}"`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  const rankedEntities = rankedEntitiesWithScores.map(([id]) => id);

  trace.push({
    stepType: "lookup",
    details: `Found ${rankedEntities.length} matching entities`,
    involved: rankedEntities.slice(0, 5),
  });

  // Get the top match
  const topEntityId = rankedEntities[0];
  const entity = index.entities.find((e) => e.id === topEntityId);

  if (!entity) {
    return {
      answer: "UNKNOWN",
      unknownReason: "Entity lookup failed",
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  // Check privacy
  if (entity.sensitivity.level === "REDACTED") {
    trace.push({
      stepType: "privacy_block",
      details: "Entity is REDACTED",
    });
    return {
      answer: "UNKNOWN",
      unknownReason: "Blocked by privacy boundary (REDACTED content)",
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  if (entity.sensitivity.level === "SENSITIVE" && !allowSensitive) {
    trace.push({
      stepType: "privacy_block",
      details: "Entity is SENSITIVE (use --private flag)",
    });
    return {
      answer: "UNKNOWN",
      unknownReason: "Blocked by privacy boundary (SENSITIVE content, use --private)",
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  // Build answer
  const citation = entityCitations.get(topEntityId) || {
    file: entity.provenance.file,
    yamlPath: entity.provenance.yamlPath,
    crystalId: entity.provenance.crystalId,
    contentHash: entity.provenance.contentHash,
  };
  citations.push(citation);

  const answer = {
    id: entity.id,
    type: entity.type,
    title: entity.attrs.title || entity.labels[0],
    summary: entity.attrs.summary,
    labels: entity.labels,
    attrs: entity.attrs,
  };

  return {
    answer,
    citations,
    trace,
    artifactsUsed,
    timestamp: new Date().toISOString(),
  };
}

function handleRelate(
  termA: string,
  termB: string,
  index: IRIndex,
  graph: IRGraph,
  allowSensitive: boolean
): QueryResult {
  const trace: TraceStep[] = [];
  const citations: Citation[] = [];
  const artifactsUsed = [INDEX_PATH, GRAPH_PATH];

  trace.push({
    stepType: "search",
    details: `Finding path between "${termA}" and "${termB}"`,
  });

  // Resolve terms to entity IDs
  const resolveEntity = (term: string): Entity | null => {
    // Try exact match first
    let entity = index.entities.find(
      (e) =>
        e.id.toLowerCase() === term.toLowerCase() ||
        e.labels.some((l) => l.toLowerCase() === term.toLowerCase())
    );
    if (entity) return entity;

    // Try partial match
    entity = index.entities.find(
      (e) =>
        e.id.toLowerCase().includes(term.toLowerCase()) ||
        e.labels.some((l) => l.toLowerCase().includes(term.toLowerCase()))
    );
    return entity || null;
  };

  const entityA = resolveEntity(termA);
  const entityB = resolveEntity(termB);

  if (!entityA) {
    return {
      answer: "UNKNOWN",
      unknownReason: `Could not resolve entity: "${termA}"`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  if (!entityB) {
    return {
      answer: "UNKNOWN",
      unknownReason: `Could not resolve entity: "${termB}"`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  trace.push({
    stepType: "lookup",
    details: `Resolved: ${entityA.id} -> ${entityB.id}`,
    involved: [entityA.id, entityB.id],
  });

  // BFS to find shortest path
  const visited = new Set<string>();
  const queue: Array<{ nodeId: string; path: string[]; rels: string[] }> = [
    { nodeId: entityA.id, path: [entityA.id], rels: [] },
  ];

  let foundPath: { path: string[]; rels: string[] } | null = null;

  while (queue.length > 0 && !foundPath) {
    const { nodeId, path, rels } = queue.shift()!;

    if (visited.has(nodeId)) continue;
    visited.add(nodeId);

    if (nodeId === entityB.id) {
      foundPath = { path, rels };
      break;
    }

    // Get adjacency list
    const neighbors = graph.adjacency[nodeId] || [];

    // Sort for deterministic order
    const sortedNeighbors = [...neighbors].sort((a, b) => {
      const relCompare = a.rel.localeCompare(b.rel);
      if (relCompare !== 0) return relCompare;
      return a.target.localeCompare(b.target);
    });

    for (const neighbor of sortedNeighbors) {
      if (!visited.has(neighbor.target)) {
        queue.push({
          nodeId: neighbor.target,
          path: [...path, neighbor.target],
          rels: [...rels, neighbor.rel],
        });
      }
    }
  }

  trace.push({
    stepType: "graph_traverse",
    details: `BFS explored ${visited.size} nodes`,
  });

  if (!foundPath) {
    return {
      answer: "UNKNOWN",
      unknownReason: `No path found between ${entityA.id} and ${entityB.id}`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  // Build citations for path
  for (const nodeId of foundPath.path) {
    const entity = index.entities.find((e) => e.id === nodeId);
    if (entity) {
      citations.push({
        file: entity.provenance.file,
        yamlPath: entity.provenance.yamlPath,
        crystalId: entity.provenance.crystalId,
        contentHash: entity.provenance.contentHash,
      });
    }
  }

  const answer = {
    from: entityA.id,
    to: entityB.id,
    path: foundPath.path,
    relationships: foundPath.rels,
    pathLength: foundPath.path.length - 1,
  };

  return {
    answer,
    citations,
    trace,
    artifactsUsed,
    timestamp: new Date().toISOString(),
  };
}

function handleFind(
  entityType: string,
  predicates: Array<{ predicate: string; args: string[] }>,
  index: IRIndex,
  rules: Rule[],
  allowSensitive: boolean
): QueryResult {
  const trace: TraceStep[] = [];
  const citations: Citation[] = [];
  const artifactsUsed = [INDEX_PATH];

  trace.push({
    stepType: "search",
    details: `Finding ${entityType} entities matching predicates`,
  });

  // Run rule engine to get derived facts
  const ruleResult = runRuleEngine(index.facts, rules);
  const allFacts = [...index.facts, ...ruleResult.derivedFacts];

  trace.push({
    stepType: "rule_fire",
    details: `Rule engine derived ${ruleResult.derivedFacts.length} facts in ${ruleResult.iterations} iterations`,
  });

  // Find entities of the given type
  let matchingEntities = index.entities.filter(
    (e) => e.type.toLowerCase() === entityType.toLowerCase()
  );

  // Apply privacy filter
  matchingEntities = filterByPrivacy(matchingEntities, allowSensitive, false);

  trace.push({
    stepType: "lookup",
    details: `Found ${matchingEntities.length} entities of type ${entityType}`,
  });

  // Filter by predicates
  for (const pred of predicates) {
    matchingEntities = matchingEntities.filter((entity) => {
      // Check if there's a fact matching this predicate for this entity
      const matchingFacts = queryFacts(allFacts, pred.predicate);
      return matchingFacts.some((fact) => {
        // The entity should be one of the arguments
        if (!fact.args.includes(entity.id)) return false;

        // Check other argument constraints
        for (let i = 0; i < pred.args.length; i++) {
          const arg = pred.args[i];
          if (arg && !arg.startsWith("?") && fact.args[i] !== arg) {
            return false;
          }
        }
        return true;
      });
    });
  }

  if (matchingEntities.length === 0) {
    return {
      answer: "UNKNOWN",
      unknownReason: `No ${entityType} entities match the given predicates`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  // Build citations
  for (const entity of matchingEntities) {
    citations.push({
      file: entity.provenance.file,
      yamlPath: entity.provenance.yamlPath,
      crystalId: entity.provenance.crystalId,
      contentHash: entity.provenance.contentHash,
    });
  }

  const answer = {
    type: entityType,
    count: matchingEntities.length,
    entities: matchingEntities.map((e) => ({
      id: e.id,
      labels: e.labels,
      attrs: e.attrs,
    })),
  };

  return {
    answer,
    citations,
    trace,
    artifactsUsed,
    timestamp: new Date().toISOString(),
  };
}

function handleProve(
  predicate: string,
  args: string[],
  index: IRIndex,
  rules: Rule[],
  allowSensitive: boolean
): QueryResult {
  const trace: TraceStep[] = [];
  const citations: Citation[] = [];
  const artifactsUsed = [INDEX_PATH];

  trace.push({
    stepType: "search",
    details: `Proving ${predicate}(${args.join(", ")})`,
  });

  // Run rule engine
  const ruleResult = runRuleEngine(index.facts, rules);
  const allFacts = [...index.facts, ...ruleResult.derivedFacts];

  // Check if the fact exists
  const matchingFacts = queryFacts(allFacts, predicate, args);

  if (matchingFacts.length === 0) {
    trace.push({
      stepType: "lookup",
      details: "Fact not found in base or derived facts",
    });

    return {
      answer: "UNKNOWN",
      unknownReason: `Cannot prove ${predicate}(${args.join(", ")})`,
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  const fact = matchingFacts[0];

  // Check privacy
  if (fact.sensitivity.level === "REDACTED") {
    trace.push({
      stepType: "privacy_block",
      details: "Proof touches REDACTED content",
    });
    return {
      answer: "UNKNOWN",
      unknownReason: "Blocked by privacy boundary (proof touches REDACTED content)",
      citations: [],
      trace,
      artifactsUsed,
      timestamp: new Date().toISOString(),
    };
  }

  // Build proof trace
  if (fact.derived) {
    // Find the firing that produced this fact
    const firing = ruleResult.firingTrace.find(
      (f) =>
        f.derivedFact.predicate === predicate &&
        f.derivedFact.args.join(",") === args.join(",")
    );

    if (firing) {
      trace.push({
        stepType: "rule_match",
        ruleId: firing.ruleId,
        details: `Matched rule ${firing.ruleId} with bindings: ${JSON.stringify(firing.bindings)}`,
        involved: firing.supportingFacts.map((f) => `${f.predicate}(${f.args.join(",")})`),
      });

      trace.push({
        stepType: "rule_fire",
        ruleId: firing.ruleId,
        details: `Derived ${predicate}(${args.join(", ")})`,
      });
    }
  } else {
    trace.push({
      stepType: "lookup",
      details: "Found as base fact (not derived)",
    });
  }

  // Build citations
  for (const prov of fact.provenance) {
    citations.push({
      file: prov.file,
      yamlPath: prov.yamlPath,
      crystalId: prov.crystalId,
      contentHash: prov.contentHash,
    });
  }

  const answer = {
    proven: true,
    predicate,
    args,
    derived: fact.derived,
    proofDepth: fact.derived
      ? ruleResult.firingTrace.filter((f) =>
          f.supportingFacts.some(
            (sf) =>
              sf.predicate === predicate && sf.args.join(",") === args.join(",")
          )
        ).length + 1
      : 0,
  };

  return {
    answer,
    citations,
    trace,
    artifactsUsed,
    timestamp: new Date().toISOString(),
  };
}

// ============================================================================
// Main
// ============================================================================

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  // Parse flags
  const allowSensitive = args.includes("--private");
  const queryArgs = args.filter((a) => !a.startsWith("--"));

  if (queryArgs.length === 0) {
    console.error("Usage: npm run query -- <query>");
    console.error("");
    console.error("Query forms:");
    console.error('  define <term>         - Define a term (e.g., "define Holodeck")');
    console.error('  relate <A> <B>        - Find path between A and B');
    console.error('  find <Type> where ... - Find entities matching predicates');
    console.error('  prove <pred>(args)    - Prove a predicate');
    console.error("");
    console.error("Flags:");
    console.error("  --private             - Allow SENSITIVE content in output");
    process.exit(1);
  }

  const queryStr = queryArgs.join(" ");

  // Load data
  const index = loadIndex();
  if (!index) {
    console.error("Error: build/index.json not found. Run npm run build first.");
    process.exit(1);
  }

  const graph = loadGraph();
  const search = loadSearch();
  const rules = loadRulesFromDirectory(RULES_DIR);

  // Parse and execute query
  const parsed = parseQuery(queryStr);
  let result: QueryResult;

  switch (parsed.type) {
    case "define":
      if (!search) {
        console.error("Error: build/search.json not found.");
        process.exit(1);
      }
      result = handleDefine(parsed.terms[0], index, search, allowSensitive);
      break;

    case "relate":
      if (!graph) {
        console.error("Error: build/graph.json not found.");
        process.exit(1);
      }
      result = handleRelate(
        parsed.terms[0],
        parsed.terms[1],
        index,
        graph,
        allowSensitive
      );
      break;

    case "find":
      result = handleFind(
        parsed.terms[0],
        parsed.predicates || [],
        index,
        rules,
        allowSensitive
      );
      break;

    case "prove":
      if (!parsed.predicates || parsed.predicates.length === 0) {
        result = {
          answer: "UNKNOWN",
          unknownReason: "Invalid prove query format",
          citations: [],
          trace: [],
          artifactsUsed: [],
          timestamp: new Date().toISOString(),
        };
      } else {
        result = handleProve(
          parsed.predicates[0].predicate,
          parsed.predicates[0].args,
          index,
          rules,
          allowSensitive
        );
      }
      break;

    default:
      result = {
        answer: "UNKNOWN",
        unknownReason: `Unknown query type. Supported: define, relate, find, prove`,
        citations: [],
        trace: [
          {
            stepType: "search",
            details: `Could not parse query: "${queryStr}"`,
          },
        ],
        artifactsUsed: [],
        timestamp: new Date().toISOString(),
      };
  }

  // Save trace
  if (!fs.existsSync(TRACES_DIR)) {
    fs.mkdirSync(TRACES_DIR, { recursive: true });
  }

  const runId = `query_${Date.now()}`;
  const tracePath = path.join(TRACES_DIR, `${runId}.json`);
  fs.writeFileSync(
    tracePath,
    stableStringify({
      runId,
      query: queryStr,
      parsed,
      result,
    })
  );

  // Output result
  console.log(stableStringify(result));
}

main().catch((err) => {
  console.error("Query failed:", err);
  process.exit(1);
});
