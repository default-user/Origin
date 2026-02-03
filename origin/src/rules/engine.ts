/**
 * ORIGIN Rule Engine
 * Deterministic forward-chaining Horn-style inference engine
 * No LLM, no randomness, fully reproducible
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

import {
  Rule,
  RuleAtom,
  RuleFilter,
  Fact,
  Provenance,
  Sensitivity,
  RuleEngineResult,
  RuleFiring,
} from "../ir/types";
import {
  sortFacts,
  mergeSensitivity,
  mergeProvenances,
  createProvenance,
  stableStringify,
} from "../ir/utils";

// ============================================================================
// Rule Loading
// ============================================================================

interface RawRule {
  rule_id: string;
  description?: string;
  head: {
    predicate: string;
    args: string[];
  };
  body: Array<{
    predicate: string;
    args: string[];
  }>;
  filters?: Array<{
    op: string;
    a: string;
    b: string;
  }>;
}

export function loadRulesFromDirectory(rulesDir: string): Rule[] {
  const rules: Rule[] = [];

  if (!fs.existsSync(rulesDir)) {
    return rules;
  }

  const files = fs.readdirSync(rulesDir).sort();

  for (const file of files) {
    if (!file.endsWith(".yaml") && !file.endsWith(".yml")) {
      continue;
    }

    const filePath = path.join(rulesDir, file);
    const content = fs.readFileSync(filePath, "utf-8");

    // Handle multi-document YAML
    const docs = yaml.loadAll(content) as RawRule[];

    for (const doc of docs) {
      if (!doc || !doc.rule_id) continue;

      const rule: Rule = {
        id: doc.rule_id,
        head: {
          predicate: doc.head.predicate,
          args: doc.head.args,
        },
        body: doc.body.map((atom) => ({
          predicate: atom.predicate,
          args: atom.args,
        })),
        filters: doc.filters?.map((f) => ({
          op: f.op as RuleFilter["op"],
          a: f.a,
          b: f.b,
        })),
        provenance: createProvenance(
          filePath,
          doc.rule_id,
          doc,
          null,
          "rules"
        ),
        description: doc.description,
      };

      rules.push(rule);
    }
  }

  // Sort rules by ID for deterministic evaluation order
  return rules.sort((a, b) => a.id.localeCompare(b.id));
}

// ============================================================================
// Pattern Matching
// ============================================================================

type Bindings = Record<string, string>;

function isVariable(arg: string): boolean {
  return arg.startsWith("?");
}

function unify(
  pattern: string,
  value: string,
  bindings: Bindings
): Bindings | null {
  if (isVariable(pattern)) {
    if (bindings[pattern] !== undefined) {
      // Already bound - check consistency
      return bindings[pattern] === value ? bindings : null;
    }
    // New binding
    return { ...bindings, [pattern]: value };
  }
  // Literal - must match exactly
  return pattern === value ? bindings : null;
}

function matchAtom(
  atom: RuleAtom,
  fact: Fact,
  bindings: Bindings
): Bindings | null {
  // Predicate must match exactly
  if (atom.predicate !== fact.predicate) {
    return null;
  }

  // Args must unify
  if (atom.args.length !== fact.args.length) {
    return null;
  }

  let currentBindings = bindings;
  for (let i = 0; i < atom.args.length; i++) {
    const result = unify(atom.args[i], fact.args[i], currentBindings);
    if (result === null) {
      return null;
    }
    currentBindings = result;
  }

  return currentBindings;
}

function applyBindings(args: string[], bindings: Bindings): string[] {
  return args.map((arg) => (isVariable(arg) ? bindings[arg] ?? arg : arg));
}

// ============================================================================
// Filter Evaluation
// ============================================================================

function evaluateFilter(filter: RuleFilter, bindings: Bindings): boolean {
  const a = isVariable(filter.a) ? bindings[filter.a] : filter.a;
  const b = isVariable(filter.b) ? bindings[filter.b] : filter.b;

  if (a === undefined || b === undefined) {
    return false; // Unbound variables fail filter
  }

  switch (filter.op) {
    case "eq":
      return a === b;
    case "neq":
      return a !== b;
    case "lt":
      return a < b;
    case "gt":
      return a > b;
    case "lte":
      return a <= b;
    case "gte":
      return a >= b;
    case "contains":
      return a.includes(b);
    case "matches":
      try {
        return new RegExp(b).test(a);
      } catch {
        return false;
      }
    default:
      return false;
  }
}

function evaluateFilters(
  filters: RuleFilter[] | undefined,
  bindings: Bindings
): boolean {
  if (!filters || filters.length === 0) {
    return true;
  }
  return filters.every((filter) => evaluateFilter(filter, bindings));
}

// ============================================================================
// Rule Evaluation (Semi-naive Forward Chaining)
// ============================================================================

interface FactIndex {
  byPredicate: Map<string, Fact[]>;
}

function buildFactIndex(facts: Fact[]): FactIndex {
  const byPredicate = new Map<string, Fact[]>();

  for (const fact of facts) {
    const existing = byPredicate.get(fact.predicate) || [];
    existing.push(fact);
    byPredicate.set(fact.predicate, existing);
  }

  return { byPredicate };
}

function findMatchingFacts(
  atom: RuleAtom,
  bindings: Bindings,
  index: FactIndex
): Array<{ fact: Fact; bindings: Bindings }> {
  const results: Array<{ fact: Fact; bindings: Bindings }> = [];

  const facts = index.byPredicate.get(atom.predicate) || [];

  for (const fact of facts) {
    const newBindings = matchAtom(atom, fact, bindings);
    if (newBindings !== null) {
      results.push({ fact, bindings: newBindings });
    }
  }

  return results;
}

function evaluateBody(
  body: RuleAtom[],
  bindings: Bindings,
  index: FactIndex
): Array<{ bindings: Bindings; supportingFacts: Fact[] }> {
  if (body.length === 0) {
    return [{ bindings, supportingFacts: [] }];
  }

  const [first, ...rest] = body;
  const matches = findMatchingFacts(first, bindings, index);
  const results: Array<{ bindings: Bindings; supportingFacts: Fact[] }> = [];

  for (const match of matches) {
    const subResults = evaluateBody(rest, match.bindings, index);
    for (const subResult of subResults) {
      results.push({
        bindings: subResult.bindings,
        supportingFacts: [match.fact, ...subResult.supportingFacts],
      });
    }
  }

  return results;
}

function deriveFactFromRule(
  rule: Rule,
  bindings: Bindings,
  supportingFacts: Fact[]
): Fact {
  const args = applyBindings(rule.head.args, bindings);

  // Merge provenances from supporting facts + rule
  const allProvenances = [
    rule.provenance,
    ...supportingFacts.flatMap((f) => f.provenance),
  ];

  // Merge sensitivities (take max)
  const allSensitivities = supportingFacts.map((f) => f.sensitivity);
  const mergedSensitivity =
    allSensitivities.length > 0
      ? mergeSensitivity(...allSensitivities)
      : {
          level: "PUBLIC" as const,
          pii_risk: "none" as const,
          contains_personal: false,
          redacted: false,
        };

  return {
    predicate: rule.head.predicate,
    args,
    derived: true,
    provenance: mergeProvenances(allProvenances),
    sensitivity: mergedSensitivity,
  };
}

function factKey(fact: Fact): string {
  return `${fact.predicate}(${fact.args.join(",")})`;
}

export function runRuleEngine(
  baseFacts: Fact[],
  rules: Rule[],
  maxIterations: number = 100
): RuleEngineResult {
  // Sort rules for deterministic order
  const sortedRules = [...rules].sort((a, b) => a.id.localeCompare(b.id));

  // All facts (base + derived)
  let allFacts = sortFacts([...baseFacts]);
  const factSet = new Set<string>(allFacts.map(factKey));

  // Derived facts and firing trace
  const derivedFacts: Fact[] = [];
  const firingTrace: RuleFiring[] = [];

  let iteration = 0;
  let changed = true;

  while (changed && iteration < maxIterations) {
    changed = false;
    iteration++;

    // Rebuild index each iteration with new facts
    const index = buildFactIndex(allFacts);

    // Try each rule in order
    for (const rule of sortedRules) {
      // Find all matching bindings for the rule body
      const matches = evaluateBody(rule.body, {}, index);

      // Sort matches for determinism
      matches.sort((a, b) => {
        const aKey = Object.keys(a.bindings)
          .sort()
          .map((k) => `${k}=${a.bindings[k]}`)
          .join(",");
        const bKey = Object.keys(b.bindings)
          .sort()
          .map((k) => `${k}=${b.bindings[k]}`)
          .join(",");
        return aKey.localeCompare(bKey);
      });

      for (const match of matches) {
        // Check filters
        if (!evaluateFilters(rule.filters, match.bindings)) {
          continue;
        }

        // Derive new fact
        const newFact = deriveFactFromRule(
          rule,
          match.bindings,
          match.supportingFacts
        );
        const key = factKey(newFact);

        // Only add if not already known
        if (!factSet.has(key)) {
          factSet.add(key);
          allFacts.push(newFact);
          derivedFacts.push(newFact);
          changed = true;

          // Record firing
          firingTrace.push({
            ruleId: rule.id,
            bindings: match.bindings,
            derivedFact: newFact,
            supportingFacts: match.supportingFacts,
            iteration,
          });
        }
      }
    }
  }

  // Sort derived facts for determinism
  const sortedDerivedFacts = sortFacts(derivedFacts);

  return {
    derivedFacts: sortedDerivedFacts,
    firingTrace,
    iterations: iteration,
    fixedPoint: !changed,
  };
}

// ============================================================================
// Convenience Functions
// ============================================================================

export function queryFacts(
  facts: Fact[],
  predicate: string,
  args?: (string | null)[]
): Fact[] {
  return facts.filter((fact) => {
    if (fact.predicate !== predicate) return false;
    if (!args) return true;
    if (fact.args.length !== args.length) return false;

    for (let i = 0; i < args.length; i++) {
      if (args[i] !== null && args[i] !== fact.args[i]) {
        return false;
      }
    }
    return true;
  });
}

export function hasFact(
  facts: Fact[],
  predicate: string,
  args: string[]
): boolean {
  return facts.some(
    (fact) =>
      fact.predicate === predicate &&
      fact.args.length === args.length &&
      fact.args.every((arg, i) => arg === args[i])
  );
}
