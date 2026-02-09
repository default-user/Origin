//! Core replication operations.

use crate::gate::{RGateStatus, ReplicationGateResult, ReplicationReceipt};
use dpack_core::manifest::DpackManifest;
use dpack_core::pack::{pack_repo, unfurl_pack, verify_shape_equivalence, PackError};
use dpack_core::policy::Policy;
use seed_core::Seed;
use std::path::Path;
use thiserror::Error;

#[derive(Error, Debug)]
pub enum ReplicationError {
    #[error("pack error: {0}")]
    Pack(#[from] PackError),
    #[error("seed error: {0}")]
    Seed(#[from] seed_core::SeedError),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
    #[error("replication failed: {reason}")]
    Failed { reason: String },
    #[error("gate failed (fail-closed): {gate}")]
    GateFailed { gate: String },
}

/// R0_LOCAL_CLONE: Pack the repo, then unfurl into a target directory.
/// Verifies shape equivalence post-replication.
pub fn replicate_local(
    repo_root: &Path,
    target_dir: &Path,
    seed: &Seed,
    policy: Option<&Policy>,
) -> Result<ReplicationReceipt, ReplicationError> {
    let mut gates = Vec::new();

    // RG0: Policy
    gates.push(ReplicationGateResult {
        gate: "RG0_POLICY".to_string(),
        status: RGateStatus::Pass,
        detail: "policy applied".to_string(),
    });

    // RG1: Seed binding
    gates.push(ReplicationGateResult {
        gate: "RG1_SEED_BINDING".to_string(),
        status: RGateStatus::Pass,
        detail: format!("seed_fp={}", &seed.fingerprint[..16]),
    });

    // Pack to a temp dir
    let pack_temp = tempfile::tempdir()?;
    let pack_receipt = pack_repo(repo_root, pack_temp.path(), seed, policy)?;
    if !pack_receipt.passed {
        return Err(ReplicationError::GateFailed {
            gate: "pack".to_string(),
        });
    }
    let source_pack_hash = pack_receipt.pack_hash.clone();

    // Unfurl to target
    let unfurl_receipt = unfurl_pack(pack_temp.path(), target_dir, seed)?;
    if !unfurl_receipt.passed {
        return Err(ReplicationError::GateFailed {
            gate: "unfurl".to_string(),
        });
    }

    // RG2: Shape equivalence
    let shape_eq = verify_shape_equivalence(repo_root, target_dir)?;
    gates.push(ReplicationGateResult {
        gate: "RG2_SHAPE_EQUIVALENCE".to_string(),
        status: if shape_eq {
            RGateStatus::Pass
        } else {
            RGateStatus::Fail
        },
        detail: if shape_eq {
            "tree shapes identical".to_string()
        } else {
            "tree shape mismatch".to_string()
        },
    });

    if !shape_eq {
        let receipt = ReplicationReceipt::new(
            "replicate",
            "R0_LOCAL_CLONE",
            &seed.fingerprint,
            source_pack_hash.as_deref(),
            None,
            gates,
        );
        return Err(ReplicationError::Failed {
            reason: receipt.to_json().unwrap_or_default(),
        });
    }

    // RG3: Content equivalence - re-pack the target and compare hashes
    let verify_temp = tempfile::tempdir()?;
    let target_pack_receipt = pack_repo(target_dir, verify_temp.path(), seed, policy)?;
    let target_pack_hash = target_pack_receipt.pack_hash.clone();

    let content_eq = source_pack_hash.as_deref() == target_pack_hash.as_deref();
    gates.push(ReplicationGateResult {
        gate: "RG3_CONTENT_EQUIVALENCE".to_string(),
        status: if content_eq {
            RGateStatus::Pass
        } else {
            RGateStatus::Fail
        },
        detail: if content_eq {
            "content hashes identical".to_string()
        } else {
            "content hash mismatch".to_string()
        },
    });

    // RG5: Receipt
    gates.push(ReplicationGateResult {
        gate: "RG5_RECEIPT".to_string(),
        status: RGateStatus::Pass,
        detail: "replication receipt emitted".to_string(),
    });

    let receipt = ReplicationReceipt::new(
        "replicate",
        "R0_LOCAL_CLONE",
        &seed.fingerprint,
        source_pack_hash.as_deref(),
        target_pack_hash.as_deref(),
        gates,
    );
    let receipt_json = receipt.to_json()?;
    std::fs::write(target_dir.join("replication_receipt.json"), &receipt_json)?;

    Ok(receipt)
}

/// R1_ROOTBALL_SEED: Pack the repo into a DPACK rootball for transport.
/// The rootball is a self-contained pack directory that can be unfurled elsewhere.
pub fn replicate_rootball(
    repo_root: &Path,
    output_dir: &Path,
    seed: &Seed,
    policy: Option<&Policy>,
) -> Result<ReplicationReceipt, ReplicationError> {
    let mut gates = Vec::new();

    // RG0: Policy
    gates.push(ReplicationGateResult {
        gate: "RG0_POLICY".to_string(),
        status: RGateStatus::Pass,
        detail: "policy applied".to_string(),
    });

    // RG1: Seed binding
    gates.push(ReplicationGateResult {
        gate: "RG1_SEED_BINDING".to_string(),
        status: RGateStatus::Pass,
        detail: format!("seed_fp={}", &seed.fingerprint[..16]),
    });

    // Pack
    let pack_receipt = pack_repo(repo_root, output_dir, seed, policy)?;
    if !pack_receipt.passed {
        return Err(ReplicationError::GateFailed {
            gate: "pack".to_string(),
        });
    }

    // RG5: Receipt
    gates.push(ReplicationGateResult {
        gate: "RG5_RECEIPT".to_string(),
        status: RGateStatus::Pass,
        detail: format!("rootball created at {}", output_dir.display()),
    });

    let receipt = ReplicationReceipt::new(
        "replicate",
        "R1_ROOTBALL_SEED",
        &seed.fingerprint,
        pack_receipt.pack_hash.as_deref(),
        None,
        gates,
    );
    let receipt_json = receipt.to_json()?;
    std::fs::write(output_dir.join("replication_receipt.json"), &receipt_json)?;

    Ok(receipt)
}

/// R2_ZIP_TO_FRESH_REPO_V1: Extract a zip and set up as a fresh repo.
/// In v1, no merge with existing history - clean extraction only.
///
/// Note: This is a simplified v1 implementation that works with a directory
/// source (simulating zip extraction). Full zip support would add a zip
/// dependency.
pub fn replicate_zip2repo_v1(
    source_dir: &Path,
    out_dir: &Path,
    seed: &Seed,
    init_git: bool,
    policy: Option<&Policy>,
) -> Result<ReplicationReceipt, ReplicationError> {
    let mut gates = Vec::new();

    // RG0: Policy
    gates.push(ReplicationGateResult {
        gate: "RG0_POLICY".to_string(),
        status: RGateStatus::Pass,
        detail: "policy applied".to_string(),
    });

    // RG1: Seed binding
    gates.push(ReplicationGateResult {
        gate: "RG1_SEED_BINDING".to_string(),
        status: RGateStatus::Pass,
        detail: format!("seed_fp={}", &seed.fingerprint[..16]),
    });

    // Pack source, then unfurl to output
    let pack_temp = tempfile::tempdir()?;
    let pack_receipt = pack_repo(source_dir, pack_temp.path(), seed, policy)?;
    if !pack_receipt.passed {
        return Err(ReplicationError::GateFailed {
            gate: "pack".to_string(),
        });
    }

    let unfurl_receipt = unfurl_pack(pack_temp.path(), out_dir, seed)?;
    if !unfurl_receipt.passed {
        return Err(ReplicationError::GateFailed {
            gate: "unfurl".to_string(),
        });
    }

    // Shape equivalence
    let shape_eq = verify_shape_equivalence(source_dir, out_dir)?;
    gates.push(ReplicationGateResult {
        gate: "RG2_SHAPE_EQUIVALENCE".to_string(),
        status: if shape_eq {
            RGateStatus::Pass
        } else {
            RGateStatus::Fail
        },
        detail: if shape_eq {
            "shape preserved".to_string()
        } else {
            "shape mismatch".to_string()
        },
    });

    if !shape_eq {
        let receipt = ReplicationReceipt::new(
            "replicate",
            "R2_ZIP_TO_FRESH_REPO_V1",
            &seed.fingerprint,
            pack_receipt.pack_hash.as_deref(),
            None,
            gates,
        );
        return Err(ReplicationError::Failed {
            reason: receipt.to_json().unwrap_or_default(),
        });
    }

    // Init git if requested
    if init_git {
        let git_dir = out_dir.join(".git");
        if !git_dir.exists() {
            // Create minimal git init marker (actual git init would require git binary)
            std::fs::create_dir_all(&git_dir)?;
            std::fs::write(git_dir.join("HEAD"), "ref: refs/heads/main\n")?;
            std::fs::create_dir_all(git_dir.join("refs/heads"))?;
        }
    }

    // RG5: Receipt
    gates.push(ReplicationGateResult {
        gate: "RG5_RECEIPT".to_string(),
        status: RGateStatus::Pass,
        detail: "replication receipt emitted".to_string(),
    });

    let receipt = ReplicationReceipt::new(
        "replicate",
        "R2_ZIP_TO_FRESH_REPO_V1",
        &seed.fingerprint,
        pack_receipt.pack_hash.as_deref(),
        None,
        gates,
    );
    let receipt_json = receipt.to_json()?;
    std::fs::write(out_dir.join("replication_receipt.json"), &receipt_json)?;

    Ok(receipt)
}

/// Read a manifest from a pack directory.
pub fn read_manifest(pack_dir: &Path) -> Result<DpackManifest, ReplicationError> {
    let manifest_str = std::fs::read_to_string(pack_dir.join("manifest.json"))?;
    let manifest: DpackManifest = serde_json::from_str(&manifest_str)?;
    Ok(manifest)
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn make_test_repo(dir: &Path) -> Seed {
        std::fs::create_dir_all(dir.join("src")).unwrap();
        std::fs::write(dir.join("README.md"), "# Test").unwrap();
        std::fs::write(dir.join("src/main.rs"), "fn main() {}").unwrap();
        let seed_dir = dir.join("spec/seed");
        std::fs::create_dir_all(&seed_dir).unwrap();
        std::fs::write(seed_dir.join("denotum.seed.2i.yaml"), "test seed").unwrap();
        Seed::load_from_workspace(dir).unwrap()
    }

    #[test]
    fn test_replicate_local() {
        let repo = TempDir::new().unwrap();
        let target = TempDir::new().unwrap();
        let seed = make_test_repo(repo.path());

        let receipt = replicate_local(repo.path(), target.path(), &seed, None).unwrap();
        assert!(receipt.passed);
        assert_eq!(receipt.mode, "R0_LOCAL_CLONE");

        // Verify the target has the same files
        assert!(target.path().join("README.md").exists());
        assert!(target.path().join("src/main.rs").exists());

        // Shape equivalence is verified internally by the RG2 gate.
        // After replication, target also contains replication_receipt.json,
        // so a raw shape comparison would differ by that one file.
        assert!(target.path().join("replication_receipt.json").exists());
    }

    #[test]
    fn test_replicate_rootball() {
        let repo = TempDir::new().unwrap();
        let rootball = TempDir::new().unwrap();
        let seed = make_test_repo(repo.path());

        let receipt = replicate_rootball(repo.path(), rootball.path(), &seed, None).unwrap();
        assert!(receipt.passed);
        assert_eq!(receipt.mode, "R1_ROOTBALL_SEED");
        assert!(rootball.path().join("manifest.json").exists());
        assert!(rootball.path().join("data").exists());
    }

    #[test]
    fn test_replicate_zip2repo_v1() {
        let source = TempDir::new().unwrap();
        let out = TempDir::new().unwrap();
        let seed = make_test_repo(source.path());

        let receipt = replicate_zip2repo_v1(source.path(), out.path(), &seed, false, None).unwrap();
        assert!(receipt.passed);
        assert_eq!(receipt.mode, "R2_ZIP_TO_FRESH_REPO_V1");
        assert!(out.path().join("README.md").exists());
    }

    #[test]
    fn test_replicate_zip2repo_v1_with_git_init() {
        let source = TempDir::new().unwrap();
        let out = TempDir::new().unwrap();
        let seed = make_test_repo(source.path());

        let receipt = replicate_zip2repo_v1(source.path(), out.path(), &seed, true, None).unwrap();
        assert!(receipt.passed);
        assert!(out.path().join(".git/HEAD").exists());
    }

    #[test]
    fn test_replicate_local_preserves_seed_binding() {
        let repo = TempDir::new().unwrap();
        let target = TempDir::new().unwrap();
        let seed = make_test_repo(repo.path());

        let receipt = replicate_local(repo.path(), target.path(), &seed, None).unwrap();
        assert_eq!(receipt.root_2i_seed_fingerprint, seed.fingerprint);
    }

    #[test]
    fn test_replicate_local_content_equivalence() {
        let repo = TempDir::new().unwrap();
        let target = TempDir::new().unwrap();
        let seed = make_test_repo(repo.path());

        let receipt = replicate_local(repo.path(), target.path(), &seed, None).unwrap();

        // Check that source and target pack hashes match
        assert!(receipt.source_pack_hash.is_some());
        assert!(receipt.target_pack_hash.is_some());
        assert_eq!(receipt.source_pack_hash, receipt.target_pack_hash);
    }
}
