//! DWG version signatures. Reference: ODA Open Design Specification §2.

use crate::error::DwgError;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DwgVersion {
    R14,     // AC1014
    R2000,   // AC1015
    R2004,   // AC1018
    R2007,   // AC1021
    R2010,   // AC1024
    R2013,   // AC1027
    R2018,   // AC1032
}

impl DwgVersion {
    /// First 6 bytes of a DWG file (ASCII version code).
    pub fn from_signature(sig: &[u8; 6]) -> Result<Self, DwgError> {
        match sig {
            b"AC1014" => Ok(Self::R14),
            b"AC1015" => Ok(Self::R2000),
            b"AC1018" => Ok(Self::R2004),
            b"AC1021" => Ok(Self::R2007),
            b"AC1024" => Ok(Self::R2010),
            b"AC1027" => Ok(Self::R2013),
            b"AC1032" => Ok(Self::R2018),
            other => Err(DwgError::UnsupportedVersion(*other)),
        }
    }

    pub fn signature(self) -> &'static [u8; 6] {
        match self {
            Self::R14 => b"AC1014",
            Self::R2000 => b"AC1015",
            Self::R2004 => b"AC1018",
            Self::R2007 => b"AC1021",
            Self::R2010 => b"AC1024",
            Self::R2013 => b"AC1027",
            Self::R2018 => b"AC1032",
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn roundtrip_signatures() {
        for v in [
            DwgVersion::R14,
            DwgVersion::R2000,
            DwgVersion::R2004,
            DwgVersion::R2007,
            DwgVersion::R2010,
            DwgVersion::R2013,
            DwgVersion::R2018,
        ] {
            let sig = v.signature();
            let back = DwgVersion::from_signature(sig).expect("round-trip");
            assert_eq!(v, back);
        }
    }

    #[test]
    fn unknown_signature_rejected() {
        let bad = b"AC9999";
        assert!(matches!(
            DwgVersion::from_signature(bad),
            Err(DwgError::UnsupportedVersion(_))
        ));
    }
}
