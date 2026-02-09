//! replication_core: Deterministic reproduction of the Origin orgasystem.
//!
//! Replication produces a new instance of the orgasystem preserving structure
//! and root binding. All replicated instances bind to the same root_2i_seed_fingerprint
//! unless explicitly version-bumped by the steward.
//!
//! Modes:
//! - R0_LOCAL_CLONE: pack + unfurl into a new directory (offline)
//! - R1_ROOTBALL_SEED: produce a DPACK rootball for transport
//! - R2_ZIP_TO_FRESH_REPO_V1: unfurl from zip into new repo tree

pub mod gate;
pub mod replicate;

pub use gate::{ReplicationGateResult, ReplicationReceipt};
pub use replicate::{replicate_local, replicate_rootball, replicate_zip2repo_v1};
