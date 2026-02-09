//! Deterministic local index: BTreeMap-based document index with embedding lookup.

use crate::chunk::Chunk;
use crate::embed::{cosine_similarity, embed_chunk, Embedding};
use std::collections::BTreeMap;

/// An indexed chunk: chunk metadata + precomputed embedding.
#[derive(Debug, Clone)]
pub struct IndexedChunk {
    pub chunk: Chunk,
    pub embedding: Embedding,
}

/// Deterministic in-memory index for RAG retrieval.
///
/// Uses BTreeMap keyed by chunk ID for stable iteration order.
#[derive(Debug, Clone)]
pub struct DeterministicIndex {
    /// Chunks indexed by their stable ID.
    chunks: BTreeMap<String, IndexedChunk>,
}

impl DeterministicIndex {
    /// Create a new empty index.
    pub fn new() -> Self {
        Self {
            chunks: BTreeMap::new(),
        }
    }

    /// Index a document: chunk it and add all chunks to the index.
    ///
    /// Returns the number of chunks added.
    pub fn add_document(&mut self, source_id: &str, text: &str, max_chunk_chars: usize) -> usize {
        let chunks = crate::chunk::chunk_text(source_id, text, max_chunk_chars);
        let count = chunks.len();
        for chunk in chunks {
            let embedding = embed_chunk(&chunk.text);
            self.chunks.insert(
                chunk.id.clone(),
                IndexedChunk { chunk, embedding },
            );
        }
        count
    }

    /// Add a single pre-chunked entry.
    pub fn add_chunk(&mut self, chunk: Chunk) {
        let embedding = embed_chunk(&chunk.text);
        self.chunks.insert(
            chunk.id.clone(),
            IndexedChunk { chunk, embedding },
        );
    }

    /// Number of indexed chunks.
    pub fn len(&self) -> usize {
        self.chunks.len()
    }

    /// Whether the index is empty.
    pub fn is_empty(&self) -> bool {
        self.chunks.is_empty()
    }

    /// Retrieve the top-k most similar chunks to a query.
    ///
    /// Returns results sorted by similarity (descending), with deterministic
    /// tie-breaking by chunk ID (lexicographic ascending).
    pub fn query(&self, query_text: &str, top_k: usize) -> Vec<(f64, &IndexedChunk)> {
        let query_embedding = embed_chunk(query_text);

        // Compute similarities
        let mut scored: Vec<(f64, &str, &IndexedChunk)> = self
            .chunks
            .iter()
            .map(|(id, ic)| {
                let sim = cosine_similarity(&query_embedding, &ic.embedding);
                (sim, id.as_str(), ic)
            })
            .collect();

        // Sort: descending by similarity, then ascending by ID for deterministic ties
        scored.sort_by(|a, b| {
            b.0.partial_cmp(&a.0)
                .unwrap_or(std::cmp::Ordering::Equal)
                .then_with(|| a.1.cmp(b.1))
        });

        scored
            .into_iter()
            .take(top_k)
            .map(|(sim, _, ic)| (sim, ic))
            .collect()
    }

    /// Get a chunk by ID.
    pub fn get(&self, id: &str) -> Option<&IndexedChunk> {
        self.chunks.get(id)
    }

    /// Iterate over all indexed chunks in stable (sorted by ID) order.
    pub fn iter(&self) -> impl Iterator<Item = (&String, &IndexedChunk)> {
        self.chunks.iter()
    }
}

impl Default for DeterministicIndex {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_index_add_document() {
        let mut idx = DeterministicIndex::new();
        let count = idx.add_document("doc1", "Hello world.\n\nSecond paragraph.", 100);
        assert!(count > 0);
        assert_eq!(idx.len(), count);
    }

    #[test]
    fn test_index_query_deterministic() {
        let mut idx = DeterministicIndex::new();
        idx.add_document("doc1", "Rust is a systems programming language.", 100);
        idx.add_document("doc2", "Python is great for scripting.", 100);
        idx.add_document("doc3", "The weather is sunny today.", 100);

        let results1 = idx.query("programming language", 2);
        let results2 = idx.query("programming language", 2);

        assert_eq!(results1.len(), results2.len());
        for (a, b) in results1.iter().zip(results2.iter()) {
            assert_eq!(a.0, b.0);
            assert_eq!(a.1.chunk.id, b.1.chunk.id);
        }
    }

    #[test]
    fn test_index_empty_query() {
        let idx = DeterministicIndex::new();
        let results = idx.query("anything", 5);
        assert!(results.is_empty());
    }

    #[test]
    fn test_index_top_k_limit() {
        let mut idx = DeterministicIndex::new();
        for i in 0..10 {
            idx.add_document(
                &format!("doc{i}"),
                &format!("Document number {i} with content."),
                100,
            );
        }
        let results = idx.query("document", 3);
        assert_eq!(results.len(), 3);
    }

    #[test]
    fn test_index_stable_iteration() {
        let mut idx = DeterministicIndex::new();
        idx.add_document("b", "Second.", 100);
        idx.add_document("a", "First.", 100);

        let ids: Vec<&String> = idx.iter().map(|(id, _)| id).collect();
        // BTreeMap ensures sorted order
        for i in 1..ids.len() {
            assert!(ids[i - 1] <= ids[i], "iteration must be sorted by ID");
        }
    }
}
