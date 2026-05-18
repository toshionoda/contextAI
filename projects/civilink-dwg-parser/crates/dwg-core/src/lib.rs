//! civilink-dwg-parser core library.
//!
//! Clean-room implementation. Do not open LibreDWG or other GPL-licensed DWG
//! parser sources. Reference only: ODA Open Design Specification and direct
//! observation of sample DWG files.

pub mod error;
pub mod version;

pub use error::{DwgError, Result};
pub use version::DwgVersion;
