//! dpack_core: Deterministic pack/verify/unfurl/audit for the Origin orgasystem.
//!
//! A DPACK is a snapshot envelope that captures file paths, content hashes,
//! and seed binding. It preserves paths verbatim and restores identical shape.

pub mod manifest;
pub mod pack;
pub mod policy;
pub mod receipt;

pub use manifest::{DpackManifest, FileEntry};
pub use pack::{pack_repo, unfurl_pack, verify_pack};
pub use policy::Policy;
pub use receipt::{AuditReceipt, GateResult, GateStatus};
