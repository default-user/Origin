//! Parser: load Denotum seeds from YAML or JSON.

use crate::denotum::*;
use std::collections::BTreeMap;
use std::path::Path;

#[derive(Debug, thiserror::Error)]
pub enum ParseError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("YAML parse error: {0}")]
    Yaml(#[from] serde_yaml::Error),
    #[error("JSON parse error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("unsupported format: {0}")]
    UnsupportedFormat(String),
    #[error("missing required field: {0}")]
    MissingField(String),
}

/// Parse a Denotum seed from a YAML string (the canonical 2I seed format).
///
/// The raw YAML uses a non-standard layout; this parser maps it to the
/// typed Denotum struct. Non-YAML header lines (like `DENOTUM::SEED::2I`)
/// are stripped before parsing.
pub fn parse_seed(input: &str) -> Result<Denotum, ParseError> {
    // Strip non-YAML header lines (e.g., "DENOTUM::SEED::2I")
    let cleaned: String = input
        .lines()
        .filter(|line| {
            let trimmed = line.trim();
            trimmed.is_empty()
                || trimmed.starts_with('#')
                || trimmed.contains(": ")
                || trimmed.ends_with(':')
                || trimmed.starts_with("- ")
                || trimmed.starts_with("  ")
        })
        .collect::<Vec<_>>()
        .join("\n");

    let raw: serde_yaml::Value = serde_yaml::from_str(&cleaned)?;

    let version = extract_string(&raw, "VERSION").unwrap_or_else(|| "v1.0".to_string());
    let steward = extract_string(&raw, "STEWARD").unwrap_or_else(|| "unknown".to_string());
    let posture = extract_string(&raw, "POSTURE").unwrap_or_else(|| "FAIL_CLOSED".to_string());
    let stop_wins = raw
        .get("STOP_WINS")
        .and_then(|v| v.as_bool())
        .unwrap_or(true);

    // Glossary
    let glossary = parse_glossary(&raw);

    // Axioms
    let axioms = parse_axioms(&raw);

    // Posture ladder
    let posture_ladder = parse_posture_ladder(&raw);

    // Layers
    let layers = parse_layers(&raw);

    // Blocker registry
    let blocker_registry = parse_blocker_registry(&raw);

    Ok(Denotum {
        version,
        steward,
        posture,
        stop_wins,
        glossary,
        axioms,
        posture_ladder,
        layers,
        beams: vec![],
        lattices: vec![],
        prisms: vec![],
        blocker_registry,
    })
}

/// Parse a Denotum seed from a file (YAML or JSON, detected by extension).
pub fn parse_seed_file(path: &Path) -> Result<Denotum, ParseError> {
    let content = std::fs::read_to_string(path)?;
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("");
    match ext {
        "yaml" | "yml" => parse_seed(&content),
        "json" => {
            let d: Denotum = serde_json::from_str(&content)?;
            Ok(d)
        }
        _ => Err(ParseError::UnsupportedFormat(ext.to_string())),
    }
}

fn extract_string(val: &serde_yaml::Value, key: &str) -> Option<String> {
    val.get(key).and_then(|v| v.as_str()).map(|s| s.to_string())
}

fn parse_glossary(raw: &serde_yaml::Value) -> BTreeMap<String, GlossaryEntry> {
    let mut map = BTreeMap::new();
    if let Some(g) = raw.get("GLOSSARY").and_then(|v| v.as_mapping()) {
        for (k, v) in g {
            if let (Some(key), Some(def)) = (k.as_str(), v.as_str()) {
                map.insert(
                    key.to_string(),
                    GlossaryEntry {
                        definition: def.to_string(),
                    },
                );
            }
        }
    }
    map
}

fn parse_axioms(raw: &serde_yaml::Value) -> BTreeMap<String, Axiom> {
    let mut map = BTreeMap::new();
    if let Some(a) = raw.get("AXIOMS").and_then(|v| v.as_mapping()) {
        for (k, v) in a {
            if let (Some(key), Some(stmt)) = (k.as_str(), v.as_str()) {
                map.insert(
                    key.to_string(),
                    Axiom {
                        statement: stmt.to_string(),
                    },
                );
            }
        }
    }
    map
}

fn parse_posture_ladder(raw: &serde_yaml::Value) -> PostureLadder {
    let mut levels = BTreeMap::new();
    let mut degrade_rule = String::new();
    if let Some(pl) = raw.get("POSTURE_LADDER").and_then(|v| v.as_mapping()) {
        for (k, v) in pl {
            if let Some(key) = k.as_str() {
                if key == "degrade_rule" {
                    degrade_rule = v.as_str().unwrap_or("").to_string();
                } else if let Some(val) = v.as_str() {
                    levels.insert(key.to_string(), val.to_string());
                }
            }
        }
    }
    PostureLadder {
        levels,
        degrade_rule,
    }
}

