//! Proptest round-trip invariants:
//! decompress(compress(x)) == x for random content.

use dpack_core::manifest::{DpackManifest, FileEntry};
use proptest::prelude::*;
use seed_core::compute_sha256;
use std::collections::BTreeMap;
use tempfile::TempDir;

/// Create a synthetic dpack directory from given file entries.
fn make_synthetic_dpack(dir: &std::path::Path, files: &[(String, Vec<u8>)], seed_fp: &str) {
    let data_dir = dir.join("data");
    std::fs::create_dir_all(&data_dir).unwrap();

    let mut manifest_files = BTreeMap::new();
    for (rel_path, content) in files {
        let dest = data_dir.join(rel_path);
        if let Some(parent) = dest.parent() {
            std::fs::create_dir_all(parent).unwrap();
        }
        std::fs::write(&dest, content).unwrap();
        manifest_files.insert(
            rel_path.clone(),
            FileEntry {
                sha256: compute_sha256(content),
                size: content.len() as u64,
            },
        );
    }

    let pack_hash = DpackManifest::compute_pack_hash(&manifest_files);
    let manifest = DpackManifest {
        schema_version: "1.0".to_string(),
        root_2i_seed_fingerprint: seed_fp.to_string(),
        created_at: "2026-01-01T00:00:00Z".to_string(),
        source_root: "/synthetic".to_string(),
        files: manifest_files,
        pack_hash,
    };
    let json = serde_json::to_string_pretty(&manifest).unwrap();
    std::fs::write(dir.join("manifest.json"), json).unwrap();
}

/// Generate a valid file path component (no slashes, no dots prefix, ASCII alphanumeric).
fn arb_filename() -> impl Strategy<Value = String> {
    "[a-z][a-z0-9]{0,7}\\.[a-z]{1,3}"
}

/// Generate a random file tree: 1-5 files with random content.
fn arb_file_tree() -> impl Strategy<Value = Vec<(String, Vec<u8>)>> {
    prop::collection::vec(
        (arb_filename(), prop::collection::vec(any::<u8>(), 0..256)),
        1..6,
    )
    .prop_map(|entries| {
        // Deduplicate filenames
        let mut seen = std::collections::BTreeSet::new();
        entries
            .into_iter()
            .filter(|(name, _)| seen.insert(name.clone()))
            .collect()
    })
}

proptest! {
    #![proptest_config(ProptestConfig::with_cases(100))]

    /// Round-trip: decompress(compress(dpack)) must restore identical manifest and files.
    #[test]
    fn roundtrip_compress_decompress(files in arb_file_tree()) {
        let dpack = TempDir::new().unwrap();
        let seed_fp = "proptest_seed_fingerprint_stable";
        make_synthetic_dpack(dpack.path(), &files, seed_fp);

        // Compress
        let cpack_dir = TempDir::new().unwrap();
        let cpack_path = cpack_dir.path().join("test.cpack");
        let hash1 = compress::compress_dpack(dpack.path(), &cpack_path).unwrap();

        // Decompress
        let restored = TempDir::new().unwrap();
        let hash2 = compress::decompress_cpack(&cpack_path, restored.path()).unwrap();

        // Hashes must match
        prop_assert_eq!(&hash1, &hash2, "payload hash mismatch");

        // Manifest must match
        let orig_bytes = std::fs::read(dpack.path().join("manifest.json")).unwrap();
        let rest_bytes = std::fs::read(restored.path().join("manifest.json")).unwrap();
        let orig: DpackManifest = serde_json::from_slice(&orig_bytes).unwrap();
        let rest: DpackManifest = serde_json::from_slice(&rest_bytes).unwrap();
        prop_assert_eq!(&orig.pack_hash, &rest.pack_hash);
        prop_assert_eq!(&orig.files, &rest.files);

        // Data files must match
        for (rel_path, content) in &files {
            let restored_content = std::fs::read(restored.path().join("data").join(rel_path)).unwrap();
            prop_assert_eq!(content, &restored_content, "file content mismatch: {}", rel_path);
        }
    }

    /// Determinism: compress(x) twice must produce identical bytes.
    #[test]
    fn compress_deterministic(files in arb_file_tree()) {
        let dpack = TempDir::new().unwrap();
        make_synthetic_dpack(dpack.path(), &files, "determinism_test");

        let cp1 = TempDir::new().unwrap();
        let cp2 = TempDir::new().unwrap();
        let p1 = cp1.path().join("a.cpack");
        let p2 = cp2.path().join("b.cpack");

        compress::compress_dpack(dpack.path(), &p1).unwrap();
        compress::compress_dpack(dpack.path(), &p2).unwrap();

        let d1 = std::fs::read(&p1).unwrap();
        let d2 = std::fs::read(&p2).unwrap();
        prop_assert_eq!(d1, d2, "compress not deterministic");
    }

    /// Frame round-trip: encode then decode must return identical data.
    #[test]
    fn frame_payload_roundtrip(
        manifest in prop::collection::vec(any::<u8>(), 1..200),
        files in prop::collection::vec(
            ("[a-z]{1,8}".prop_map(|s| s), prop::collection::vec(any::<u8>(), 0..100)),
            0..5
        )
    ) {
        let sorted: Vec<(String, Vec<u8>)> = {
            let mut m = BTreeMap::new();
            for (k, v) in files {
                m.insert(k, v);
            }
            m.into_iter().collect()
        };

        let encoded = compress::frame::encode_payload(&manifest, &sorted);
        let (dec_manifest, dec_files) = compress::frame::decode_payload(&encoded).unwrap();

        prop_assert_eq!(&manifest, &dec_manifest);
        prop_assert_eq!(&sorted, &dec_files);
    }
}
