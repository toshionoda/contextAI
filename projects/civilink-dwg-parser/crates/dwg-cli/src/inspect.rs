//! `dwg-inspect`: read the first 6 bytes of a DWG file and print its version.
//!
//! Phase A1 で header.rs と統合し、ヘッダ情報の詳細表示に拡張する。
//! 現時点は Phase A0/A1 のスモークテスト用途。

use std::fs::File;
use std::io::Read;
use std::path::PathBuf;
use std::process::ExitCode;

use clap::Parser;
use dwg_core::DwgVersion;

#[derive(Parser)]
#[command(name = "dwg-inspect", about = "Inspect a DWG file signature")]
struct Cli {
    /// Path to a .dwg file
    path: PathBuf,
}

fn main() -> ExitCode {
    let cli = Cli::parse();

    let mut file = match File::open(&cli.path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("error: could not open {}: {}", cli.path.display(), e);
            return ExitCode::FAILURE;
        }
    };

    let mut sig = [0u8; 6];
    if let Err(e) = file.read_exact(&mut sig) {
        eprintln!("error: could not read signature: {}", e);
        return ExitCode::FAILURE;
    }

    match DwgVersion::from_signature(&sig) {
        Ok(v) => {
            println!("{} version: {:?}", cli.path.display(), v);
            println!("signature:  {}", std::str::from_utf8(&sig).unwrap_or("?"));
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("{} unsupported: {}", cli.path.display(), e);
            ExitCode::FAILURE
        }
    }
}
