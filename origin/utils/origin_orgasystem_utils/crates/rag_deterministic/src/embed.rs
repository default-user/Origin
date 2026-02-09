//! Stable embedding interface stub.
//!
//! Uses SHA-256-based deterministic "embeddings" — no external model calls.
//! The embedding is a fixed-dimensional vector derived from the content hash.
//! This is a toy implementation that still provides deterministic retrieval.

use sha2::{Digest, Sha256};

/// Embedding dimension (number of f64 values).
pub const EMBED_DIM: usize = 32;

/// A deterministic embedding vector.
#[derive(Debug, Clone, PartialEq)]
pub struct Embedding {
    /// The embedding vector (EMBED_DIM f64 values in [0, 1]).
    pub vector: Vec<f64>,
}

/// Compute a deterministic "embedding" from text.
///
/// This is a hash-based stub: it hashes the text and maps bytes to [0, 1] floats.
/// Same input always produces same output. Not semantically meaningful, but
/// sufficient for testing deterministic retrieval pipelines.
pub fn embed_chunk(text: &str) -> Embedding {
    let mut hasher = Sha256::new();
    hasher.update(text.as_bytes());
    let hash = hasher.finalize();

    let mut vector = Vec::with_capacity(EMBED_DIM);
    for &byte in hash.iter().take(EMBED_DIM) {
        vector.push(byte as f64 / 255.0);
    }

    Embedding { vector }
}

/// Compute cosine similarity between two embeddings.
///
/// Returns value in [-1, 1]. Deterministic for identical inputs.
pub fn cosine_similarity(a: &Embedding, b: &Embedding) -> f64 {
    assert_eq!(a.vector.len(), b.vector.len());

    let mut dot = 0.0f64;
    let mut norm_a = 0.0f64;
    let mut norm_b = 0.0f64;

    for i in 0..a.vector.len() {
        dot += a.vector[i] * b.vector[i];
        norm_a += a.vector[i] * a.vector[i];
        norm_b += b.vector[i] * b.vector[i];
    }

    let denom = norm_a.sqrt() * norm_b.sqrt();
    if denom == 0.0 {
        0.0
    } else {
        dot / denom
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embed_deterministic() {
        let a = embed_chunk("hello world");
        let b = embed_chunk("hello world");
        assert_eq!(a.vector, b.vector);
    }

    #[test]
    fn test_embed_dimension() {
        let e = embed_chunk("test");
        assert_eq!(e.vector.len(), EMBED_DIM);
    }

    #[test]
    fn test_embed_range() {
        let e = embed_chunk("test input");
        for v in &e.vector {
            assert!(*v >= 0.0 && *v <= 1.0);
        }
    }

    #[test]
    fn test_embed_different_inputs() {
        let a = embed_chunk("hello");
        let b = embed_chunk("world");
        assert_ne!(a.vector, b.vector);
    }

    #[test]
    fn test_cosine_self_similarity() {
        let e = embed_chunk("test");
        let sim = cosine_similarity(&e, &e);
        assert!((sim - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_cosine_deterministic() {
        let a = embed_chunk("hello");
        let b = embed_chunk("world");
        let s1 = cosine_similarity(&a, &b);
        let s2 = cosine_similarity(&a, &b);
        assert_eq!(s1, s2);
    }
}
