//! Validator: enforce Denotum seed invariants.
//!
//! Fail-closed: if any required invariant is violated, validation fails.

use crate::denotum::Denotum;

#[derive(Debug, thiserror::Error)]
pub enum ValidationError {
    #[error("missing required field: {field}")]
    MissingField { field: String },
    #[error("invariant violated: {invariant}")]
    InvariantViolated { invariant: String },
    #[error("multiple errors: {0:?}")]
    Multiple(Vec<ValidationError>),
}

/// Validation result containing all errors found.
#[derive(Debug)]
pub struct ValidationResult {
    pub errors: Vec<ValidationError>,
}

impl ValidationResult {
    pub fn is_valid(&self) -> bool {
        self.errors.is_empty()
    }
}

/// Validate a Denotum seed against all structural invariants.
///
/// Returns a list of errors. Empty list = valid.
pub fn validate_denotum(d: &Denotum) -> ValidationResult {
    let mut errors = Vec::new();

    // R1: Version must be present and non-empty.
    if d.version.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "version".to_string(),
        });
    }

    // R2: Steward must be present and non-empty.
    if d.steward.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "steward".to_string(),
        });
    }

    // R3: Posture must be FAIL_CLOSED (only supported mode in v1).
    if d.posture != "FAIL_CLOSED" {
        errors.push(ValidationError::InvariantViolated {
            invariant: format!(
                "posture must be FAIL_CLOSED in v1, got '{}'",
                d.posture
            ),
        });
    }

    // R4: stop_wins must be true.
    if !d.stop_wins {
        errors.push(ValidationError::InvariantViolated {
            invariant: "stop_wins must be true".to_string(),
        });
    }

    // R5: Glossary must be non-empty.
    if d.glossary.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "glossary (must have at least one entry)".to_string(),
        });
    }

    // R6: At least one axiom required.
    if d.axioms.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "axioms (must have at least one)".to_string(),
        });
    }

    // R7: Posture ladder must have at least L0.
    if !d.posture_ladder.levels.contains_key("L0") {
        errors.push(ValidationError::InvariantViolated {
            invariant: "posture ladder must define L0".to_string(),
        });
    }

    // R8: Degrade rule must be non-empty.
    if d.posture_ladder.degrade_rule.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "posture_ladder.degrade_rule".to_string(),
        });
    }

    // R9: At least one layer required.
    if d.layers.is_empty() {
        errors.push(ValidationError::MissingField {
            field: "layers (must have at least one)".to_string(),
        });
    }

    // R10: All beams must have non-empty id and claim.
    for (i, beam) in d.beams.iter().enumerate() {
        if beam.id.is_empty() {
            errors.push(ValidationError::InvariantViolated {
                invariant: format!("beam[{i}] has empty id"),
            });
        }
        if beam.claim.is_empty() {
            errors.push(ValidationError::InvariantViolated {
                invariant: format!("beam[{i}] has empty claim"),
            });
        }
    }

    // R11: Lattice beam_ids must be non-empty and reference valid beams.
    let beam_ids: std::collections::BTreeSet<&str> =
        d.beams.iter().map(|b| b.id.as_str()).collect();
    for (i, lattice) in d.lattices.iter().enumerate() {
        if lattice.beam_ids.is_empty() {
            errors.push(ValidationError::InvariantViolated {
                invariant: format!("lattice[{i}] has no beam_ids"),
            });
        }
        for bid in &lattice.beam_ids {
            if !beam_ids.contains(bid.as_str()) && !d.beams.is_empty() {
                errors.push(ValidationError::InvariantViolated {
                    invariant: format!(
                        "lattice[{i}] references unknown beam '{bid}'"
                    ),
                });
            }
        }
    }

    ValidationResult { errors }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::denotum::*;
    use std::collections::BTreeMap;

    fn minimal_valid() -> Denotum {
        Denotum {
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
                purpose: "continuity".to_string(),
                invariants: vec![],
                operators: vec![],
                artifacts: vec![],
            }],
            beams: vec![],
            lattices: vec![],
            prisms: vec![],
            blocker_registry: BlockerRegistry::default(),
        }
    }

    #[test]
    fn test_valid_seed() {
        let d = minimal_valid();
        let result = validate_denotum(&d);
        assert!(result.is_valid(), "errors: {:?}", result.errors);
    }

    #[test]
    fn test_missing_version() {
        let mut d = minimal_valid();
        d.version = String::new();
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_missing_steward() {
        let mut d = minimal_valid();
        d.steward = String::new();
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_wrong_posture() {
        let mut d = minimal_valid();
        d.posture = "OPEN".to_string();
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_stop_wins_false() {
        let mut d = minimal_valid();
        d.stop_wins = false;
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_empty_glossary() {
        let mut d = minimal_valid();
        d.glossary.clear();
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_beam_empty_id() {
        let mut d = minimal_valid();
        d.beams.push(Beam {
            id: String::new(),
            claim: "test".to_string(),
            provenance: String::new(),
            tests: vec![],
        });
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }

    #[test]
    fn test_lattice_unknown_beam() {
        let mut d = minimal_valid();
        d.beams.push(Beam {
            id: "B1".to_string(),
            claim: "test".to_string(),
            provenance: String::new(),
            tests: vec![],
        });
        d.lattices.push(Lattice {
            id: "L1".to_string(),
            name: "test lattice".to_string(),
            beam_ids: vec!["NONEXISTENT".to_string()],
        });
        let result = validate_denotum(&d);
        assert!(!result.is_valid());
    }
}
