use thiserror::Error;

#[derive(Debug, Error)]
pub enum DwgError {
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("unsupported DWG version signature: {0:?}")]
    UnsupportedVersion([u8; 6]),

    #[error("malformed header at offset {offset:#x}: {reason}")]
    MalformedHeader { offset: u64, reason: String },

    #[error("CRC mismatch: expected {expected:#x}, got {actual:#x}")]
    CrcMismatch { expected: u32, actual: u32 },

    #[error("not implemented yet: {0}")]
    NotImplemented(&'static str),
}

pub type Result<T> = std::result::Result<T, DwgError>;
