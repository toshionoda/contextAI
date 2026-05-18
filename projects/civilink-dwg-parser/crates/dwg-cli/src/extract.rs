//! `dwg-extract`: placeholder for Phase A4. 現時点は未実装で、呼ばれたら
//! Phase A4 まで待つ旨を出力して終了する。

use std::process::ExitCode;

fn main() -> ExitCode {
    eprintln!("dwg-extract is not implemented yet. See Phase A4 in the plan.");
    ExitCode::from(2)
}
