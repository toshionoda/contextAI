"""PoC ディレクトリのパス管理。

環境変数で上書き可能だが、既定では PoC ディレクトリ構造から自動検出する。
"""
from __future__ import annotations

import os
from pathlib import Path


_THIS = Path(__file__).resolve()
SRC_ROOT = _THIS.parents[1]                   # src/
POC_ROOT = SRC_ROOT.parent                    # customers/.../poc/
DATASET_PREP = Path(os.environ.get("DATASET_DIR", POC_ROOT / "dataset_prep"))
RESULTS_DIR = Path(os.environ.get("RESULTS_DIR", POC_ROOT / "results"))
SCHEMA_DIR = POC_ROOT / "schema"
CONFIG_DIR = POC_ROOT / "config"
KNOWLEDGE_FILE = CONFIG_DIR / "knowledge_sewer_kanra.md"
SOUKATU_SCHEMA = SCHEMA_DIR / "fukuoka_soukatu.yaml"

CASES = [
    ("case_001", "429-2"),
    ("case_002", "430-3"),
    ("case_003", "410-1-3"),
    ("case_004", "86-1"),
    ("case_005", "209-4"),
    ("case_006", "452-5"),
]

# 2026-05-16 受領分。Phase A の路線分割／GT作成が未完のため、本処理（all/extract-calc等）には
# まだ組み込まない。検証時は --case を明示的に指定して動かす想定。
# 各案件は「数量計算書+総括表+金抜設計書+図面」が独立PDFで、路線が PDF 内に複数同居している。
NEW_CASES_2026_05_16 = [
    # (case_id, expected_route_or_label, source_dir)
    ("case_007", "西部C008-田島四丁目", "送付用_西部下水/202403C008_草ヶ江（田島四丁目）外地区下水道築造工事"),
    ("case_008", "西部C108-鳥飼六丁目", "送付用_西部下水/202403C108_草ヶ江（鳥飼六丁目）地区（２）下水道築造工事"),
    ("case_009", "中部-平尾高宮-大楠一丁目3", "送付用_中部下水/平尾高宮（大楠一丁目3）地区下水道築造工事"),
    ("case_010", "中部-福岡-桜坂二丁目外", "送付用_中部下水/福岡（桜坂二丁目外）地区下水道築造工事"),
]


def case_soukatu_pdf(case_id: str) -> Path | None:
    """case 配下に soukatu/ がある場合の数量総括表PDFを返す（新規案件向け）。"""
    d = case_dir(case_id) / "soukatu"
    if not d.exists():
        return None
    pdfs = list(d.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def case_kingenuki_pdf(case_id: str) -> Path | None:
    """case 配下に kingenuki/ がある場合の金抜設計書PDFを返す（新規案件向け）。"""
    d = case_dir(case_id) / "kingenuki"
    if not d.exists():
        return None
    pdfs = list(d.glob("*.pdf"))
    return pdfs[0] if pdfs else None


def case_dir(case_id: str) -> Path:
    return DATASET_PREP / case_id


def case_calc_pdf(case_id: str) -> Path | None:
    pdfs = list((case_dir(case_id) / "calc").glob("*.pdf"))
    return pdfs[0] if pdfs else None


def case_drawing_pdf(case_id: str) -> Path | None:
    pdfs = list((case_dir(case_id) / "drawing").glob("*.pdf"))
    return pdfs[0] if pdfs else None


def case_ground_truth(case_id: str) -> Path | None:
    p = case_dir(case_id) / "ground_truth.json"
    return p if p.exists() else None


def case_results_dir(case_id: str) -> Path:
    p = RESULTS_DIR / case_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def shared_calc_pdfs() -> list[Path]:
    return sorted((DATASET_PREP / "shared" / "calc").glob("*.pdf"))


def shared_drawing_pdfs() -> list[Path]:
    return sorted((DATASET_PREP / "shared" / "drawing").glob("*.pdf"))
