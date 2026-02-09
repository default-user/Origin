//! Replication gates: checks that must pass before/after replication.

use serde::{Deserialize, Serialize};

/// Status of a replication gate.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub enum RGateStatus {
    Pass,
    Fail,
}

/// Result of a single replication gate check.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplicationGateResult {
    pub gate: String,
    pub status: RGateStatus,
    pub detail: String,
}

/// Replication receipt: emitted after any replication operation.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ReplicationReceipt {
    pub operation: String,
    pub mode: String,
    pub timestamp: String,
    pub root_2i_seed_fingerprint: String,
    pub source_pack_hash: Option<String>,
    pub target_pack_hash: Option<String>,
    pub gates: Vec<ReplicationGateResult>,
    pub passed: bool,
}

impl ReplicationReceipt {
    pub fn new(
        operation: &str,
        mode: &str,
        root_2i_seed_fingerprint: &str,
        source_pack_hash: Option<&str>,
        target_pack_hash: Option<&str>,
        gates: Vec<ReplicationGateResult>,
    ) -> Self {
        let passed = gates.iter().all(|g| g.status != RGateStatus::Fail);
        Self {
            operation: operation.to_string(),
            mode: mode.to_string(),
            timestamp: chrono::Utc::now().to_rfc3339(),
            root_2i_seed_fingerprint: root_2i_seed_fingerprint.to_string(),
            source_pack_hash: source_pack_hash.map(|s| s.to_string()),
            target_pack_hash: target_pack_hash.map(|s| s.to_string()),
            gates,
            passed,
        }
    }

    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string_pretty(self)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_receipt_all_pass() {
        let gates = vec![
            ReplicationGateResult {
                gate: "RG0_POLICY".to_string(),
                status: RGateStatus::Pass,
                detail: "ok".to_string(),
            },
            ReplicationGateResult {
                gate: "RG1_SEED_BINDING".to_string(),
                status: RGateStatus::Pass,
                detail: "ok".to_string(),
            },
        ];
        let receipt = ReplicationReceipt::new(
            "replicate",
            "R0_LOCAL_CLONE",
            "fp",
            Some("src"),
            Some("tgt"),
            gates,
        );
        assert!(receipt.passed);
    }

    #[test]
    fn test_receipt_gate_fail() {
        let gates = vec![ReplicationGateResult {
            gate: "RG2_SHAPE_EQUIVALENCE".to_string(),
            status: RGateStatus::Fail,
            detail: "shape mismatch".to_string(),
        }];
        let receipt =
            ReplicationReceipt::new("replicate", "R0_LOCAL_CLONE", "fp", None, None, gates);
        assert!(!receipt.passed);
    }
}
