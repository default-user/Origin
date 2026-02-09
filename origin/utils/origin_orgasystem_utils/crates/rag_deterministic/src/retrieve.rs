//! Deterministic retrieval: query the index and return structured results.

use crate::index::{DeterministicIndex, IndexedChunk};
use serde::{Deserialize, Serialize};

/// A retrieval result with score and chunk metadata.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RetrievalResult {
    /// Chunk ID.
    pub chunk_id: String,
    /// Source document ID.
    pub source_id: String,
    /// Chunk index within document.
    pub chunk_index: usize,
    /// Similarity score.
    pub score: f64,
    /// The chunk text.
    pub text: String,
}

/// Retrieve top-k results from the index for a query.
///
/// Deterministic: same index + same query = same results, always.
pub fn retrieve(index: &DeterministicIndex, query: &str, top_k: usize) -> Vec<RetrievalResult> {
    index
        .query(query, top_k)
        .into_iter()
        .map(|(score, ic): (f64, &IndexedChunk)| RetrievalResult {
            chunk_id: ic.chunk.id.clone(),
            source_id: ic.chunk.source_id.clone(),
            chunk_index: ic.chunk.index,
            score,
            text: ic.chunk.text.clone(),
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::index::DeterministicIndex;

    #[test]
    fn test_retrieve_deterministic() {
        let mut idx = DeterministicIndex::new();
        idx.add_document("doc1", "The Rust programming language is fast.", 100);
        idx.add_document("doc2", "Python is interpreted.", 100);

        let r1 = retrieve(&idx, "fast programming", 2);
        let r2 = retrieve(&idx, "fast programming", 2);

        assert_eq!(r1.len(), r2.len());
        for (a, b) in r1.iter().zip(r2.iter()) {
            assert_eq!(a.chunk_id, b.chunk_id);
            assert_eq!(a.score, b.score);
            assert_eq!(a.text, b.text);
        }
    }

    #[test]
    fn test_retrieve_serializable() {
        let mut idx = DeterministicIndex::new();
        idx.add_document("doc1", "Test content.", 100);
        let results = retrieve(&idx, "test", 1);
        let json = serde_json::to_string(&results).unwrap();
        let parsed: Vec<RetrievalResult> = serde_json::from_str(&json).unwrap();
        assert_eq!(parsed.len(), results.len());
        assert_eq!(parsed[0].chunk_id, results[0].chunk_id);
    }
}
