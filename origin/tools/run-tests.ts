#!/usr/bin/env npx ts-node
/**
 * ORIGIN Test Runner
 * Runs golden tests for deterministic query verification
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";
import { execSync } from "child_process";

const ROOT_DIR = path.join(__dirname, "..");
const TESTS_DIR = path.join(ROOT_DIR, "tests", "golden");

interface GoldenTest {
  name: string;
  query: string;
  expected_type?: string;
  expected_answer?: string | "UNKNOWN";
  expected_fields?: string[];
  expected_answer_contains?: Record<string, unknown>;
  expected_unknown_reason_contains?: string;
  expected_trace_contains?: string[];
}

interface TestResult {
  name: string;
  passed: boolean;
  error?: string;
  duration: number;
}

function loadTests(): GoldenTest[] {
  const tests: GoldenTest[] = [];

  if (!fs.existsSync(TESTS_DIR)) {
    console.log("No tests directory found.");
    return [];
  }

  const files = fs.readdirSync(TESTS_DIR).sort();

  for (const file of files) {
    if (!file.endsWith(".yaml") && !file.endsWith(".yml")) {
      continue;
    }

    const filePath = path.join(TESTS_DIR, file);
    const content = fs.readFileSync(filePath, "utf-8");
    const docs = yaml.loadAll(content) as GoldenTest[];

    for (const doc of docs) {
      if (doc && doc.name && doc.query) {
        tests.push(doc);
      }
    }
  }

  return tests;
}

function runQuery(query: string): { result: Record<string, unknown>; duration: number } {
  const start = Date.now();

  try {
    const output = execSync(`npx ts-node tools/query.ts "${query}"`, {
      cwd: ROOT_DIR,
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });

    const result = JSON.parse(output.trim());
    return { result, duration: Date.now() - start };
  } catch (err) {
    const error = err as { stdout?: string; stderr?: string };
    if (error.stdout) {
      try {
        const result = JSON.parse(error.stdout.trim());
        return { result, duration: Date.now() - start };
      } catch {
        throw new Error(`Query failed: ${error.stderr || "unknown error"}`);
      }
    }
    throw err;
  }
}

function validateResult(
  test: GoldenTest,
  result: Record<string, unknown>
): { passed: boolean; error?: string } {
  // Check expected_answer
  if (test.expected_answer !== undefined) {
    if (test.expected_answer === "UNKNOWN") {
      if (result.answer !== "UNKNOWN") {
        return {
          passed: false,
          error: `Expected UNKNOWN but got: ${JSON.stringify(result.answer)}`,
        };
      }
    } else if (result.answer !== test.expected_answer) {
      return {
        passed: false,
        error: `Expected answer "${test.expected_answer}" but got: ${JSON.stringify(result.answer)}`,
      };
    }
  }

  // Check expected_type
  if (test.expected_type) {
    const answerType = typeof result.answer;
    if (answerType !== test.expected_type) {
      return {
        passed: false,
        error: `Expected type "${test.expected_type}" but got "${answerType}"`,
      };
    }
  }

  // Check expected_fields
  if (test.expected_fields && typeof result.answer === "object" && result.answer !== null) {
    const answer = result.answer as Record<string, unknown>;
    for (const field of test.expected_fields) {
      if (!(field in answer)) {
        return {
          passed: false,
          error: `Missing expected field: ${field}`,
        };
      }
    }
  }

  // Check expected_answer_contains
  if (test.expected_answer_contains && typeof result.answer === "object" && result.answer !== null) {
    const answer = result.answer as Record<string, unknown>;
    for (const [key, value] of Object.entries(test.expected_answer_contains)) {
      if (answer[key] !== value) {
        return {
          passed: false,
          error: `Expected ${key}=${JSON.stringify(value)} but got ${JSON.stringify(answer[key])}`,
        };
      }
    }
  }

  // Check expected_unknown_reason_contains
  if (test.expected_unknown_reason_contains && result.unknownReason) {
    const reason = result.unknownReason as string;
    if (!reason.includes(test.expected_unknown_reason_contains)) {
      return {
        passed: false,
        error: `Unknown reason doesn't contain "${test.expected_unknown_reason_contains}": ${reason}`,
      };
    }
  }

  // Check expected_trace_contains
  if (test.expected_trace_contains && Array.isArray(result.trace)) {
    const traceSteps = (result.trace as Array<{ stepType: string }>).map((s) => s.stepType);
    for (const expectedStep of test.expected_trace_contains) {
      if (!traceSteps.includes(expectedStep)) {
        return {
          passed: false,
          error: `Trace missing step type: ${expectedStep}`,
        };
      }
    }
  }

  return { passed: true };
}

async function main(): Promise<void> {
  console.log("ORIGIN Test Runner");
  console.log("==================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load tests
  const tests = loadTests();
  console.log(`Found ${tests.length} golden tests.\n`);

  if (tests.length === 0) {
    console.log("No tests to run.");
    return;
  }

  // Run tests
  const results: TestResult[] = [];

  for (const test of tests) {
    process.stdout.write(`  ${test.name}... `);

    try {
      const { result, duration } = runQuery(test.query);
      const validation = validateResult(test, result);

      if (validation.passed) {
        console.log(`\u2713 (${duration}ms)`);
        results.push({ name: test.name, passed: true, duration });
      } else {
        console.log(`\u2717`);
        console.log(`    Error: ${validation.error}`);
        results.push({
          name: test.name,
          passed: false,
          error: validation.error,
          duration,
        });
      }
    } catch (err) {
      console.log(`\u2717`);
      console.log(`    Error: ${(err as Error).message}`);
      results.push({
        name: test.name,
        passed: false,
        error: (err as Error).message,
        duration: 0,
      });
    }
  }

  // Summary
  console.log("\n---");
  const passed = results.filter((r) => r.passed).length;
  const failed = results.filter((r) => !r.passed).length;
  console.log(`Passed: ${passed}/${results.length}`);
  console.log(`Failed: ${failed}/${results.length}`);

  if (failed > 0) {
    console.log("\nFailed tests:");
    for (const result of results.filter((r) => !r.passed)) {
      console.log(`  - ${result.name}: ${result.error}`);
    }
    process.exit(1);
  }

  console.log("\nAll tests passed!");
}

main().catch((err) => {
  console.error("Test run failed:", err);
  process.exit(1);
});
