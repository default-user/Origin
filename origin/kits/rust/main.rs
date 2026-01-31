// ORIGIN Rust Kit
// Demonstrates loading and exploring ORIGIN knowledge packs
//
// Attribution: Ande + Kai (OI) + Whānau (OIs)
//
// To run: cargo run (requires Cargo.toml setup)
// Or: rustc main.rs -o origin_kit && ./origin_kit

use std::fs;
use std::path::Path;

const ATTRIBUTION: &str = "Ande + Kai (OI) + Whānau (OIs)";

fn main() {
    println!("ORIGIN Kit - Rust");
    println!("=================");
    println!("Attribution: {}\n", ATTRIBUTION);

    // Load index
    let index_path = Path::new("../../knowledge/dist/packs.index.json");
    let index_content = match fs::read_to_string(index_path) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error loading index: {}", e);
            return;
        }
    };

    // Parse JSON (using simple string parsing for demo)
    let pack_count = index_content.matches("\"id\":").count();
    println!("Loaded {} packs from index.", pack_count);

    // Load graph
    let graph_path = Path::new("../../knowledge/dist/graph.json");
    let graph_content = match fs::read_to_string(graph_path) {
        Ok(content) => content,
        Err(e) => {
            eprintln!("Error loading graph: {}", e);
            return;
        }
    };

    let node_count = graph_content.matches("\"id\":").count();
    let edge_count = graph_content.matches("\"source\":").count();
    println!("Loaded graph with {} nodes, {} edges.\n", node_count, edge_count);

    // Note: Full JSON parsing would use serde_json crate
    println!("(Full implementation requires serde_json crate)");
    println!("\nAttribution: {}", ATTRIBUTION);
}
