//! Command implementations for originctl.

use compress::{compress_dpack, decompress_cpack};
use dpack_core::pack::{pack_repo, unfurl_pack, verify_pack};
use dpack_core::policy::Policy;
use replication_core::replicate::{replicate_local, replicate_rootball, replicate_zip2repo_v1};
use seed_core::Seed;
use std::path::Path;

type Result<T> = std::result::Result<T, anyhow::Error>;

fn load_seed(seed_path: Option<&Path>, repo_root: Option<&Path>) -> Result<Seed> {
    if let Some(path) = seed_path {
        Ok(Seed::load(path)?)
    } else if let Some(root) = repo_root {
        Ok(Seed::load_from_workspace(root)?)
    } else {
        anyhow::bail!("no seed path provided and no repo root to search")
    }
}

fn load_policy(policy_path: Option<&Path>) -> Result<Option<Policy>> {
    match policy_path {
        Some(p) => Ok(Some(Policy::load(p)?)),
        None => Ok(None),
    }
}

pub fn run_pack(
    repo_root: &Path,
    output: &Path,
    policy_path: Option<&Path>,
    seed_path: Option<&Path>,
) -> Result<()> {
    let seed = load_seed(seed_path, Some(repo_root))?;
    let policy = load_policy(policy_path)?;

    eprintln!("Packing {} -> {}", repo_root.display(), output.display());
    eprintln!("Seed fingerprint: {}", seed.fingerprint);

    let receipt = pack_repo(repo_root, output, &seed, policy.as_ref())?;

    if receipt.passed {
        println!("PASS: pack complete");
        println!("  pack_hash: {}", receipt.pack_hash.unwrap_or_default());
        println!("  seed_fp:   {}", receipt.root_2i_seed_fingerprint);
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    } else {
        eprintln!("FAIL: pack gates did not all pass");
        for g in &receipt.gates {
            eprintln!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
        anyhow::bail!("pack failed");
    }
    Ok(())
}

pub fn run_compress(dpack_dir: &Path, output: &Path) -> Result<()> {
    eprintln!(
        "Compressing {} -> {}",
        dpack_dir.display(),
        output.display()
    );

    let payload_hash = compress_dpack(dpack_dir, output)?;
    println!("PASS: compress complete");
    println!("  payload_sha256: {}", payload_hash);
    println!("  output: {}", output.display());

    let meta = std::fs::metadata(output)?;
    println!("  size: {} bytes", meta.len());
    Ok(())
}

pub fn run_decompress(cpack_path: &Path, output_dir: &Path) -> Result<()> {
    eprintln!(
        "Decompressing {} -> {}",
        cpack_path.display(),
        output_dir.display()
    );

    let payload_hash = decompress_cpack(cpack_path, output_dir)?;
    println!("PASS: decompress complete");
    println!("  payload_sha256: {}", payload_hash);
    println!("  output: {}", output_dir.display());
    Ok(())
}

pub fn run_verify(path: &Path, seed_path: Option<&Path>) -> Result<()> {
    // Detect whether this is a cpack file or dpack directory
    if path.is_file() {
        // Assume .cpack file: decompress to temp, then verify
        eprintln!("Verifying CPACK file: {}", path.display());
        let tmp = tempfile::tempdir()?;
        let payload_hash = decompress_cpack(path, tmp.path())?;
        println!("PASS: CPACK integrity verified");
        println!("  payload_sha256: {}", payload_hash);

        // Also verify the contained dpack if seed is provided
        if seed_path.is_some()
            || tmp
                .path()
                .join("data/spec/seed/denotum.seed.2i.yaml")
                .exists()
        {
            let seed = if let Some(sp) = seed_path {
                Seed::load(sp)?
            } else {
                Seed::load(&tmp.path().join("data/spec/seed/denotum.seed.2i.yaml"))?
            };
            let receipt = verify_pack(tmp.path(), &seed)?;
            if receipt.passed {
                println!("PASS: contained DPACK verification complete");
            } else {
                println!("FAIL: contained DPACK verification failed");
            }
            for g in &receipt.gates {
                println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
            }
            if !receipt.passed {
                anyhow::bail!("verification failed");
            }
        }
    } else {
        // DPACK directory
        eprintln!("Verifying DPACK at {}", path.display());
        let seed = if let Some(sp) = seed_path {
            Seed::load(sp)?
        } else {
            let candidate = path.join("data/spec/seed/denotum.seed.2i.yaml");
            if candidate.exists() {
                Seed::load(&candidate)?
            } else {
                anyhow::bail!("no seed path provided; use --seed or ensure seed is in pack data")
            }
        };

        let receipt = verify_pack(path, &seed)?;
        if receipt.passed {
            println!("PASS: verification complete");
        } else {
            println!("FAIL: verification failed");
        }
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
        if !receipt.passed {
            anyhow::bail!("verification failed");
        }
    }
    Ok(())
}

pub fn run_unfurl(pack_dir: &Path, output: &Path, seed_path: Option<&Path>) -> Result<()> {
    let seed = if let Some(sp) = seed_path {
        Seed::load(sp)?
    } else {
        let candidate = pack_dir.join("data/spec/seed/denotum.seed.2i.yaml");
        if candidate.exists() {
            Seed::load(&candidate)?
        } else {
            anyhow::bail!("no seed path provided; use --seed or ensure seed is in pack data")
        }
    };

    eprintln!("Unfurling {} -> {}", pack_dir.display(), output.display());

    let receipt = unfurl_pack(pack_dir, output, &seed)?;

    if receipt.passed {
        println!("PASS: unfurl complete");
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    } else {
        eprintln!("FAIL: unfurl failed");
        anyhow::bail!("unfurl failed");
    }
    Ok(())
}

pub fn run_audit(pack_dir: &Path, json: bool, seed_path: Option<&Path>) -> Result<()> {
    let seed = if let Some(sp) = seed_path {
        Seed::load(sp)?
    } else {
        let candidate = pack_dir.join("data/spec/seed/denotum.seed.2i.yaml");
        if candidate.exists() {
            Seed::load(&candidate)?
        } else {
            anyhow::bail!("no seed path provided; use --seed or ensure seed is in pack data")
        }
    };

    let receipt = verify_pack(pack_dir, &seed)?;

    if json {
        println!("{}", receipt.to_json()?);
    } else {
        println!("Audit of {}", pack_dir.display());
        println!("  operation: {}", receipt.operation);
        println!("  seed_fp:   {}", receipt.root_2i_seed_fingerprint);
        println!(
            "  pack_hash: {}",
            receipt.pack_hash.as_deref().unwrap_or("N/A")
        );
        println!("  passed:    {}", receipt.passed);
        println!("  gates:");
        for g in &receipt.gates {
            println!("    [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    }

    if !receipt.passed {
        anyhow::bail!("audit found failures");
    }
    Ok(())
}

pub fn run_replicate_local(
    repo_root: &Path,
    output: &Path,
    policy_path: Option<&Path>,
    seed_path: Option<&Path>,
) -> Result<()> {
    let seed = load_seed(seed_path, Some(repo_root))?;
    let policy = load_policy(policy_path)?;

    eprintln!(
        "Replicating (local) {} -> {}",
        repo_root.display(),
        output.display()
    );

    let receipt = replicate_local(repo_root, output, &seed, policy.as_ref())?;

    if receipt.passed {
        println!("PASS: local replication complete");
        println!(
            "  source_pack_hash: {}",
            receipt.source_pack_hash.unwrap_or_default()
        );
        println!(
            "  target_pack_hash: {}",
            receipt.target_pack_hash.unwrap_or_default()
        );
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    } else {
        eprintln!("FAIL: replication failed");
        anyhow::bail!("replication failed");
    }
    Ok(())
}

pub fn run_replicate_rootball(
    repo_root: &Path,
    output: &Path,
    policy_path: Option<&Path>,
    seed_path: Option<&Path>,
) -> Result<()> {
    let seed = load_seed(seed_path, Some(repo_root))?;
    let policy = load_policy(policy_path)?;

    eprintln!(
        "Creating rootball {} -> {}",
        repo_root.display(),
        output.display()
    );

    let receipt = replicate_rootball(repo_root, output, &seed, policy.as_ref())?;

    if receipt.passed {
        println!("PASS: rootball created");
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    } else {
        eprintln!("FAIL: rootball creation failed");
        anyhow::bail!("rootball creation failed");
    }
    Ok(())
}

pub fn run_replicate_zip2repo_v1(
    source: &Path,
    out_dir: &Path,
    init_git: bool,
    policy_path: Option<&Path>,
    seed_path: Option<&Path>,
) -> Result<()> {
    let seed = load_seed(seed_path, Some(source))?;
    let policy = load_policy(policy_path)?;

    eprintln!(
        "Replicating (zip2repo_v1) {} -> {}",
        source.display(),
        out_dir.display()
    );

    let receipt = replicate_zip2repo_v1(source, out_dir, &seed, init_git, policy.as_ref())?;

    if receipt.passed {
        println!("PASS: zip2repo_v1 replication complete");
        for g in &receipt.gates {
            println!("  [{}] {:?}: {}", g.gate, g.status, g.detail);
        }
    } else {
        eprintln!("FAIL: replication failed");
        anyhow::bail!("replication failed");
    }
    Ok(())
}

/// End-to-end pipeline: pack -> compress -> decompress -> verify round-trip.
pub fn run_e2e(
    repo_root: &Path,
    seed_path: Option<&Path>,
    policy_path: Option<&Path>,
) -> Result<()> {
    let seed = load_seed(seed_path, Some(repo_root))?;
    let policy = load_policy(policy_path)?;

    println!("=== ORIGIN E2E PIPELINE ===");
    println!();

    // Step 1: Pack
    println!("[1/6] Packing repository...");
    let dpack_dir = tempfile::tempdir()?;
    let pack_receipt = pack_repo(repo_root, dpack_dir.path(), &seed, policy.as_ref())?;
    if !pack_receipt.passed {
        anyhow::bail!("E2E FAIL at step 1 (pack): gates did not pass");
    }
    let pack_hash = pack_receipt.pack_hash.clone().unwrap_or_default();
    println!("  PASS: {} files packed", pack_receipt.gates.len());
    println!("  pack_hash: {}", &pack_hash[..16]);

    // Step 2: Compress
    println!("[2/6] Compressing to CPACK...");
    let cpack_dir = tempfile::tempdir()?;
    let cpack_path = cpack_dir.path().join("origin.cpack");
    let payload_hash = compress_dpack(dpack_dir.path(), &cpack_path)?;
    let cpack_size = std::fs::metadata(&cpack_path)?.len();
    println!("  PASS: compressed to {} bytes", cpack_size);
    println!("  payload_sha256: {}", &payload_hash[..16]);

    // Step 3: Decompress
    println!("[3/6] Decompressing CPACK...");
    let restored_dir = tempfile::tempdir()?;
    let restored_hash = decompress_cpack(&cpack_path, restored_dir.path())?;
    println!("  PASS: decompressed");
    assert_eq!(
        payload_hash, restored_hash,
        "payload hash mismatch after decompress"
    );
    println!("  payload_sha256 matches: YES");

    // Step 4: Verify restored dpack
    println!("[4/6] Verifying restored DPACK...");
    let verify_receipt = verify_pack(restored_dir.path(), &seed)?;
    if !verify_receipt.passed {
        anyhow::bail!("E2E FAIL at step 4 (verify): restored dpack verification failed");
    }
    println!("  PASS: all gates passed");
    for g in &verify_receipt.gates {
        println!("    [{}] {:?}", g.gate, g.status);
    }

    // Step 5: Round-trip integrity check (compare pack hashes)
    println!("[5/6] Checking round-trip integrity...");
    let restored_manifest_bytes = std::fs::read(restored_dir.path().join("manifest.json"))?;
    let restored_manifest: dpack_core::DpackManifest =
        serde_json::from_slice(&restored_manifest_bytes)?;
    if restored_manifest.pack_hash != pack_hash {
        anyhow::bail!(
            "E2E FAIL at step 5: pack_hash mismatch (orig={}, restored={})",
            &pack_hash[..16],
            &restored_manifest.pack_hash[..16]
        );
    }
    println!("  PASS: pack_hash matches original");

    // Step 6: Compress determinism check
    println!("[6/6] Checking compress determinism...");
    let cpack2_dir = tempfile::tempdir()?;
    let cpack2_path = cpack2_dir.path().join("origin2.cpack");
    let payload_hash2 = compress_dpack(dpack_dir.path(), &cpack2_path)?;
    let cpack1_bytes = std::fs::read(&cpack_path)?;
    let cpack2_bytes = std::fs::read(&cpack2_path)?;
    if cpack1_bytes != cpack2_bytes {
        anyhow::bail!("E2E FAIL at step 6: compress is not deterministic");
    }
    assert_eq!(payload_hash, payload_hash2);
    println!("  PASS: compress is deterministic (byte-identical)");

    println!();
    println!("=== E2E PIPELINE PASSED ===");
    println!("  pack_hash:       {}", pack_hash);
    println!("  payload_sha256:  {}", payload_hash);
    println!("  cpack_size:      {} bytes", cpack_size);
    println!("  round_trip:      VERIFIED");
    println!("  determinism:     VERIFIED");
    Ok(())
}
