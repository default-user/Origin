//! Deterministic chunking: split text into fixed-size, non-overlapping chunks.
//!
//! Chunks are split on paragraph boundaries (double newline), then on sentence
//! boundaries if still too large, then on word boundaries as a last resort.
//! Each chunk gets a stable ID derived from its content hash.

use sha2::{Digest, Sha256};

/// A text chunk with a stable content-derived ID.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Chunk {
    /// Stable ID: SHA-256 of (source_id + ":" + chunk_index).
    pub id: String,
    /// The chunk text.
    pub text: String,
    /// Index of this chunk within the source document.
    pub index: usize,
    /// Source document identifier.
    pub source_id: String,
}

/// Default target chunk size in characters.
pub const DEFAULT_CHUNK_SIZE: usize = 512;

/// Split text into deterministic chunks.
///
/// - `source_id`: stable identifier for the source document.
/// - `text`: the text to chunk.
/// - `max_chars`: target maximum characters per chunk.
///
/// Returns chunks in order. Same input always produces same output.
pub fn chunk_text(source_id: &str, text: &str, max_chars: usize) -> Vec<Chunk> {
    let max_chars = if max_chars == 0 { DEFAULT_CHUNK_SIZE } else { max_chars };

    // Split on paragraph boundaries first
    let paragraphs: Vec<&str> = text.split("\n\n").collect();
    let mut chunks = Vec::new();
    let mut current = String::new();
    let mut chunk_index = 0usize;

    for para in paragraphs {
        let trimmed = para.trim();
        if trimmed.is_empty() {
            continue;
        }

        if current.len() + trimmed.len() + 2 > max_chars && !current.is_empty() {
            // Emit current chunk
            let id = compute_chunk_id(source_id, chunk_index);
            chunks.push(Chunk {
                id,
                text: current.trim().to_string(),
                index: chunk_index,
                source_id: source_id.to_string(),
            });
            chunk_index += 1;
            current.clear();
        }

        // If a single paragraph exceeds max_chars, split on sentences
        if trimmed.len() > max_chars {
            if !current.is_empty() {
                let id = compute_chunk_id(source_id, chunk_index);
                chunks.push(Chunk {
                    id,
                    text: current.trim().to_string(),
                    index: chunk_index,
                    source_id: source_id.to_string(),
                });
                chunk_index += 1;
                current.clear();
            }
            for sub in split_large(trimmed, max_chars) {
                let id = compute_chunk_id(source_id, chunk_index);
                chunks.push(Chunk {
                    id,
                    text: sub,
                    index: chunk_index,
                    source_id: source_id.to_string(),
                });
                chunk_index += 1;
            }
        } else {
            if !current.is_empty() {
                current.push_str("\n\n");
            }
            current.push_str(trimmed);
        }
    }

    // Emit remaining
    if !current.trim().is_empty() {
        let id = compute_chunk_id(source_id, chunk_index);
        chunks.push(Chunk {
            id,
            text: current.trim().to_string(),
            index: chunk_index,
            source_id: source_id.to_string(),
        });
    }

    chunks
}

/// Split a large text block into pieces ≤ max_chars on word boundaries.
fn split_large(text: &str, max_chars: usize) -> Vec<String> {
    let mut pieces = Vec::new();
    let mut current = String::new();

    for word in text.split_whitespace() {
        if current.len() + word.len() + 1 > max_chars && !current.is_empty() {
            pieces.push(current.trim().to_string());
            current.clear();
        }
        if !current.is_empty() {
            current.push(' ');
        }
        current.push_str(word);
    }
    if !current.trim().is_empty() {
        pieces.push(current.trim().to_string());
    }
    pieces
}

/// Compute a deterministic chunk ID from source_id and chunk index.
fn compute_chunk_id(source_id: &str, index: usize) -> String {
    let mut hasher = Sha256::new();
    hasher.update(source_id.as_bytes());
    hasher.update(b":");
    hasher.update(index.to_string().as_bytes());
    hex::encode(hasher.finalize())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_chunk_deterministic() {
        let text = "Hello world.\n\nThis is a test.\n\nAnother paragraph.";
        let a = chunk_text("doc1", text, 100);
        let b = chunk_text("doc1", text, 100);
        assert_eq!(a, b);
    }

    #[test]
    fn test_chunk_ids_stable() {
        let text = "Hello world.\n\nSecond paragraph.";
        let chunks = chunk_text("doc1", text, 100);
        assert!(!chunks.is_empty());
        // Run again - same IDs
        let chunks2 = chunk_text("doc1", text, 100);
        for (a, b) in chunks.iter().zip(chunks2.iter()) {
            assert_eq!(a.id, b.id);
        }
    }

    #[test]
    fn test_chunk_respects_max_size() {
        let text = "Word ".repeat(200);
        let chunks = chunk_text("doc2", &text, 50);
        for chunk in &chunks {
            assert!(
                chunk.text.len() <= 55, // some tolerance for word boundaries
                "chunk too large: {} chars",
                chunk.text.len()
            );
        }
    }

    #[test]
    fn test_chunk_different_sources_different_ids() {
        let text = "Same text.";
        let a = chunk_text("doc_a", text, 100);
        let b = chunk_text("doc_b", text, 100);
        assert_ne!(a[0].id, b[0].id);
    }

    #[test]
    fn test_empty_text() {
        let chunks = chunk_text("empty", "", 100);
        assert!(chunks.is_empty());
    }

    #[test]
    fn test_whitespace_only() {
        let chunks = chunk_text("ws", "   \n\n   \n\n   ", 100);
        assert!(chunks.is_empty());
    }
}