fn parse_layers(raw: &serde_yaml::Value) -> Vec<Layer> {
    let layer_names = ["OI", "SGS", "STANGRAPHICS", "GSI", "NSCE", "2I"];
    let mut layers = Vec::new();

    for name in &layer_names {
        if let Some(section) = raw.get(*name) {
            let purpose = section
                .get("PURPOSE")
                .or_else(|| section.get("DEFINITION"))
                .or_else(|| section.get("ROLE"))
                .or_else(|| section.get("CLAIM"))
                .and_then(|v| match v {
                    serde_yaml::Value::String(s) => Some(s.clone()),
                    serde_yaml::Value::Mapping(_) => {
                        // For OI.DEFINITION which is a mapping
                        Some(format!("{:?}", v))
                    }
                    _ => v.as_str().map(|s| s.to_string()),
                })
                .unwrap_or_default();

            let invariants = extract_string_list(section, "INVARIANTS");
            let operators = extract_string_list(section, "OPERATORS");
            let artifacts = extract_string_list(section, "ARTIFACTS");

            layers.push(Layer {
                name: name.to_string(),
                purpose,
                invariants,
                operators,
                artifacts,
            });
        }
    }

    layers
}

fn extract_string_list(val: &serde_yaml::Value, key: &str) -> Vec<String> {
    val.get(key)
        .and_then(|v| v.as_sequence())
        .map(|seq| {
            seq.iter()
                .filter_map(|item| item.as_str().map(|s| s.to_string()))
                .collect()
        })
        .unwrap_or_default()
}

fn parse_blocker_registry(raw: &serde_yaml::Value) -> BlockerRegistry {
    if let Some(br) = raw.get("BLOCKER_REGISTRY") {
        let blockers = br
            .get("blockers")
            .and_then(|v| v.as_sequence())
            .map(|seq| {
                seq.iter()
                    .filter_map(|item| item.as_str().map(|s| s.to_string()))
                    .collect()
            })
            .unwrap_or_default();
        BlockerRegistry { blockers }
    } else {
        BlockerRegistry::default()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const TEST_SEED: &str = r#"
VERSION: v1.0
STEWARD: Ande
POSTURE: FAIL_CLOSED
STOP_WINS: true

GLOSSARY:
  2I: "Integrated Intelligence"
  OI: "Ongoing Intelligence"

AXIOMS:
  A1_PeopleFirst: "People first, tools serve."
  A2_StopWins: "Stop wins."

POSTURE_LADDER:
  L0: "READ_ONLY"
  L1: "SUGGEST"
  L2: "PLAN"
  L3: "EXECUTE"
  degrade_rule: "Drop one level on guard failure."

OI:
  PURPOSE: "Thread-tending continuity"
  INVARIANTS:
    - "No personhood claims"
  OPERATORS:
    - "FRAME"
    - "GENERATE"
  ARTIFACTS:
    - "Beams"

SGS:
  PURPOSE: "Structural generation"

BLOCKER_REGISTRY:
  blockers: []
"#;

    #[test]
    fn test_parse_seed_basic() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert_eq!(d.version, "v1.0");
        assert_eq!(d.steward, "Ande");
        assert_eq!(d.posture, "FAIL_CLOSED");
        assert!(d.stop_wins);
    }

    #[test]
    fn test_parse_glossary() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert_eq!(d.glossary.len(), 2);
        assert!(d.glossary.contains_key("2I"));
        assert!(d.glossary.contains_key("OI"));
    }

    #[test]
    fn test_parse_axioms() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert_eq!(d.axioms.len(), 2);
        assert!(d.axioms.contains_key("A1_PeopleFirst"));
    }

    #[test]
    fn test_parse_posture_ladder() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert_eq!(d.posture_ladder.levels.len(), 4);
        assert_eq!(
            d.posture_ladder.levels.get("L0").unwrap(),
            "READ_ONLY"
        );
    }

    #[test]
    fn test_parse_layers() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert!(d.layers.len() >= 2);
        assert_eq!(d.layers[0].name, "OI");
        assert_eq!(d.layers[0].operators, vec!["FRAME", "GENERATE"]);
    }

    #[test]
    fn test_parse_blocker_registry_empty() {
        let d = parse_seed(TEST_SEED).unwrap();
        assert!(d.blocker_registry.blockers.is_empty());
    }

    #[test]
    fn test_parse_real_seed_file() {
        let seed_content = std::fs::read_to_string(
            "/home/user/Origin/origin/utils/origin_orgasystem_utils/spec/seed/denotum.seed.2i.yaml",
        );
        if let Ok(content) = seed_content {
            let d = parse_seed(&content).unwrap();
            assert_eq!(d.version, "v1.0");
            assert_eq!(d.steward, "Ande");
            assert!(d.stop_wins);
            assert!(d.glossary.len() >= 6);
            assert!(d.axioms.len() >= 7);
        }
    }
}
