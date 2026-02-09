//! CPACK framing protocol: header, payload encoding, and integrity.
//!
//! Binary format (v1):
//!   Bytes 0-3:    Magic "CPCK"
//!   Byte  4:      Version (1)
//!   Byte  5:      Compression method (1 = zstd)
//!   Bytes 6-7:    Reserved (0x00, 0x00)
//!   Bytes 8-39:   SHA-256 of uncompressed payload (32 bytes)
//!   Bytes 40-47:  Compressed data length (u64 LE)
//!   Bytes 48..:   Zstd compressed payload
//!
//! Payload format (before compression):
//!   u32 LE: manifest JSON length
//!   bytes:  manifest JSON (canonical, sorted keys)
//!   u32 LE: file count
//!   For each file (sorted by relative path):
//!     u32 LE: path length (UTF-8)
//!     bytes:  path
//!     u64 LE: content length
//!     bytes:  content

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

/// Magic bytes identifying a CPACK file.
pub const CPACK_MAGIC: &[u8; 4] = b"CPCK";

/// Current CPACK format version.
pub const CPACK_VERSION: u8 = 1;

/// Compression method: zstd.
pub const COMPRESS_ZSTD: u8 = 1;

/// Fixed header size in bytes.
pub const HEADER_SIZE: usize = 48;

/// CPACK file header.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CpackHeader {
    pub version: u8,
    pub compression_method: u8,
    pub payload_sha256: [u8; 32],
    pub compressed_size: u64,
}

impl CpackHeader {
    /// Serialize header to bytes.
    pub fn to_bytes(&self) -> Vec<u8> {
        let mut buf = Vec::with_capacity(HEADER_SIZE);
        buf.extend_from_slice(CPACK_MAGIC);
        buf.push(self.version);
        buf.push(self.compression_method);
        buf.extend_from_slice(&[0u8; 2]); // reserved
        buf.extend_from_slice(&self.payload_sha256);
        buf.extend_from_slice(&self.compressed_size.to_le_bytes());
        buf
    }

    /// Parse header from bytes.
    pub fn from_bytes(data: &[u8]) -> Result<Self, FrameError> {
        if data.len() < HEADER_SIZE {
            return Err(FrameError::HeaderTooShort {
                got: data.len(),
                need: HEADER_SIZE,
            });
        }
        if &data[0..4] != CPACK_MAGIC {
            return Err(FrameError::BadMagic);
        }
        let version = data[4];
        if version != CPACK_VERSION {
            return Err(FrameError::UnsupportedVersion(version));
        }
        let compression_method = data[5];
        if compression_method != COMPRESS_ZSTD {
            return Err(FrameError::UnsupportedCompression(compression_method));
        }
        let mut sha = [0u8; 32];
        sha.copy_from_slice(&data[8..40]);
        let compressed_size = u64::from_le_bytes(data[40..48].try_into().unwrap());
        Ok(Self {
            version,
            compression_method,
            payload_sha256: sha,
            compressed_size,
        })
    }
}

/// Encode a payload: manifest JSON + sorted file entries -> deterministic bytes.
pub fn encode_payload(
    manifest_json: &[u8],
    files: &[(String, Vec<u8>)], // sorted by path
) -> Vec<u8> {
    let mut buf = Vec::new();

    // Manifest
    let mlen = manifest_json.len() as u32;
    buf.extend_from_slice(&mlen.to_le_bytes());
    buf.extend_from_slice(manifest_json);

    // File count
    let fcount = files.len() as u32;
    buf.extend_from_slice(&fcount.to_le_bytes());

    // Files (must already be sorted by caller)
    for (path, content) in files {
        let plen = path.len() as u32;
        buf.extend_from_slice(&plen.to_le_bytes());
        buf.extend_from_slice(path.as_bytes());
        let clen = content.len() as u64;
        buf.extend_from_slice(&clen.to_le_bytes());
        buf.extend_from_slice(content);
    }

    buf
}

