//! Compress a DPACK directory into a single .cpack file.

use crate::frame::{
    encode_payload, sha256_bytes, CpackHeader, FrameError, COMPRESS_ZSTD, CPACK_VERSION,
};
use dpack_core::manifest::DpackManifest;
use std::collections::BTreeMap;
use std::path::Path;
use walkdir::WalkDir;

/// Compress a DPACK directory into a .cpack file.
///
/// The dpack_dir must contain manifest.json and a data/ subdirectory.
/// Output is written to `output_path`.
///
/// Returns the SHA-256 hex string of the uncompressed payload.
pub fn compress_dpack(dpack_dir: &Path, output_path: &Path) -> Result<String, FrameError> {
    // Read manifest
    let manifest_path = dpack_dir.join("manifest.json");
    let manifest_bytes = std::fs::read(&manifest_path)?;

    // Validate manifest parses
    let manifest: DpackManifest = serde_json::from_slice(&manifest_bytes)?;

    // Re-serialize manifest canonically (sorted keys via BTreeMap in struct)
    let canonical_manifest = serde_json::to_vec(&manifest)?;

    // Collect files from data/ directory, sorted by relative path
    let data_dir = dpack_dir.join("data");
    let mut files: BTreeMap<String, Vec<u8>> = BTreeMap::new();

    if data_dir.exists() {
        for entry in WalkDir::new(&data_dir)
            .follow_links(false)
            .sort_by_file_name()
        {
            let entry = entry.map_err(|e| {
                let msg = e.to_string();
                FrameError::Io(
                    e.into_io_error()
                        .unwrap_or_else(|| std::io::Error::other(msg)),
                )
            })?;
            if !entry.file_type().is_file() {
                continue;
            }
            let rel = entry
                .path()
                .strip_prefix(&data_dir)
                .unwrap_or(entry.path())
                .to_string_lossy()
                .replace('\\', "/");
            let content = std::fs::read(entry.path())?;
            files.insert(rel, content);
        }
    }

    // Build sorted file list
    let sorted_files: Vec<(String, Vec<u8>)> = files.into_iter().collect();

    // Encode payload
    let payload = encode_payload(&canonical_manifest, &sorted_files);

    // Hash payload
    let payload_hash = sha256_bytes(&payload);

    // Compress with zstd (level 3 for good ratio/speed balance)
    let compressed = zstd::encode_all(payload.as_slice(), 3)?;

    // Build header
    let header = CpackHeader {
        version: CPACK_VERSION,
        compression_method: COMPRESS_ZSTD,
        payload_sha256: payload_hash,
        compressed_size: compressed.len() as u64,
    };

    // Write output file
    let mut out = header.to_bytes();
    out.extend_from_slice(&compressed);
    std::fs::write(output_path, &out)?;

    Ok(hex::encode(payload_hash))
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    fn make_dpack(dir: &Path) {
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
    fn test_compress_creates_file() {
        let dpack = TempDir::new().unwrap();
        make_dpack(dpack.path());
        let out = TempDir::new().unwrap();
        let cpack_path = out.path().join("test.cpack");

        let hash = compress_dpack(dpack.path(), &cpack_path).unwrap();
        assert!(cpack_path.exists());
        assert_eq!(hash.len(), 64);

        let data = std::fs::read(&cpack_path).unwrap();
        assert!(data.len() > 48); // header + some data
        assert_eq!(&data[0..4], b"CPCK");
    }

    #[test]
    fn test_compress_deterministic() {
        let dpack = TempDir::new().unwrap();
        make_dpack(dpack.path());

        let out1 = TempDir::new().unwrap();
        let out2 = TempDir::new().unwrap();
        let p1 = out1.path().join("a.cpack");
        let p2 = out2.path().join("b.cpack");

        compress_dpack(dpack.path(), &p1).unwrap();
        compress_dpack(dpack.path(), &p2).unwrap();

        let d1 = std::fs::read(&p1).unwrap();
        let d2 = std::fs::read(&p2).unwrap();
        assert_eq!(d1, d2, "compress must be deterministic");
    }
}
