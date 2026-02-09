//! originctl: CLI for Origin orgasystem pack/verify/unfurl/audit/replicate.

use clap::{Parser, Subcommand};
use std::path::PathBuf;
use std::process;

mod commands;

#[derive(Parser)]
#[command(
    name = "originctl",
    about = "Origin orgasystem utility: pack, verify, unfurl, audit, and replicate.",
    version
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Pack a repository into a DPACK snapshot.
    Pack {
        /// Path to the repository root.
        #[arg(long)]
        repo_root: PathBuf,
        /// Output directory for the pack.
        #[arg(short, long)]
        output: PathBuf,
        /// Optional policy YAML file.
        #[arg(long)]
        policy: Option<PathBuf>,
        /// Path to the seed file (defaults to spec/seed/denotum.seed.2i.yaml in repo_root).
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// Verify a DPACK snapshot.
    Verify {
        /// Path to the DPACK directory.
        pack: PathBuf,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// Unfurl (restore) a DPACK snapshot to a target directory.
    Unfurl {
        /// Path to the DPACK directory.
        pack: PathBuf,
        /// Target directory.
        #[arg(short, long)]
        output: PathBuf,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// Audit a DPACK snapshot and output gate results.
    Audit {
        /// Path to the DPACK directory.
        pack: PathBuf,
        /// Output as JSON.
        #[arg(long)]
        json: bool,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// Replicate the orgasystem.
    Replicate {
        #[command(subcommand)]
        mode: ReplicateMode,
    },
}

#[derive(Subcommand)]
enum ReplicateMode {
    /// R0: Local clone via pack+unfurl.
    Local {
        /// Path to the repository root.
        #[arg(long)]
        repo_root: PathBuf,
        /// Target directory.
        #[arg(short, long)]
        output: PathBuf,
        /// Optional policy YAML file.
        #[arg(long)]
        policy: Option<PathBuf>,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// R1: Produce a DPACK rootball for transport.
    Rootball {
        /// Path to the repository root.
        #[arg(long)]
        repo_root: PathBuf,
        /// Output directory for the rootball.
        #[arg(short, long)]
        output: PathBuf,
        /// Optional policy YAML file.
        #[arg(long)]
        policy: Option<PathBuf>,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
    /// R2: Unfurl from a source directory into a fresh repo tree (v1).
    Zip2repoV1 {
        /// Source directory (simulating extracted zip).
        #[arg(long)]
        source: PathBuf,
        /// Output directory.
        #[arg(long)]
        out_dir: PathBuf,
        /// Initialize a git repository in the output.
        #[arg(long)]
        init_git: bool,
        /// Optional policy YAML file.
        #[arg(long)]
        policy: Option<PathBuf>,
        /// Path to the seed file.
        #[arg(long)]
        seed: Option<PathBuf>,
    },
}

fn main() {
    let cli = Cli::parse();
    let result = match cli.command {
        Commands::Pack {
            repo_root,
            output,
            policy,
            seed,
        } => commands::run_pack(&repo_root, &output, policy.as_deref(), seed.as_deref()),
        Commands::Verify { pack, seed } => commands::run_verify(&pack, seed.as_deref()),
        Commands::Unfurl { pack, output, seed } => {
            commands::run_unfurl(&pack, &output, seed.as_deref())
        }
        Commands::Audit { pack, json, seed } => {
            commands::run_audit(&pack, json, seed.as_deref())
        }
        Commands::Replicate { mode } => match mode {
            ReplicateMode::Local {
                repo_root,
                output,
                policy,
                seed,
            } => commands::run_replicate_local(
                &repo_root,
                &output,
                policy.as_deref(),
                seed.as_deref(),
            ),
            ReplicateMode::Rootball {
                repo_root,
                output,
                policy,
                seed,
            } => commands::run_replicate_rootball(
                &repo_root,
                &output,
                policy.as_deref(),
                seed.as_deref(),
            ),
            ReplicateMode::Zip2repoV1 {
                source,
                out_dir,
                init_git,
                policy,
                seed,
            } => commands::run_replicate_zip2repo_v1(
                &source,
                &out_dir,
                init_git,
                policy.as_deref(),
                seed.as_deref(),
            ),
        },
    };

    if let Err(e) = result {
        eprintln!("FAIL CLOSED: {e}");
        process::exit(1);
    }
}
