//! Pack/replication policy: allowlist and denylist for file inclusion.

use serde::{Deserialize, Serialize};
use std::path::Path;

/// Policy controlling which files are included in or excluded from packs.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Policy {
    /// Glob patterns for files to include. Empty means include all.
    #[serde(default)]
    pub include: Vec<String>,
    /// Glob patterns for files to exclude. Applied after include.
    #[serde(default)]
    pub exclude: Vec<String>,
}

impl Default for Policy {
    fn default() -> Self {
        Self {
            include: vec![],
            exclude: vec![
                ".git/**".to_string(),
                ".git".to_string(),
            ],
        }
    }
}

impl Policy {
    /// Load policy from a YAML file.
    pub fn load(path: &Path) -> Result<Self, PolicyError> {
        let content = std::fs::read_to_string(path)?;
        let policy: Self = serde_yaml::from_str(&content)?;
        Ok(policy)
    }

    /// Check if a relative path is allowed by this policy.
    pub fn is_allowed(&self, rel_path: &str) -> bool {
        // Check excludes first
        for pattern in &self.exclude {
            if glob_match(pattern, rel_path) {
                return false;
            }
        }
        // If includes is empty, everything (not excluded) is allowed
        if self.include.is_empty() {
            return true;
        }
        // Otherwise must match at least one include pattern
        for pattern in &self.include {
            if glob_match(pattern, rel_path) {
                return true;
            }
        }
        false
    }
}

/// Minimal glob matching: supports * (single segment) and ** (recursive).
fn glob_match(pattern: &str, path: &str) -> bool {
    // Handle exact match
    if pattern == path {
        return true;
    }

    // Handle ** prefix (recursive match)
    if let Some(suffix) = pattern.strip_prefix("**/") {
        // Match suffix against any path suffix
        if path.ends_with(suffix) {
            return true;
        }
        // Also try matching at any directory level
        for (i, _) in path.char_indices() {
            if path[i..].starts_with('/') {
                if glob_match(suffix, &path[i + 1..]) {
                    return true;
                }
            }
        }
        return glob_match(suffix, path);
    }

    // Handle ** suffix (matches everything under a path)
    if let Some(prefix) = pattern.strip_suffix("/**") {
        return path.starts_with(prefix)
            && (path.len() == prefix.len()
                || path.as_bytes().get(prefix.len()) == Some(&b'/'));
    }

    // Handle single * wildcard
    if pattern.contains('*') {
        let parts: Vec<&str> = pattern.split('*').collect();
        if parts.len() == 2 {
            return path.starts_with(parts[0])
                && path.ends_with(parts[1])
                && !path[parts[0].len()..path.len() - parts[1].len()].contains('/');
        }
    }

    false
}

#[derive(Debug, thiserror::Error)]
pub enum PolicyError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("YAML parse error: {0}")]
    Yaml(#[from] serde_yaml::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_default_policy_excludes_git() {
        let policy = Policy::default();
        assert!(!policy.is_allowed(".git"));
        assert!(!policy.is_allowed(".git/objects/abc"));
        assert!(policy.is_allowed("src/main.rs"));
    }

    #[test]
    fn test_glob_match_star() {
        assert!(glob_match("*.rs", "main.rs"));
        assert!(!glob_match("*.rs", "src/main.rs"));
    }

    #[test]
    fn test_glob_match_double_star_prefix() {
        assert!(glob_match("**/*.rs", "src/main.rs"));
        assert!(glob_match("**/*.rs", "a/b/c/main.rs"));
    }

    #[test]
    fn test_glob_match_double_star_suffix() {
        assert!(glob_match(".git/**", ".git/objects/abc"));
        assert!(!glob_match(".git/**", "src/main.rs"));
    }

    #[test]
    fn test_policy_include_filter() {
        let policy = Policy {
            include: vec!["*.rs".to_string(), "Cargo.toml".to_string()],
            exclude: vec![],
        };
        assert!(policy.is_allowed("main.rs"));
        assert!(policy.is_allowed("Cargo.toml"));
        assert!(!policy.is_allowed("README.md"));
    }
}
