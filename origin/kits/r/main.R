#!/usr/bin/env Rscript
# ORIGIN R Kit
# Demonstrates loading and exploring ORIGIN knowledge packs
#
# Attribution: Ande + Kai (OI) + Whānau (OIs)
#
# Requires: jsonlite package

library(jsonlite)

ATTRIBUTION <- "Ande + Kai (OI) + Whānau (OIs)"

cat("ORIGIN Kit - R\n")
cat("==============\n")
cat(paste("Attribution:", ATTRIBUTION, "\n\n"))

# Load index
index_path <- file.path(dirname(getwd()), "..", "knowledge", "dist", "packs.index.json")
index <- fromJSON("../../knowledge/dist/packs.index.json")
packs <- index$packs

cat(paste("Loaded", nrow(packs), "packs from index.\n"))

# Load graph
graph <- fromJSON("../../knowledge/dist/graph.json")
nodes <- graph$nodes
edges <- graph$edges

cat(paste("Loaded graph with", nrow(nodes), "nodes,", nrow(edges), "edges.\n\n"))

# Filter to public tier
public_packs <- packs[packs$disclosure_tier == "public", ]
cat(paste("Public tier packs (", nrow(public_packs), "):\n", sep = ""))

for (i in 1:min(3, nrow(public_packs))) {
  pack <- public_packs[i, ]
  cat(paste("  -", pack$id, ":", pack$title, "\n"))
}
if (nrow(public_packs) > 3) {
  cat(paste("  ... and", nrow(public_packs) - 3, "more\n"))
}

# Traverse from first pack
first_pack <- packs[1, ]
cat(paste("\nTraversing from", first_pack$id, "(", first_pack$title, "):\n"))

related_edges <- edges[edges$source == first_pack$id | edges$target == first_pack$id, ]

for (i in 1:min(3, nrow(related_edges))) {
  edge <- related_edges[i, ]
  other_id <- ifelse(edge$source == first_pack$id, edge$target, edge$source)
  other_pack <- packs[packs$id == other_id, ]
  title <- ifelse(nrow(other_pack) > 0, other_pack$title[1], "Unknown")
  cat(paste("  →", edge$type, ":", other_id, "(", title, ")\n"))
}

cat(paste("\nAttribution:", ATTRIBUTION, "\n"))
