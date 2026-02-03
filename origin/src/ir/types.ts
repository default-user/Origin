/**
 * ORIGIN Intermediate Representation (IR) Types
 * Canonical types for deterministic reasoning without LLM inference
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

// ============================================================================
// Sensitivity Levels - for privacy boundary enforcement
// ============================================================================

export type SensitivityLevel = "PUBLIC" | "SENSITIVE" | "REDACTED";

export interface Sensitivity {
  level: SensitivityLevel;
  pii_risk: "none" | "low" | "medium" | "high";
  contains_personal: boolean;
  redacted: boolean;
}

// ============================================================================
// Provenance - for citation and traceability
// ============================================================================

export interface Provenance {
  /** Source file path relative to repo root */
  file: string;
  /** Path within YAML structure (e.g., "claims[0]") */
  yamlPath: string;
  /** Stable content hash (SHA-256 of normalized JSON) */
  contentHash: string;
  /** Crystal ID if applicable (e.g., "C0001") */
  crystalId: string | null;
  /** Crystal root directory */
  crystalRoot: string;
}

// ============================================================================
// Entity - nodes in the knowledge graph
// ============================================================================

export interface Entity {
  /** Stable ID derived from crystalId + yamlPath or explicit ID */
  id: string;
  /** Entity type (e.g., "Concept", "Claim", "Test") */
  type: EntityType;
  /** Human-readable labels for search */
  labels: string[];
  /** Arbitrary attributes (key-value pairs) */
  attrs: Record<string, unknown>;
  /** Provenance chain */
  provenance: Provenance;
  /** Privacy classification */
  sensitivity: Sensitivity;
}

export type EntityType =
  | "Concept"
  | "Claim"
  | "Test"
  | "Artifact"
  | "Tag"
  | "External";

// ============================================================================
// Edge - relationships between entities
// ============================================================================

export interface Edge {
  /** Source entity ID */
  src: string;
  /** Relationship type */
  rel: RelationType;
  /** Destination entity ID */
  dst: string;
  /** Edge attributes */
  attrs: Record<string, unknown>;
  /** Provenance chain */
  provenance: Provenance;
  /** Inherited sensitivity (max of src/dst) */
  sensitivity: Sensitivity;
}

export type RelationType =
  | "parent"
  | "child"
  | "related"
  | "claims"
  | "tests"
  | "tagged"
  | "references"
  | "derived_from"
  | "influences";

// ============================================================================
// Fact - ground facts extracted from crystals
// ============================================================================

export interface Fact {
  /** Predicate name (e.g., "hasTitle", "isTagged", "claims") */
  predicate: string;
  /** Arguments (entity IDs or literal values) */
  args: string[];
  /** Whether this fact was derived (true) or extracted (false) */
  derived: boolean;
  /** Provenance chain (union if derived) */
  provenance: Provenance[];
  /** Inherited sensitivity */
  sensitivity: Sensitivity;
}

// ============================================================================
// Rule - Horn-like rules for inference
// ============================================================================

export interface RuleAtom {
  /** Predicate name */
  predicate: string;
  /** Arguments (variables start with "?") */
  args: string[];
}

export interface RuleFilter {
  /** Filter operation */
  op: "eq" | "neq" | "lt" | "gt" | "lte" | "gte" | "contains" | "matches";
  /** Left operand (variable or literal) */
  a: string;
  /** Right operand (variable or literal) */
  b: string;
}

export interface Rule {
  /** Unique rule ID (e.g., "R001_transitivity") */
  id: string;
  /** Head atom (what is derived) */
  head: RuleAtom;
  /** Body atoms (what must be true) */
  body: RuleAtom[];
  /** Optional filters */
  filters?: RuleFilter[];
  /** Rule provenance */
  provenance: Provenance;
  /** Rule description */
  description?: string;
}

// ============================================================================
// Query Types - for the query tool
// ============================================================================

export type QueryType = "define" | "relate" | "find" | "prove";

export interface QueryResult {
  /** Answer content or "UNKNOWN" */
  answer: string | Record<string, unknown> | "UNKNOWN";
  /** Reason if UNKNOWN */
  unknownReason?: string;
  /** Citations for the answer */
  citations: Citation[];
  /** Reasoning trace */
  trace: TraceStep[];
  /** Build artifacts used */
  artifactsUsed: string[];
  /** Query execution timestamp */
  timestamp: string;
}

export interface Citation {
  file: string;
  yamlPath: string;
  crystalId: string | null;
  contentHash: string;
}

export interface TraceStep {
  /** Step type */
  stepType:
    | "search"
    | "lookup"
    | "rule_match"
    | "rule_fire"
    | "graph_traverse"
    | "privacy_block";
  /** Rule ID if applicable */
  ruleId?: string;
  /** Step details */
  details: string;
  /** Entities/facts involved */
  involved?: string[];
}

// ============================================================================
// Index Types - for build artifacts
// ============================================================================

export interface IRIndex {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    entity_count: number;
    edge_count: number;
    fact_count: number;
    content_hash: string;
  };
  entities: Entity[];
  edges: Edge[];
  facts: Fact[];
}

export interface IRGraph {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    node_count: number;
    edge_count: number;
    content_hash: string;
  };
  adjacency: Record<string, AdjacencyEntry[]>;
  nodes: Record<string, GraphNode>;
}

export interface AdjacencyEntry {
  target: string;
  rel: RelationType;
  attrs: Record<string, unknown>;
  provenance: Provenance;
}

export interface GraphNode {
  id: string;
  type: EntityType;
  labels: string[];
  sensitivity: SensitivityLevel;
}

export interface IRSearch {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    entry_count: number;
    token_count: number;
    content_hash: string;
  };
  /** Inverted index: token -> entity IDs with citations */
  invertedIndex: Record<string, SearchHit[]>;
  /** Entity labels for display */
  entityLabels: Record<string, string[]>;
}

export interface SearchHit {
  entityId: string;
  score: number;
  citation: Citation;
}

// ============================================================================
// Validation Report Types
// ============================================================================

export interface ValidationReport {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    total_crystals: number;
    valid_count: number;
    invalid_count: number;
  };
  results: ValidationResult[];
}

export interface ValidationResult {
  file: string;
  yamlPath: string;
  crystalId: string | null;
  crystalRoot: string;
  valid: boolean;
  errors: ValidationError[];
}

export interface ValidationError {
  path: string;
  message: string;
  schemaPath?: string;
}

// ============================================================================
// Rule Engine Types
// ============================================================================

export interface RuleEngineResult {
  /** Newly derived facts */
  derivedFacts: Fact[];
  /** Firing trace */
  firingTrace: RuleFiring[];
  /** Number of iterations */
  iterations: number;
  /** Fixed point reached? */
  fixedPoint: boolean;
}

export interface RuleFiring {
  ruleId: string;
  bindings: Record<string, string>;
  derivedFact: Fact;
  supportingFacts: Fact[];
  iteration: number;
}

// ============================================================================
// Crystal Root Configuration
// ============================================================================

export interface CrystalRootsConfig {
  /** List of crystal root directories relative to repo root */
  roots: string[];
  /** Default schema to use */
  defaultSchema?: string;
  /** Schema overrides by root */
  schemaOverrides?: Record<string, string>;
}
