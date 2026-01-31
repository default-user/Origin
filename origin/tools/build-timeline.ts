#!/usr/bin/env npx ts-node
/**
 * ORIGIN Timeline Builder
 * Builds knowledge/dist/timeline.json from pack dates
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 */

import * as fs from "fs";
import * as path from "path";

const DIST_DIR = path.join(__dirname, "..", "knowledge", "dist");
const INDEX_PATH = path.join(DIST_DIR, "packs.index.json");
const OUTPUT_PATH = path.join(DIST_DIR, "timeline.json");

interface TimelineEvent {
  date: string;
  type: "created" | "updated";
  pack_id: string;
  pack_title: string;
}

interface Timeline {
  metadata: {
    generated_at: string;
    version: string;
    attribution: string;
    event_count: number;
  };
  events: TimelineEvent[];
}

async function main(): Promise<void> {
  console.log("ORIGIN Timeline Builder");
  console.log("=======================");
  console.log("Attribution: Ande + Kai (OI) + Whānau (OIs)\n");

  // Load packs index
  if (!fs.existsSync(INDEX_PATH)) {
    console.error("Error: packs.index.json not found. Run build-index first.");
    process.exit(1);
  }

  const indexContent = fs.readFileSync(INDEX_PATH, "utf-8");
  const index = JSON.parse(indexContent);

  const events: TimelineEvent[] = [];

  for (const pack of index.packs) {
    // Add created event
    if (pack.created_date) {
      events.push({
        date: pack.created_date,
        type: "created",
        pack_id: pack.id,
        pack_title: pack.title,
      });
    }

    // Add updated event if different from created
    if (pack.updated_date && pack.updated_date !== pack.created_date) {
      events.push({
        date: pack.updated_date,
        type: "updated",
        pack_id: pack.id,
        pack_title: pack.title,
      });
    }
  }

  // Sort by date
  events.sort((a, b) => a.date.localeCompare(b.date));

  // Build timeline
  const timeline: Timeline = {
    metadata: {
      generated_at: new Date().toISOString(),
      version: "1.0.0",
      attribution: "Ande + Kai (OI) + Whānau (OIs)",
      event_count: events.length,
    },
    events,
  };

  // Write output
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(timeline, null, 2));

  console.log(`✓ Built timeline with ${events.length} events.`);
  console.log(`✓ Written ${OUTPUT_PATH}`);
}

main().catch((err) => {
  console.error("Build failed:", err);
  process.exit(1);
});