/// Decode a payload back into manifest JSON and file entries.
pub fn decode_payload(data: &[u8]) -> Result<(Vec<u8>, Vec<(String, Vec<u8>)>), FrameError> {
    let mut pos = 0;

    // Manifest
    if data.len() < pos + 4 {
        return Err(FrameError::PayloadTruncated);
    }
    let mlen = u32::from_le_bytes(data[pos..pos + 4].try_into().unwrap()) as usize;
    pos += 4;
    if data.len() < pos + mlen {
        return Err(FrameError::PayloadTruncated);
    }
    let manifest_json = data[pos..pos + mlen].to_vec();
    pos += mlen;

    // File count
    if data.len() < pos + 4 {
        return Err(FrameError::PayloadTruncated);
    }
    let fcount = u32::from_le_bytes(data[pos..pos + 4].try_into().unwrap()) as usize;
    pos += 4;

    let mut files = Vec::with_capacity(fcount);
    for _ in 0..fcount {
        // Path
        if data.len() < pos + 4 {
            return Err(FrameError::PayloadTruncated);
        }
        let plen = u32::from_le_bytes(data[pos..pos + 4].try_into().unwrap()) as usize;
        pos += 4;
        if data.len() < pos + plen {
            return Err(FrameError::PayloadTruncated);
        }
        let path = String::from_utf8(data[pos..pos + plen].to_vec())
            .map_err(|_| FrameError::InvalidUtf8Path)?;
        pos += plen;

        // Content
        if data.len() < pos + 8 {
            return Err(FrameError::PayloadTruncated);
        }
        let clen = u64::from_le_bytes(data[pos..pos + 8].try_into().unwrap()) as usize;
        pos += 8;
        if data.len() < pos + clen {
            return Err(FrameError::PayloadTruncated);
        }
        let content = data[pos..pos + clen].to_vec();
        pos += clen;

        files.push((path, content));
    }

    Ok((manifest_json, files))
}

/// Compute SHA-256 of a byte slice.
pub fn sha256_bytes(data: &[u8]) -> [u8; 32] {
    let mut hasher = Sha256::new();
    hasher.update(data);
    let result = hasher.finalize();
    let mut out = [0u8; 32];
    out.copy_from_slice(&result);
    out
}

#[derive(Debug, thiserror::Error)]
pub enum FrameError {
    #[error("header too short: got {got}, need {need}")]
    HeaderTooShort { got: usize, need: usize },
    #[error("bad magic bytes (expected CPCK)")]
    BadMagic,
    #[error("unsupported CPACK version: {0}")]
    UnsupportedVersion(u8),
    #[error("unsupported compression method: {0}")]
    UnsupportedCompression(u8),
    #[error("payload truncated")]
    PayloadTruncated,
    #[error("invalid UTF-8 in file path")]
    InvalidUtf8Path,
    #[error("payload SHA-256 mismatch")]
    IntegrityMismatch,
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    #[error("JSON error: {0}")]
    Json(#[from] serde_json::Error),
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_header_roundtrip() {
        let header = CpackHeader {
            version: CPACK_VERSION,
            compression_method: COMPRESS_ZSTD,
            payload_sha256: [0xAB; 32],
            compressed_size: 12345,
        };
        let bytes = header.to_bytes();
        assert_eq!(bytes.len(), HEADER_SIZE);
        let parsed = CpackHeader::from_bytes(&bytes).unwrap();
        assert_eq!(parsed.version, CPACK_VERSION);
        assert_eq!(parsed.compressed_size, 12345);
        assert_eq!(parsed.payload_sha256, [0xAB; 32]);
    }

    #[test]
    fn test_payload_roundtrip() {
        let manifest = b"{\"version\":\"1.0\"}";
        let files = vec![
            ("a/b.txt".to_string(), b"hello".to_vec()),
            ("c.txt".to_string(), b"world".to_vec()),
        ];
        let encoded = encode_payload(manifest, &files);
        let (dec_manifest, dec_files) = decode_payload(&encoded).unwrap();
        assert_eq!(dec_manifest, manifest);
        assert_eq!(dec_files.len(), 2);
        assert_eq!(dec_files[0].0, "a/b.txt");
        assert_eq!(dec_files[0].1, b"hello");
        assert_eq!(dec_files[1].0, "c.txt");
        assert_eq!(dec_files[1].1, b"world");
    }

    #[test]
    fn test_payload_deterministic() {
        let manifest = b"{\"test\":true}";
        let files = vec![("x.rs".to_string(), b"fn main(){}".to_vec())];
        let a = encode_payload(manifest, &files);
        let b = encode_payload(manifest, &files);
        assert_eq!(a, b);
    }

    #[test]
    fn test_bad_magic() {
        let data = b"XXXX\x01\x01\x00\x00";
        let mut buf = data.to_vec();
        buf.extend_from_slice(&[0u8; 40]);
        assert!(matches!(
            CpackHeader::from_bytes(&buf),
            Err(FrameError::BadMagic)
        ));
    }
}
