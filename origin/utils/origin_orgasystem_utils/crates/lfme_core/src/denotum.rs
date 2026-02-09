//! Denotum structs: the typed representation of a 2I seed.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// Top-level Denotum seed structure.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Denotum {
    /// Seed version string (e.g. "v1.0").
    pub version: String,
    /// Steward name.
    pub steward: String,
    /// Posture mode (e.g. "FAIL_CLOSED").
    pub posture: String,
    /// Whether stop-wins governance is active.
    pub stop_wins: bool,
    /// Glossary: term -> definition.
    pub glossary: BTreeMap<String, GlossaryEntry>,
    /// Axioms: id -> axiom.
    pub axioms: BTreeMap<String, Axiom>,
    /// Posture ladder levels.
    pub posture_ladder: PostureLadder,
    /// Layers in the 2I stack.
    pub layers: Vec<Layer>,
    /// Beams (atomic meaning-bearing claims).
    #[serde(default)]
    pub beams: Vec<Beam>,
    /// Lattices (composed beams).
    #[serde(default)]
    pub lattices: Vec<Lattice>,
    /// Prisms (behavioral refractors).
    #[serde(default)]
    pub prisms: Vec<Prism>,
    /// Blocker registry.
    #[serde(default)]
    pub blocker_registry: BlockerRegistry,
}

/// A glossary entry: short name + full definition.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct GlossaryEntry {
    pub definition: String,
}

/// An axiom with an ID and statement.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Axiom {
    pub statement: String,
}

/// Posture ladder: governance levels L0-L3.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct PostureLadder {
    pub levels: BTreeMap<String, String>,
    pub degrade_rule: String,
}

/// A layer in the 2I stack.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Layer {
    pub name: String,
    pub purpose: String,
    #[serde(default)]
    pub invariants: Vec<String>,
    #[serde(default)]
    pub operators: Vec<String>,
    #[serde(default)]
    pub artifacts: Vec<String>,
}

/// A beam: atomic meaning-bearing claim.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Beam {
    pub id: String,
    pub claim: String,
    #[serde(default)]
    pub provenance: String,
    #[serde(default)]
    pub tests: Vec<String>,
}

/// A lattice: composed set of beams.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Lattice {
    pub id: String,
    pub name: String,
    pub beam_ids: Vec<String>,
}

/// A prism: behavioral refractor (tool, adapter, judge).
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Prism {
    pub id: String,
    pub kind: String,
    pub description: String,
}

/// Blocker registry: explicit list of current blockers.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
pub struct BlockerRegistry {
    #[serde(default)]
    pub blockers: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_denotum_serde_roundtrip() {
        let d = Denotum {
            version: "v1.0".to_string(),
            steward: "Ande".to_string(),
            posture: "FAIL_CLOSED".to_string(),
            stop_wins: true,
            glossary: {
                let mut m = BTreeMap::new();
                m.insert(
                    "2I".to_string(),
                    GlossaryEntry {
                        definition: "Integrated Intelligence".to_string(),
                    },
                );
                m
            },
            axioms: {
                let mut m = BTreeMap::new();
                m.insert(
                    "A1".to_string(),
                    Axiom {
                        statement: "People first".to_string(),
                    },
                );
                m
            },
            posture_ladder: PostureLadder {
                levels: {
                    let mut m = BTreeMap::new();
                    m.insert("L0".to_string(), "READ_ONLY".to_string());
                    m
                },
                degrade_rule: "drop one level".to_string(),
            },
            layers: vec![Layer {
                name: "OI".to_string(),
                purpose: "Ongoing Intelligence".to_string(),
                invariants: vec!["no personhood claims".to_string()],
                operators: vec!["FRAME".to_string()],
                artifacts: vec!["Beams".to_string()],
            }],
            beams: vec![],
            lattices: vec![],
            prisms: vec![],
            blocker_registry: BlockerRegistry::default(),
        };

        let json = serde_json::to_string_pretty(&d).unwrap();
        let parsed: Denotum = serde_json::from_str(&json).unwrap();
        assert_eq!(d, parsed);
    }

    #[test]
    fn test_glossary_sorted() {
        let mut g = BTreeMap::new();
        g.insert(
            "ZZZ".to_string(),
            GlossaryEntry {
                definition: "last".to_string(),
            },
        );
        g.insert(
            "AAA".to_string(),
            GlossaryEntry {
                definition: "first".to_string(),
            },
        );
        let json = serde_json::to_string(&g).unwrap();
        let apos = json.find("AAA").unwrap();
        let zpos = json.find("ZZZ").unwrap();
        assert!(apos < zpos, "BTreeMap must serialize in sorted order");
    }
}
