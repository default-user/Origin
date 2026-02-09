//! Canonical serialization: stable, deterministic output for Denotum structures.
//!
//! Guarantees:
//! - Same input always produces identical byte output.
//! - BTreeMap keys are sorted (inherent in BTreeMap + serde).
//! - Vectors preserve insertion order.
//! - No floating-point ambiguity (all strings/ints/bools).

use crate::denotum::Denotum;
use sha2::{Digest, Sha256};

/// Serialize a Denotum to canonical JSON bytes.
///
/// Uses serde_json without pretty-printing for minimal, deterministic output.
/// BTreeMap ensures sorted keys.
pub fn canonical_json(d: &Denotum) -> Result<Vec<u8>, serde_json::Error> {
    serde_json::to_vec(d)
}

/// Serialize a Denotum to canonical pretty JSON bytes.
///
/// Same determinism guarantees as `canonical_json`, but human-readable.
pub fn canonical_json_pretty(d: &Denotum) -> Result<Vec<u8>, serde_json::Error> {
    serde_json::to_vec_pretty(d)
}

/// Compute the SHA-256 fingerprint of a Denotum's canonical form.
pub fn canonical_fingerprint(d: &Denotum) -> Result<String, serde_json::Error> {
    let bytes = canonical_json(d)?;
    let mut hasher = Sha256::new();
    hasher.update(&bytes);
    Ok(hex::encode(hasher.finalize()))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::denotum::*;
    use std::collections::BTreeMap;

    fn test_denotum() -> Denotum {
        Denotum {
            version: "v1.0".to_string(),
            steward: "Ande".to_string(),
            posture: "FAIL_CLOSED".to_string(),
            stop_wins: true,
            glossary: {
                let mut m = BTreeMap::new();
                m.insert(
                    "ZZZ".to_string(),
                    GlossaryEntry {
                        definition: "last".to_string(),
                    },
                );
                m.insert(
                    "AAA".to_string(),
                    GlossaryEntry {
                        definition: "first".to_string(),
                    },
                );
                m
            },
            axioms: BTreeMap::new(),
            posture_ladder: PostureLadder {
                levels: BTreeMap::new(),
                degrade_rule: String::new(),
            },
            layers: vec![],
            beams: vec![],
            lattices: vec![],
            prisms: vec![],
            blocker_registry: BlockerRegistry::default(),
        }
    }

    #[test]
    fn test_canonical_deterministic() {
        let d = test_denotum();
        let a = canonical_json(&d).unwrap();
        let b = canonical_json(&d).unwrap();
        assert_eq!(a, b);
    }

    #[test]
    fn test_canonical_sorted_keys() {
        let d = test_denotum();
        let json = String::from_utf8(canonical_json(&d).unwrap()).unwrap();
        let apos = json.find("AAA").unwrap();
        let zpos = json.find("ZZZ").unwrap();
        assert!(apos < zpos, "glossary keys must be sorted");
    }

    #[test]
    fn test_fingerprint_stable() {
        let d = test_denotum();
        let fp1 = canonical_fingerprint(&d).unwrap();
        let fp2 = canonical_fingerprint(&d).unwrap();
        assert_eq!(fp1, fp2);
        assert_eq!(fp1.len(), 64);
    }

    #[test]
    fn test_fingerprint_changes_on_mutation() {
        let d1 = test_denotum();
        let mut d2 = test_denotum();
        d2.version = "v2.0".to_string();
        let fp1 = canonical_fingerprint(&d1).unwrap();
        let fp2 = canonical_fingerprint(&d2).unwrap();
        assert_ne!(fp1, fp2);
    }
}
