#!/usr/bin/env swift
/**
 * ORIGIN Swift Kit
 * Demonstrates loading and exploring ORIGIN knowledge packs
 *
 * Attribution: Ande + Kai (OI) + Whānau (OIs)
 *
 * To run: swift main.swift
 */

import Foundation

let ATTRIBUTION = "Ande + Kai (OI) + Whānau (OIs)"

struct Pack: Decodable {
    let id: String
    let title: String
    let disclosure_tier: String
}

struct PacksIndex: Decodable {
    let packs: [Pack]
}

struct GraphMetadata: Decodable {
    let node_count: Int
    let edge_count: Int
}

struct Graph: Decodable {
    let metadata: GraphMetadata
}

func loadJSON<T: Decodable>(_ filename: String) throws -> T {
    let path = "../../knowledge/dist/\(filename)"
    let url = URL(fileURLWithPath: path)
    let data = try Data(contentsOf: url)
    return try JSONDecoder().decode(T.self, from: data)
}

print("ORIGIN Kit - Swift")
print("==================")
print("Attribution: \(ATTRIBUTION)\n")

do {
    // Load index
    let index: PacksIndex = try loadJSON("packs.index.json")
    print("Loaded \(index.packs.count) packs from index.")

    // Load graph
    let graph: Graph = try loadJSON("graph.json")
    print("Loaded graph with \(graph.metadata.node_count) nodes, \(graph.metadata.edge_count) edges.\n")

    // Filter to public tier
    let publicPacks = index.packs.filter { $0.disclosure_tier == "public" }
    print("Public tier packs (\(publicPacks.count)):")
    for pack in publicPacks.prefix(3) {
        print("  - \(pack.id): \(pack.title)")
    }
    if publicPacks.count > 3 {
        print("  ... and \(publicPacks.count - 3) more")
    }

    print("\nAttribution: \(ATTRIBUTION)")

} catch {
    print("Error: \(error)")
}
