#!/usr/bin/env julia
# ORIGIN Julia Kit
# Demonstrates loading and exploring ORIGIN knowledge packs
#
# Attribution: Ande + Kai (OI) + Whānau (OIs)
#
# Requires: JSON3 package

using JSON3

const ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"

function load_json(filename)
    path = joinpath(@__DIR__, "..", "..", "knowledge", "dist", filename)
    return JSON3.read(read(path, String))
end

println("ORIGIN Kit - Julia")
println("==================")
println("Attribution: $ATTRIBUTION\n")

# Load index
index = load_json("packs.index.json")
packs = index.packs
println("Loaded $(length(packs)) packs from index.")

# Load graph
graph = load_json("graph.json")
nodes = graph.nodes
edges = graph.edges
println("Loaded graph with $(length(nodes)) nodes, $(length(edges)) edges.\n")

# Filter to public tier
public_packs = filter(p -> p.disclosure_tier == "public", packs)
println("Public tier packs ($(length(public_packs))):")
for pack in public_packs[1:min(3, length(public_packs))]
    println("  - $(pack.id): $(pack.title)")
end
if length(public_packs) > 3
    println("  ... and $(length(public_packs) - 3) more")
end

# Traverse from first pack
first_pack = packs[1]
println("\nTraversing from $(first_pack.id) ($(first_pack.title)):")

related_edges = filter(e -> e.source == first_pack.id || e.target == first_pack.id, edges)
for edge in related_edges[1:min(3, length(related_edges))]
    other_id = edge.source == first_pack.id ? edge.target : edge.source
    other_pack = findfirst(p -> p.id == other_id, packs)
    title = other_pack !== nothing ? packs[other_pack].title : "Unknown"
    println("  → $(edge.type): $other_id ($title)")
end

println("\nAttribution: $ATTRIBUTION")
