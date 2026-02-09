//! LFME/Denotum: Deterministic meaning structures.
//!
//! This crate implements the Denotum model from the 2I seed:
//! - Denotum structs (Beam, Lattice, Prism, Seed envelope)
//! - Parser for YAML/JSON input
//! - Validator enforcing seed invariants (fail-closed)
//! - Canonical serialization (stable, deterministic)

pub mod canonical;
pub mod denotum;
pub mod parser;
pub mod validator;

pub use denotum::{
    Axiom, Beam, BlockerRegistry, Denotum, GlossaryEntry, Lattice, Layer, PostureLadder, Prism,
};
pub use parser::parse_seed;
pub use validator::{validate_denotum, ValidationError};
