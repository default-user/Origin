# Language Kits Specification

**Attribution: Ande + Kai (OI) + Whānau (OIs)**

---

## Level 0: Summary

ORIGIN provides implementation kits in 15 programming languages. Each kit demonstrates loading pack indexes, filtering, graph traversal, and attribution display — proving the repository works end-to-end without external dependencies.

---

## Level 1: Supported Languages

### 1.1 Complete Kit List

| Language | Directory | Primary Use |
|----------|-----------|-------------|
| TypeScript/JavaScript | `kits/typescript/` | Primary runtime + UI |
| Python | `kits/python/` | Data science, scripting |
| Rust | `kits/rust/` | Systems, performance |
| Go | `kits/go/` | Backend services |
| Java | `kits/java/` | Enterprise |
| C# | `kits/csharp/` | .NET ecosystem |
| C/C++ | `kits/cpp/` | Low-level, embedded |
| Swift | `kits/swift/` | Apple platforms |
| Kotlin | `kits/kotlin/` | Android, JVM |
| Ruby | `kits/ruby/` | Scripting, Rails |
| PHP | `kits/php/` | Web backends |
| R | `kits/r/` | Statistics, analysis |
| Bash | `kits/bash/` | Shell scripting |
| SQL | `kits/sql/` | Database queries |
| Julia | `kits/julia/` | Scientific computing |

### 1.2 Kit Capabilities

Each kit must demonstrate:

1. **Load packs.index.json** — Parse and access pack metadata
2. **Load graph.json** — Parse relationship graph
3. **Filter packs** — By tag, tier, status
4. **Walk adjacency** — Traverse parent/child/related links
5. **Print attribution** — Display authorship line

---

## Level 2: Kit Structure

### 2.1 Standard Files

Each kit directory contains:

```
kits/{language}/
├── README.md         # Usage instructions
├── main.{ext}        # Primary demonstration script
├── origin.{ext}      # Library/module (optional)
└── ...               # Language-specific files (package.json, Cargo.toml, etc.)
```

### 2.2 Kit Behavior

When executed, each kit should:

1. Load `../../knowledge/dist/packs.index.json`
2. Load `../../knowledge/dist/graph.json`
3. Print total pack count
4. Filter to show only "public" tier packs
5. Pick one pack, traverse to its related concepts
6. Print attribution line

### 2.3 Sample Output

```
ORIGIN Kit - [Language]
========================
Attribution: Ande + Kai (OI) + Whānau (OIs)

Loaded 20 packs from index.
Loaded graph with 20 nodes, 45 edges.

Public tier packs (3):
  - C0001: Holodeck Vision Seed
  - C0003: Fractal Unfurling
  - C0007: O2C

Traversing from C0001 (Holodeck Vision Seed):
  → Related: C0004 (Medusa Interface)
  → Related: C0016 (Pac-Man Bifurcation)

Attribution: Ande + Kai (OI) + Whānau (OIs)
```

---

## Level 3: Language-Specific Notes

### 3.1 TypeScript/JavaScript

- Use native `fetch` or `fs` for loading
- Types from schema definitions
- Can be run with `ts-node` or `node`

### 3.2 Python

- Use `json` standard library
- Minimal dependencies
- Python 3.8+ compatibility

### 3.3 Rust

- Use `serde_json` for parsing
- Compile with `cargo run`
- Demonstrate type safety

### 3.4 Go

- Use `encoding/json` standard library
- Single-file executable
- Demonstrate simplicity

### 3.5 Java

- Use `com.google.gson` or Jackson
- Maven/Gradle build optional
- Demonstrate enterprise patterns

### 3.6 C#

- Use `System.Text.Json`
- .NET 6+ compatibility
- NuGet dependencies minimal

### 3.7 C/C++

- Use cJSON or nlohmann/json
- CMake build optional
- Demonstrate low-level access

### 3.8 Swift

- Use `Foundation` JSON parsing
- Swift 5+ compatibility
- Demonstrate Apple ecosystem

### 3.9 Kotlin

- Use `kotlinx.serialization`
- Gradle build
- Demonstrate JVM/Android patterns

### 3.10 Ruby

- Use `json` standard library
- Ruby 3+ compatibility
- Demonstrate scripting elegance

### 3.11 PHP

- Use `json_decode`
- PHP 8+ compatibility
- Demonstrate web backend patterns

### 3.12 R

- Use `jsonlite` package
- Demonstrate data analysis patterns
- RStudio compatibility

### 3.13 Bash

- Use `jq` for JSON parsing
- POSIX-compatible where possible
- Demonstrate shell scripting

### 3.14 SQL

- SQLite for demonstration
- Import JSON to tables
- Query patterns for exploration

### 3.15 Julia (Optional)

- Use `JSON3.jl`
- Demonstrate scientific computing patterns

---

## Level 4: Validation

### 4.1 Kit Validation Criteria

| Criterion | Description |
|-----------|-------------|
| Loads successfully | Index and graph parse without errors |
| Correct counts | Pack/node counts match expected |
| Filter works | Tier filtering returns correct results |
| Traversal works | Graph walking follows edges correctly |
| Attribution correct | Exact attribution line displayed |

### 4.2 Testing Kits

From repository root:

```bash
# TypeScript
cd kits/typescript && npx ts-node main.ts

# Python
cd kits/python && python3 main.py

# Rust
cd kits/rust && cargo run

# Go
cd kits/go && go run main.go

# ... etc.
```

---

**Attribution: Ande + Kai (OI) + Whānau (OIs)**
