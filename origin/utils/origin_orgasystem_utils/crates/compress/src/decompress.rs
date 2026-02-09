//! Decompress a .cpack file back into a DPACK directory.

use crate::frame::{decode_payload, sha256_bytes, CpackHeader, FrameError, HEADER_SIZE};
use std::path::Path;

/// Decompress a .cpack file into a DPACK directory.
///
/// Reconstructs manifest.json and data/ from the compressed payload.
/// Verifies SHA-256 integrity before writing.
pub fn decompress_cpack(cpack_path: &Path, output_dir: &Path) -> Result<String, FrameError> {
    let cpack_data = std::fs::read(cpack_path)?;

    if cpack_data.len() < HEADER_SIZE {
        return Err(FrameError::HeaderTooShort {
            got: cpack_data.len(),
            need: HEADER_SIZE,
        });
    }

    // Parse header
    let header = CpackHeader::from_bytes(&cpack_data)?;

    // Extract compressed data
    let compressed = &cpack_data[HEADER_SIZE..];
    if compressed.len() != header.compressed_size as usize {
        return Err(FrameError::PayloadTruncated);
    }

    // Decompress
    let payload = zstd::decode_all(compressed)?;

    // Verify integrity
    let actual_hash = sha256_bytes(&payload);
    if actual_hash != header.payload_sha256 {
        return Err(FrameError::IntegrityMismatch);
    }

    // Decode payload
    let (manifest_json, files) = decode_payload(&payload)?;

    // Write manifest.json
    std::fs::create_dir_all(output_dir)?;
    std::fs::write(output_dir.join("manifest.json"), &manifest_json)?;

    // Write data files
    let data_dir = output_dir.join("data");
    for (rel_path, content) in &files {
        let dest = data_dir.join(rel_path);
        if let Some(parent) = dest.parent() {
            std::fs::create_dir_all(parent)?;
        }
        std::fs::write(&dest, content)?;
    }

    Ok(hex::encode(actual_hash))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::compress::compress_dpack;
    use tempfile::TempDir;

    fn make_dpack(dir: &std::path::Path) {
        let data_dir = dir.join("data");
        std::fs::create_dir_all(data_dir.join("src")).unwrap();
        std::fs::write(data_dir.join("README.md"), "# Test").unwrap();
        std::fs::write(data_dir.join("src/main.rs"), "fn main() {}").unwrap();

        let mut files = std::collections::BTreeMap::new();
        files.insert(
            "README.md".to_string(),
            dpack_core::manifest::FileEntry {
                sha256: seed_core::compute_sha256(b"# Test"),
                size: 6,
            },
        );
        files.insert(
            "src/main.rs".to_string(),
            dpack_core::manifest::FileEntry {
                sha256: seed_core::compute_sha256(b"fn main() {}"),
                size: 12,
            },
        );
        let pack_hash = dpack_core::manifest::DpackManifest::compute_pack_hash(&files);
        let manifest = dpack_core::manifest::DpackManifest {
            schema_version: "1.0".to_string(),
            root_2i_seed_fingerprint: "test_fp".to_string(),
            created_at: "2026-01-01T00:00:00Z".to_string(),
            source_root: "/tmp/test".to_string(),
            files,
            pack_hash,
        };
        let json = serde_json::to_string_pretty(&manifest).unwrap();
        std::fs::write(dir.join("manifest.json"), json).unwrap();
    }

    #[test]
    fn test_roundtrip_compress_decompress() {
        let dpack = TempDir::new().unwrap();
        make_dpack(dpack.path());

        let cpack_file = TempDir::new().unwrap();
        let cpack_path = cpack_file.path().join("test.cpack");
        compress_dpack(dpack.path(), &cpack_path).unwrap();

        let restored = TempDir::new().unwrap();
        decompress_cpack(&cpack_path, restored.path()).unwrap();

        // Verify manifest exists and matches
        let orig_manifest = std::fs::read(dpack.path().join("manifest.json")).unwrap();
        let rest_manifest = std::fs::read(restored.path().join("manifest.json")).unwrap();
        // Both should parse to same structure (canonical form)
        let orig: dpack_core::manifest::DpackManifest =
            serde_json::from_slice(&orig_manifest).unwrap();
        let rest: dpack_core::manifest::DpackManifest =
            serde_json::from_slice(&rest_manifest).unwrap();
        assert_eq!(orig.pack_hash, rest.pack_hash);
        assert_eq!(orig.files.len(), rest.files.len());

        // Verify data files
        assert_eq!(
            std::fs::read_to_string(restored.path().join("data/README.md")).unwrap(),
            "# Test"
        );
        assert_eq!(
            std::fs::read_to_string(restored.path().join("data/src/main.rs")).unwrap(),
            "fn main() {}"
        );
    }

    #[test]
    fn test_decompress_detects_corruption() {
        let dpack = TempDir::new().unwrap();
        make_dpack(dpack.path());

        let cpack_file = TempDir::new().unwrap();
        let cpack_path = cpack_file.path().join("test.cpack");
        compress_dpack(dpack.path(), &cpack_path).unwrap();

        // Corrupt one byte in the compressed data
        let mut data = std::fs::read(&cpack_path).unwrap();
        if data.len() > 50 {
            data[50] ^= 0xFF;
        }
        std::fs::write(&cpack_path, &data).unwrap();

        let restored = TempDir::new().unwrap();
        let result = decompress_cpack(&cpack_path, restored.path());
        assert!(result.is_err());
    }
}
