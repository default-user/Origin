#!/usr/bin/env npx ts-node
/**
 * ORIGIN Explain Tool
 * Replays saved traces to explain query results
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

import { QueryResult, TraceStep } from "../src/ir/types";

const ROOT_DIR = path.join(__dirname, "..");
const BUILD_DIR = path.join(ROOT_DIR, "build");
const TRACES_DIR = path.join(BUILD_DIR, "traces");

interface SavedTrace {
  runId: string;
  query: string;
  parsed: {
    type: string;
    terms: string[];
    predicates?: Array<{ predicate: string; args: string[] }>;
    raw: string;
  };
  result: QueryResult;
}

function loadTrace(runId: string): SavedTrace | null {
  const tracePath = path.join(TRACES_DIR, `${runId}.json`);
  if (!fs.existsSync(tracePath)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(tracePath, "utf-8"));
}

function listTraces(): string[] {
  if (!fs.existsSync(TRACES_DIR)) {
    return [];
  }

  return fs
    .readdirSync(TRACES_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => f.replace(".json", ""))
    .sort()
    .reverse(); // Most recent first
}

function formatStep(step: TraceStep, index: number): string {
  const lines: string[] = [];

  const stepIcon =
    {
      search: "\u{1F50D}",
      lookup: "\u{1F4D6}",
      rule_match: "\u{1F3AF}",
      rule_fire: "\u26A1",
      graph_traverse: "\u{1F578}",
      privacy_block: "\u{1F512}",
    }[step.stepType] || "\u2022";

  lines.push(`  ${index + 1}. ${stepIcon} [${step.stepType}] ${step.details}`);

  if (step.ruleId) {
    lines.push(`       Rule: ${step.ruleId}`);
  }

  if (step.involved && step.involved.length > 0) {
    lines.push(`       Involved: ${step.involved.slice(0, 5).join(", ")}`);
    if (step.involved.length > 5) {
      lines.push(`                 ... and ${step.involved.length - 5} more`);
    }
  }

  return lines.join("\n");
}

function explainTrace(trace: SavedTrace): void {
  console.log("ORIGIN Query Explanation");
  console.log("========================");
  console.log(`Attribution: Ande + Kai (OI) + Whanau (OIs)\n`);

  console.log(`Run ID: ${trace.runId}`);
  console.log(`Query:  ${trace.query}`);
  console.log(`Type:   ${trace.parsed.type}`);
  console.log(`Time:   ${trace.result.timestamp}`);
  console.log("");

  console.log("Reasoning Trace:");
  console.log("-----------------");

  if (trace.result.trace.length === 0) {
    console.log("  (no trace steps recorded)");
  } else {
    for (let i = 0; i < trace.result.trace.length; i++) {
      console.log(formatStep(trace.result.trace[i], i));
    }
  }

  console.log("");
  console.log("Answer:");
  console.log("-------");

  if (trace.result.answer === "UNKNOWN") {
    console.log(`  UNKNOWN: ${trace.result.unknownReason}`);
  } else {
    console.log(JSON.stringify(trace.result.answer, null, 2));
  }

  console.log("");
  console.log("Citations:");
  console.log("----------");

  if (trace.result.citations.length === 0) {
    console.log("  (no citations)");
  } else {
    for (const citation of trace.result.citations) {
      console.log(`  - ${citation.file}`);
      if (citation.crystalId) {
        console.log(`    Crystal: ${citation.crystalId}`);
      }
      console.log(`    Path: ${citation.yamlPath}`);
      console.log(`    Hash: ${citation.contentHash.slice(0, 16)}...`);
    }
  }

  console.log("");
  console.log("Artifacts Used:");
  console.log("---------------");

  if (trace.result.artifactsUsed.length === 0) {
    console.log("  (none)");
  } else {
    for (const artifact of trace.result.artifactsUsed) {
      console.log(`  - ${artifact}`);
    }
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);

  if (args.length === 0 || args[0] === "--list") {
    console.log("Available traces:");
    console.log("-----------------");

    const traces = listTraces();
    if (traces.length === 0) {
      console.log("  (no traces found - run some queries first)");
    } else {
      for (const traceId of traces.slice(0, 20)) {
        const trace = loadTrace(traceId);
        if (trace) {
          const status = trace.result.answer === "UNKNOWN" ? "?" : "\u2713";
          console.log(`  ${status} ${traceId}: ${trace.query}`);
        }
      }

      if (traces.length > 20) {
        console.log(`  ... and ${traces.length - 20} more`);
      }
    }

    console.log("");
    console.log("Usage: npm run explain -- <run_id>");
    return;
  }

  const runId = args[0];
  const trace = loadTrace(runId);

  if (!trace) {
    console.error(`Error: Trace not found: ${runId}`);
    console.error(`Run 'npm run explain' to see available traces.`);
    process.exit(1);
  }

  explainTrace(trace);
}

main().catch((err) => {
  console.error("Explain failed:", err);
  process.exit(1);
});
