//! DPACK manifest: the index of files, hashes, and metadata in a pack.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;

/// A DPACK manifest listing all files in the pack with their hashes.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DpackManifest {
    /// Schema version for the manifest format.
    pub schema_version: String,
    /// SHA-256 fingerprint of the root 2I seed.
    pub root_2i_seed_fingerprint: String,
    /// Timestamp of pack creation (ISO 8601).
    pub created_at: String,
    /// Source repo root path (informational).
    pub source_root: String,
    /// Map of relative path -> file entry.
    pub files: BTreeMap<String, FileEntry>,
    /// SHA-256 of the sorted concatenation of all file hashes (pack integrity).
    pub pack_hash: String,
}

/// A single file entry in the manifest.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct FileEntry {
    /// SHA-256 hash of the file contents.
    pub sha256: String,
    /// File size in bytes.
    pub size: u64,
}

impl DpackManifest {
    /// Compute the pack_hash from the file entries.
    /// This is the SHA-256 of all file hashes sorted by path and concatenated.
    pub fn compute_pack_hash(files: &BTreeMap<String, FileEntry>) -> String {
        use sha2::{Digest, Sha256};
        let mut hasher = Sha256::new();
        // BTreeMap is already sorted by key
        for (path, entry) in files {
            hasher.update(path.as_bytes());
            hasher.update(b":");
            hasher.update(entry.sha256.as_bytes());
            hasher.update(b"\n");
        }
        hex::encode(hasher.finalize())
    }

    /// Verify that the pack_hash matches the file entries.
    pub fn verify_integrity(&self) -> bool {
        let expected = Self::compute_pack_hash(&self.files);
        self.pack_hash == expected
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_pack_hash_deterministic() {
        let mut files = BTreeMap::new();
        files.insert(
            "a.txt".to_string(),
            FileEntry {
                sha256: "aaa".to_string(),
                size: 3,
            },
        );
        files.insert(
            "b.txt".to_string(),
            FileEntry {
                sha256: "bbb".to_string(),
                size: 3,
            },
        );
        let h1 = DpackManifest::compute_pack_hash(&files);
        let h2 = DpackManifest::compute_pack_hash(&files);
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_manifest_verify_integrity() {
        let mut files = BTreeMap::new();
        files.insert(
            "x.rs".to_string(),
            FileEntry {
                sha256: "abc123".to_string(),
                size: 10,
            },
        );
        let pack_hash = DpackManifest::compute_pack_hash(&files);
        let manifest = DpackManifest {
            schema_version: "1.0".to_string(),
            root_2i_seed_fingerprint: "seed_fp".to_string(),
            created_at: "2025-01-01T00:00:00Z".to_string(),
            source_root: "/tmp/test".to_string(),
            files,
            pack_hash,
        };
        assert!(manifest.verify_integrity());
    }

    #[test]
    fn test_manifest_verify_integrity_tampered() {
        let mut files = BTreeMap::new();
        files.insert(
            "x.rs".to_string(),
            FileEntry {
                sha256: "abc123".to_string(),
                size: 10,
            },
        );
        let manifest = DpackManifest {
            schema_version: "1.0".to_string(),
            root_2i_seed_fingerprint: "seed_fp".to_string(),
            created_at: "2025-01-01T00:00:00Z".to_string(),
            source_root: "/tmp/test".to_string(),
            files,
            pack_hash: "wrong_hash".to_string(),
        };
        assert!(!manifest.verify_integrity());
    }
}
