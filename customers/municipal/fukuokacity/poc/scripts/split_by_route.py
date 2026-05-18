"""
福岡市受領 PDF を路線別に分割する（Phase A Day 1-2）

路線番号:
- 数量計算書①（那珂工区）: 429-2, 430-3, 410-1-3
- 数量計算書②（板付・諸岡工区）: 86-1, 209-4, 452-5
- 図面一式: 上記6路線

各ページのテキストから路線番号を検出し、路線別にページを抽出して
dataset_prep/case_NNN/{calc,drawing}/ に配置する。

路線判定マッピングは route_mapping.json に出力（後で人手レビュー可能）。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber
from pypdf import PdfReader, PdfWriter

SCRIPT_DIR = Path(__file__).resolve().parent
POC_DIR = SCRIPT_DIR.parent
SRC_DIR = POC_DIR.parent
PREP_DIR = POC_DIR / "dataset_prep"
PREP_DIR.mkdir(parents=True, exist_ok=True)

# 路線リスト（順序が case_NNN に対応）
ROUTES = [
    "429-2",   # case_001
    "430-3",   # case_002
    "410-1-3", # case_003
    "86-1",    # case_004
    "209-4",   # case_005
    "452-5",   # case_006
]
CASE_OF = {r: f"case_{i+1:03d}" for i, r in enumerate(ROUTES)}

# 路線番号は「路線」「整理番号」などの文脈で出てくる
# 410-1-3 を先に検出しないと 410 と 1-3 に分割される可能性があるため、長い順に並べる
ROUTE_PATTERNS = sorted(ROUTES, key=len, reverse=True)


def detect_routes_in_text(text: str) -> set[str]:
    """テキストから路線番号を検出。複数路線がページ内に出る可能性も考慮。"""
    detected = set()
    if not text:
        return detected
    for r in ROUTE_PATTERNS:
        # ハイフン区切りなので単語境界での厳密マッチが難しい。
        # 周囲が数字でないことを確認する正規表現を使う。
        pattern = rf"(?<!\d){re.escape(r)}(?!\d)"
        if re.search(pattern, text):
            detected.add(r)
    return detected


def analyze_pdf(pdf_path: Path) -> list[dict]:
    """各ページのテキストから路線を判定"""
    page_routes = []
    with pdfplumber.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc.pages, 1):
            text = page.extract_text() or ""
            routes = detect_routes_in_text(text)
            page_routes.append(
                {
                    "page": i,
                    "routes": sorted(routes),
                    "snippet": text[:120].replace("\n", " "),
                }
            )
    return page_routes


def assign_pages_to_routes(page_routes: list[dict], doc_kind: str) -> dict[str, list[int]]:
    """
    ページを路線別にアサインする。
    - 単一ページに複数路線が出る場合（章境界・目次・総括）は、その全路線にコピー（重複OK）
    - 路線が検出されないページは "unassigned" に入れる（手動レビュー用）
    """
    assignment: dict[str, list[int]] = {r: [] for r in ROUTES}
    assignment["unassigned"] = []
    last_route: str | None = None
    for entry in page_routes:
        page = entry["page"]
        routes = entry["routes"]
        if not routes:
            # 路線が検出されない場合、直前の路線に紐づけ（連続性想定）
            if last_route:
                assignment[last_route].append(page)
            else:
                assignment["unassigned"].append(page)
        elif len(routes) == 1:
            r = routes[0]
            assignment[r].append(page)
            last_route = r
        else:
            # 複数路線：すべての該当路線に追加（章境界・総括ページを意図）
            for r in routes:
                assignment[r].append(page)
            last_route = None  # 連続性リセット
    return assignment


def write_pdf_subset(src: Path, pages: list[int], dst: Path) -> None:
    """ページ番号リスト（1-based）から新しい PDF を作成"""
    if not pages:
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    reader = PdfReader(str(src))
    writer = PdfWriter()
    for p in pages:
        writer.add_page(reader.pages[p - 1])
    with open(dst, "wb") as f:
        writer.write(f)


def main() -> int:
    calc1 = SRC_DIR / "0701　数量計算書①｜那珂工区.pdf"
    calc2 = SRC_DIR / "0701　数量計算書②｜板付・諸岡工区.pdf"
    drawing = SRC_DIR / "0701　図面一式｜那珂二丁目外.pdf"

    mapping = {}

    for label, pdf, kind in [
        ("calc1_那珂", calc1, "calc"),
        ("calc2_板付諸岡", calc2, "calc"),
        ("drawing_全路線", drawing, "drawing"),
    ]:
        if not pdf.exists():
            print(f"Missing: {pdf}", file=sys.stderr)
            continue
        print(f"Analyzing {pdf.name}...", file=sys.stderr)
        page_routes = analyze_pdf(pdf)
        assignment = assign_pages_to_routes(page_routes, kind)
        mapping[label] = {
            "source": str(pdf.relative_to(SRC_DIR.parents[2])),
            "kind": kind,
            "page_analysis": page_routes,
            "assignment": assignment,
        }

        # 路線別 PDF を出力
        for route, pages in assignment.items():
            if route == "unassigned" or not pages:
                continue
            case = CASE_OF.get(route)
            if case is None:
                continue
            out_name = f"{label}_{route}.pdf"
            out_path = PREP_DIR / case / kind / out_name
            write_pdf_subset(pdf, pages, out_path)
            print(f"  → {case}/{kind}/{out_name} ({len(pages)} pages)", file=sys.stderr)

        # unassigned ページ（総括・集計・全路線共通）を shared/ に集約
        unassigned = assignment.get("unassigned", [])
        if unassigned:
            shared_name = f"{label}_shared.pdf"
            shared_path = PREP_DIR / "shared" / kind / shared_name
            write_pdf_subset(pdf, unassigned, shared_path)
            print(f"  → shared/{kind}/{shared_name} ({len(unassigned)} pages, 共通・総括)", file=sys.stderr)

    # マッピングをJSON出力
    map_out = PREP_DIR / "route_mapping.json"
    map_out.write_text(json.dumps(mapping, indent=2, ensure_ascii=False))
    print(f"\nWrote {map_out}", file=sys.stderr)

    # 振り分けサマリ生成
    summary_lines = ["# 路線別仕分け結果サマリ", ""]
    for case_n, route in zip([f"case_{i+1:03d}" for i in range(6)], ROUTES):
        case_dir = PREP_DIR / case_n
        if not case_dir.exists():
            continue
        files = sorted(case_dir.rglob("*.pdf"))
        summary_lines.append(f"## {case_n}（路線 {route}）")
        for f in files:
            with pdfplumber.open(str(f)) as d:
                pages = len(d.pages)
            summary_lines.append(f"- `{f.relative_to(POC_DIR)}` ({pages}p)")
        summary_lines.append("")
    summary_lines.append("## Shared（全路線共通・総括・集計ページ）")
    summary_lines.append("")
    shared_dir = PREP_DIR / "shared"
    if shared_dir.exists():
        for f in sorted(shared_dir.rglob("*.pdf")):
            with pdfplumber.open(str(f)) as d:
                pages = len(d.pages)
            summary_lines.append(f"- `{f.relative_to(POC_DIR)}` ({pages}p)")
    summary_lines.append("")
    summary_lines.append("## 路線判定の元ページマッピング（trace用）")
    for label, info in mapping.items():
        summary_lines.append(f"")
        summary_lines.append(f"### {label}")
        for r, pages in sorted(info["assignment"].items()):
            if pages:
                summary_lines.append(f"- {r}: pages {pages}")
    (POC_DIR / "audit" / "route_assignment_summary.md").write_text("\n".join(summary_lines))
    print("Wrote route_assignment_summary.md", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
