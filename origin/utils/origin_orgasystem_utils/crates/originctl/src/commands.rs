//! Command implementations for originctl.

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

pub fn run_verify(pack_dir: &Path, seed_path: Option<&Path>) -> Result<()> {
    // Try to find seed from the manifest's source_root or require explicit path
    let seed = if let Some(sp) = seed_path {
        Seed::load(sp)?
    } else {
        // Try to find it in the pack data
        let candidate = pack_dir.join("data/spec/seed/denotum.seed.2i.yaml");
        if candidate.exists() {
            Seed::load(&candidate)?
        } else {
            anyhow::bail!("no seed path provided; use --seed or ensure seed is in pack data")
        }
    };

    eprintln!("Verifying pack at {}", pack_dir.display());

    let receipt = verify_pack(pack_dir, &seed)?;

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
    Ok(())
}

pub fn run_unfurl(
    pack_dir: &Path,
    output: &Path,
    seed_path: Option<&Path>,
) -> Result<()> {
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

    eprintln!(
        "Unfurling {} -> {}",
        pack_dir.display(),
        output.display()
    );

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

pub fn run_audit(
    pack_dir: &Path,
    json: bool,
    seed_path: Option<&Path>,
) -> Result<()> {
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
        println!("  source_pack_hash: {}", receipt.source_pack_hash.unwrap_or_default());
        println!("  target_pack_hash: {}", receipt.target_pack_hash.unwrap_or_default());
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
