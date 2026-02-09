//! seed_core: Load, fingerprint (SHA-256), and verify the Denotum 2I seed.
//!
//! The seed is the root identity of the Origin orgasystem. Every artifact
//! (pack, manifest, receipt) must bind to the seed fingerprint. If the
//! fingerprint is absent or mismatched, operations FAIL CLOSED.

use sha2::{Digest, Sha256};
use std::path::{Path, PathBuf};
use thiserror::Error;

/// Default relative path from the workspace root to the canonical seed file.
pub const SEED_RELATIVE_PATH: &str = "spec/seed/denotum.seed.2i.yaml";

#[derive(Error, Debug)]
pub enum SeedError {
    #[error("seed file not found at {path}")]
    NotFound { path: PathBuf },
    #[error("I/O error reading seed: {0}")]
    Io(#[from] std::io::Error),
    #[error("seed fingerprint mismatch: expected {expected}, got {actual}")]
    FingerprintMismatch { expected: String, actual: String },
    #[error("seed fingerprint missing in artifact")]
    FingerprintMissing,
}

/// A loaded seed with its raw bytes and computed fingerprint.
#[derive(Debug, Clone)]
pub struct Seed {
    /// Raw bytes of the seed file.
    pub bytes: Vec<u8>,
    /// SHA-256 hex fingerprint of the seed bytes.
    pub fingerprint: String,
    /// Path from which the seed was loaded.
    pub source_path: PathBuf,
}

impl Seed {
    /// Load a seed from the given file path.
    pub fn load(path: &Path) -> Result<Self, SeedError> {
        if !path.exists() {
            return Err(SeedError::NotFound {
                path: path.to_path_buf(),
            });
        }
        let bytes = std::fs::read(path)?;
        let fingerprint = compute_sha256(&bytes);
        Ok(Self {
            bytes,
            fingerprint,
            source_path: path.to_path_buf(),
        })
    }

    /// Load the seed from the canonical location relative to a workspace root.
    pub fn load_from_workspace(workspace_root: &Path) -> Result<Self, SeedError> {
        let path = workspace_root.join(SEED_RELATIVE_PATH);
        Self::load(&path)
    }

    /// Verify that a given fingerprint matches this seed's fingerprint.
    pub fn verify_fingerprint(&self, expected: &str) -> Result<(), SeedError> {
        if self.fingerprint != expected {
            return Err(SeedError::FingerprintMismatch {
                expected: expected.to_string(),
                actual: self.fingerprint.clone(),
            });
        }
        Ok(())
    }

    /// Assert that a fingerprint string is non-empty and matches this seed.
    pub fn assert_binding(&self, fingerprint: Option<&str>) -> Result<(), SeedError> {
        match fingerprint {
            None => Err(SeedError::FingerprintMissing),
            Some("") => Err(SeedError::FingerprintMissing),
            Some(fp) => self.verify_fingerprint(fp),
        }
    }
}

/// Compute SHA-256 hex digest of arbitrary bytes.
pub fn compute_sha256(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

/// Compute SHA-256 hex digest of a file.
pub fn file_sha256(path: &Path) -> Result<String, SeedError> {
    let bytes = std::fs::read(path)?;
    Ok(compute_sha256(&bytes))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;
    use tempfile::NamedTempFile;

    #[test]
    fn test_compute_sha256_deterministic() {
        let a = compute_sha256(b"hello world");
        let b = compute_sha256(b"hello world");
        assert_eq!(a, b);
        assert_eq!(a.len(), 64); // 256 bits = 64 hex chars
    }

    #[test]
    fn test_compute_sha256_known_value() {
        // SHA-256("hello world") is well-known
        let hash = compute_sha256(b"hello world");
        assert_eq!(
            hash,
            "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        );
    }

    #[test]
    fn test_seed_load() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"test seed content").unwrap();
        tmp.flush().unwrap();

        let seed = Seed::load(tmp.path()).unwrap();
        assert_eq!(seed.bytes, b"test seed content");
        assert!(!seed.fingerprint.is_empty());
        assert_eq!(seed.fingerprint.len(), 64);
    }

    #[test]
    fn test_seed_not_found() {
        let result = Seed::load(Path::new("/nonexistent/path/seed.yaml"));
        assert!(result.is_err());
        match result.unwrap_err() {
            SeedError::NotFound { .. } => {}
            other => panic!("expected NotFound, got: {other}"),
        }
    }

    #[test]
    fn test_seed_verify_fingerprint_match() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"content").unwrap();
        tmp.flush().unwrap();

        let seed = Seed::load(tmp.path()).unwrap();
        let fp = seed.fingerprint.clone();
        seed.verify_fingerprint(&fp).unwrap();
    }

    #[test]
    fn test_seed_verify_fingerprint_mismatch() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"content").unwrap();
        tmp.flush().unwrap();

        let seed = Seed::load(tmp.path()).unwrap();
        let result = seed.verify_fingerprint("0000000000000000000000000000000000000000000000000000000000000000");
        assert!(result.is_err());
    }

    #[test]
    fn test_seed_assert_binding_missing() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"content").unwrap();
        tmp.flush().unwrap();

        let seed = Seed::load(tmp.path()).unwrap();
        assert!(seed.assert_binding(None).is_err());
        assert!(seed.assert_binding(Some("")).is_err());
    }

    #[test]
    fn test_seed_assert_binding_ok() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"content").unwrap();
        tmp.flush().unwrap();

        let seed = Seed::load(tmp.path()).unwrap();
        let fp = seed.fingerprint.clone();
        seed.assert_binding(Some(&fp)).unwrap();
    }

    #[test]
    fn test_file_sha256() {
        let mut tmp = NamedTempFile::new().unwrap();
        tmp.write_all(b"file content for hash").unwrap();
        tmp.flush().unwrap();

        let hash = file_sha256(tmp.path()).unwrap();
        let expected = compute_sha256(b"file content for hash");
        assert_eq!(hash, expected);
    }

    #[test]
    fn test_seed_load_from_workspace() {
        let dir = tempfile::tempdir().unwrap();
        let seed_dir = dir.path().join("spec/seed");
        std::fs::create_dir_all(&seed_dir).unwrap();
        std::fs::write(seed_dir.join("denotum.seed.2i.yaml"), b"workspace seed").unwrap();

        let seed = Seed::load_from_workspace(dir.path()).unwrap();
        assert_eq!(seed.bytes, b"workspace seed");
    }
}
