//! CPACK: Deterministic compressed pack format.
//!
//! A CPACK is a single-file compressed representation of a DPACK directory.
//! Format: header + zstd-compressed payload + SHA-256 integrity hash.
//! Round-trip invariant: decompress(compress(dpack)) == dpack.

pub mod compress;
pub mod decompress;
pub mod frame;

pub use compress::compress_dpack;
pub use decompress::decompress_cpack;
pub use frame::{CpackHeader, CPACK_MAGIC, CPACK_VERSION};
