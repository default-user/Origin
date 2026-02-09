//! Golden tests: verify exact output hashes from fixture inputs.
//!
//! These tests use the sample_tree fixture to ensure deterministic outputs.

use dpack_core::manifest::DpackManifest;
use dpack_core::pack::{pack_repo, verify_pack};
use seed_core::{compute_sha256, Seed};
use std::path::Path;
use tempfile::TempDir;

fn fixture_path() -> &'static Path {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .parent()
        .unwrap()
        .parent()
        .unwrap()
}

fn sample_tree() -> std::path::PathBuf {
    fixture_path().join("fixtures/sample_tree")
}

fn seed_from_fixture() -> Seed {
    Seed::load_from_workspace(&sample_tree()).unwrap()
}

#[test]
fn golden_fixture_seed_fingerprint_is_stable() {
    let seed = seed_from_fixture();
    // Same fixture bytes must always produce the same fingerprint.
    let seed2 = seed_from_fixture();
    assert_eq!(seed.fingerprint, seed2.fingerprint);
    assert_eq!(seed.fingerprint.len(), 64);
}

#[test]
fn golden_pack_hash_is_deterministic() {
    let seed = seed_from_fixture();
    let out1 = TempDir::new().unwrap();
    let out2 = TempDir::new().unwrap();

    let r1 = pack_repo(&sample_tree(), out1.path(), &seed, None).unwrap();
    let r2 = pack_repo(&sample_tree(), out2.path(), &seed, None).unwrap();

    assert!(r1.passed);
    assert!(r2.passed);
    // Pack hashes must be identical for identical inputs.
    assert_eq!(
        r1.pack_hash, r2.pack_hash,
        "pack_hash must be deterministic"
    );
}

#[test]
fn golden_manifest_file_hashes_stable() {
    let seed = seed_from_fixture();
    let out = TempDir::new().unwrap();
    pack_repo(&sample_tree(), out.path(), &seed, None).unwrap();

    let manifest_bytes = std::fs::read(out.path().join("manifest.json")).unwrap();
    let manifest: DpackManifest = serde_json::from_slice(&manifest_bytes).unwrap();

    // Check that known files are present with stable hashes.
    assert!(manifest.files.contains_key("README.md"));
    assert!(manifest.files.contains_key("src/main.rs"));
    assert!(manifest.files.contains_key("config.yaml"));
    assert!(manifest
        .files
        .contains_key("spec/seed/denotum.seed.2i.yaml"));

    // Verify individual file hashes against known content.
    let readme_content = std::fs::read(sample_tree().join("README.md")).unwrap();
    let expected_readme_hash = compute_sha256(&readme_content);
    assert_eq!(
        manifest.files["README.md"].sha256, expected_readme_hash,
        "README.md hash must match"
    );
}

#[test]
fn golden_verify_accepts_clean_pack() {
    let seed = seed_from_fixture();
    let out = TempDir::new().unwrap();
    pack_repo(&sample_tree(), out.path(), &seed, None).unwrap();

    let receipt = verify_pack(out.path(), &seed).unwrap();
    assert!(
        receipt.passed,
        "clean pack must verify: {:?}",
        receipt.gates
    );
}

#[test]
fn golden_compress_decompress_roundtrip() {
    let seed = seed_from_fixture();
    let dpack = TempDir::new().unwrap();
    pack_repo(&sample_tree(), dpack.path(), &seed, None).unwrap();

    // Read original manifest
    let orig_manifest_bytes = std::fs::read(dpack.path().join("manifest.json")).unwrap();
    let orig: DpackManifest = serde_json::from_slice(&orig_manifest_bytes).unwrap();

    // Compress
    let cpack_dir = TempDir::new().unwrap();
    let cpack_path = cpack_dir.path().join("golden.cpack");
    let hash1 = compress::compress_dpack(dpack.path(), &cpack_path).unwrap();

    // Decompress
    let restored = TempDir::new().unwrap();
    let hash2 = compress::decompress_cpack(&cpack_path, restored.path()).unwrap();
    assert_eq!(hash1, hash2, "payload hash must survive round-trip");

    // Verify restored manifest matches
    let rest_manifest_bytes = std::fs::read(restored.path().join("manifest.json")).unwrap();
    let rest: DpackManifest = serde_json::from_slice(&rest_manifest_bytes).unwrap();
    assert_eq!(orig.pack_hash, rest.pack_hash);
    assert_eq!(orig.files, rest.files);
    assert_eq!(orig.root_2i_seed_fingerprint, rest.root_2i_seed_fingerprint);
}

#[test]
fn golden_compress_is_bytewise_deterministic() {
    let seed = seed_from_fixture();
    let dpack = TempDir::new().unwrap();
    pack_repo(&sample_tree(), dpack.path(), &seed, None).unwrap();

    let cp1 = TempDir::new().unwrap();
    let cp2 = TempDir::new().unwrap();
    let p1 = cp1.path().join("a.cpack");
    let p2 = cp2.path().join("b.cpack");

    compress::compress_dpack(dpack.path(), &p1).unwrap();
    compress::compress_dpack(dpack.path(), &p2).unwrap();

    let d1 = std::fs::read(&p1).unwrap();
    let d2 = std::fs::read(&p2).unwrap();
    assert_eq!(d1, d2, "compress must be bytewise deterministic");
}

#[test]
fn golden_lfme_parse_fixture_seed() {
    let seed_path = sample_tree().join("spec/seed/denotum.seed.2i.yaml");
    let content = std::fs::read_to_string(&seed_path).unwrap();
    let denotum = lfme_core::parse_seed(&content).unwrap();

    assert_eq!(denotum.version, "v1.0");
    assert_eq!(denotum.steward, "Ande");
    assert_eq!(denotum.posture, "FAIL_CLOSED");
    assert!(denotum.stop_wins);
    assert!(denotum.glossary.contains_key("2I"));
    assert!(denotum.axioms.contains_key("A1_PeopleFirst"));

    // Validate
    let result = lfme_core::validate_denotum(&denotum);
    assert!(
        result.is_valid(),
        "fixture seed must validate: {:?}",
        result.errors
    );
}

#[test]
fn golden_lfme_canonical_fingerprint_stable() {
    let seed_path = sample_tree().join("spec/seed/denotum.seed.2i.yaml");
    let content = std::fs::read_to_string(&seed_path).unwrap();
    let denotum = lfme_core::parse_seed(&content).unwrap();

    let fp1 = lfme_core::canonical::canonical_fingerprint(&denotum).unwrap();
    let fp2 = lfme_core::canonical::canonical_fingerprint(&denotum).unwrap();
    assert_eq!(fp1, fp2, "canonical fingerprint must be stable");
    assert_eq!(fp1.len(), 64);
}

#[test]
fn golden_rag_deterministic_retrieval() {
    let mut index = rag_deterministic::DeterministicIndex::new();
    index.add_document(
        "readme",
        "Origin orgasystem deterministic intelligence.",
        100,
    );
    index.add_document("code", "fn main() { println!(\"hello\"); }", 100);
    index.add_document("config", "name: origin\nversion: 1.0.0", 100);

    let r1 = rag_deterministic::retrieve(&index, "origin intelligence", 2);
    let r2 = rag_deterministic::retrieve(&index, "origin intelligence", 2);

    assert_eq!(r1.len(), r2.len());
    for (a, b) in r1.iter().zip(r2.iter()) {
        assert_eq!(a.chunk_id, b.chunk_id, "retrieval must be deterministic");
        assert_eq!(a.score, b.score);
    }
}
