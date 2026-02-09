//! Deterministic RAG: stable chunking, embedding stub, and local index retrieval.
//!
//! This is a toy-but-real implementation: deterministic chunking with stable
//! hash-based "embeddings" and BTreeMap-based retrieval. No external calls required.

pub mod chunk;
pub mod embed;
pub mod index;
pub mod retrieve;

pub use chunk::{chunk_text, Chunk};
pub use embed::{embed_chunk, Embedding};
pub use index::DeterministicIndex;
pub use retrieve::{retrieve, RetrievalResult};
