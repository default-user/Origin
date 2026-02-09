//! Receipts: audit trail for pack/verify/unfurl operations.

use serde::{Deserialize, Serialize};

/// Status of a single gate check.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum GateStatus {
    Pass,
    Fail,
    Skip,
}

/// Result of a single gate check.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GateResult {
    pub gate: String,
    pub status: GateStatus,
    pub detail: String,
}

/// Audit receipt emitted after pack/verify/unfurl/audit operations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuditReceipt {
    /// Operation that produced this receipt.
    pub operation: String,
    /// ISO 8601 timestamp.
    pub timestamp: String,
    /// Root 2I seed fingerprint bound to this operation.
    pub root_2i_seed_fingerprint: String,
    /// Pack hash (if applicable).
    pub pack_hash: Option<String>,
    /// Gate results.
    pub gates: Vec<GateResult>,
    /// Overall pass/fail.
    pub passed: bool,
}

impl AuditReceipt {
    /// Create a new receipt, computing `passed` from gate results.
    pub fn new(
        operation: &str,
        root_2i_seed_fingerprint: &str,
        pack_hash: Option<&str>,
        gates: Vec<GateResult>,
    ) -> Self {
        let passed = gates.iter().all(|g| g.status != GateStatus::Fail);
        let timestamp = chrono::Utc::now().to_rfc3339();
        Self {
            operation: operation.to_string(),
            timestamp,
            root_2i_seed_fingerprint: root_2i_seed_fingerprint.to_string(),
            pack_hash: pack_hash.map(|s| s.to_string()),
            gates,
            passed,
        }
    }

    /// Serialize to JSON.
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
}

/// Receipt for changes made outside UTILITIES_ROOT (DPACK/REPLICATION integration only).
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IntegrationExceptionReceipt {
    pub path: String,
    pub change_type: String,
    pub why_required_for_dpack_or_replication: String,
    pub risk: String,
    pub rollback_steps: Vec<String>,
    pub root_2i_seed_fingerprint: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_receipt_all_pass() {
        let gates = vec![
            GateResult {
                gate: "G0_SCHEMA".to_string(),
                status: GateStatus::Pass,
                detail: "schema valid".to_string(),
            },
            GateResult {
                gate: "G1_INTEGRITY".to_string(),
                status: GateStatus::Pass,
                detail: "hashes match".to_string(),
            },
        ];
        let receipt = AuditReceipt::new("verify", "fp123", Some("ph456"), gates);
        assert!(receipt.passed);
    }

    #[test]
    fn test_receipt_one_fail() {
        let gates = vec![
            GateResult {
                gate: "G0_SCHEMA".to_string(),
                status: GateStatus::Pass,
                detail: "ok".to_string(),
            },
            GateResult {
                gate: "G4_SEED_BINDING".to_string(),
                status: GateStatus::Fail,
                detail: "fingerprint mismatch".to_string(),
            },
        ];
        let receipt = AuditReceipt::new("verify", "fp123", None, gates);
        assert!(!receipt.passed);
    }

    #[test]
    fn test_receipt_to_json() {
        let gates = vec![GateResult {
            gate: "G0_SCHEMA".to_string(),
            status: GateStatus::Pass,
            detail: "ok".to_string(),
        }];
        let receipt = AuditReceipt::new("pack", "fp123", Some("ph"), gates);
        let json = receipt.to_json().unwrap();
        assert!(json.contains("\"operation\": \"pack\""));
        assert!(json.contains("\"root_2i_seed_fingerprint\": \"fp123\""));
    }
}
