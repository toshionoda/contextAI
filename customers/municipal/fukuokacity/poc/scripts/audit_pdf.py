"""
福岡市受領 PDF の構造判定スクリプト（Phase A Day 0）

各PDFを pdfplumber で開き、ページごとに以下を測定:
- ページサイズ (pt) と向き
- line / rect / curve / image / char の要素数
- テキスト密度（文字数 / ページ）
- ベクター度合いの判定（line+rect が閾値超え→ベクターPDF）

出力:
- audit/data_audit.md（人が読む集計レポート）
- audit/data_audit.json（機械処理用の生データ）
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

import pdfplumber

SCRIPT_DIR = Path(__file__).resolve().parent
POC_DIR = SCRIPT_DIR.parent  # customers/municipal/fukuokacity/poc/
SRC_DIR = POC_DIR.parent  # customers/municipal/fukuokacity/
REPO_ROOT = SRC_DIR.parents[2]  # contextAI/
AUDIT_DIR = POC_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

# ベクター判定の閾値（Phase A 仮置き）。1ページあたり line+rect の合計
VECTOR_THRESHOLD = 50


def audit_pdf(pdf_path: Path) -> dict:
    pages = []
    with pdfplumber.open(str(pdf_path)) as doc:
        for i, page in enumerate(doc.pages, 1):
            n_lines = len(page.lines)
            n_rects = len(page.rects)
            n_curves = len(page.curves)
            n_images = len(page.images)
            n_chars = len(page.chars)
            text = page.extract_text() or ""
            pages.append(
                {
                    "page": i,
                    "width_pt": float(page.width),
                    "height_pt": float(page.height),
                    "orientation": "landscape" if page.width > page.height else "portrait",
                    "lines": n_lines,
                    "rects": n_rects,
                    "curves": n_curves,
                    "images": n_images,
                    "chars": n_chars,
                    "text_chars": len(text),
                    "vector_score": n_lines + n_rects,
                }
            )
    return {
        "file": str(pdf_path.relative_to(REPO_ROOT)),
        "name": pdf_path.name,
        "pages": pages,
    }


def summarize(audit: dict) -> dict:
    pages = audit["pages"]
    if not pages:
        return {**audit, "summary": {"verdict": "EMPTY"}}
    total_pages = len(pages)
    avg_vector_score = mean(p["vector_score"] for p in pages)
    avg_chars = mean(p["text_chars"] for p in pages)
    avg_images = mean(p["images"] for p in pages)
    if avg_vector_score >= VECTOR_THRESHOLD and avg_chars > 50:
        verdict = "VECTOR"
    elif avg_chars > 50 and avg_vector_score < VECTOR_THRESHOLD:
        verdict = "TEXT_LAYER_ONLY"
    elif avg_images > 0 and avg_chars < 50:
        verdict = "IMAGE_PDF"
    else:
        verdict = "MIXED"
    return {
        **audit,
        "summary": {
            "total_pages": total_pages,
            "avg_vector_score": round(avg_vector_score, 1),
            "avg_text_chars": round(avg_chars, 1),
            "avg_images": round(avg_images, 2),
            "verdict": verdict,
        },
    }


def render_markdown(results: list[dict]) -> str:
    lines = [
        "# 福岡市受領 PDF 構造判定レポート（data_audit）",
        "",
        f"- 生成スクリプト: `customers/municipal/fukuokacity/poc/scripts/audit_pdf.py`",
        f"- 対象: `customers/municipal/fukuokacity/` 配下の PDF 5本",
        f"- ベクター判定閾値: line+rect の平均 ≥ {VECTOR_THRESHOLD}",
        "",
        "## サマリ",
        "",
        "| ファイル | ページ | 平均ベクター度 | 平均文字数/p | 平均画像/p | 判定 |",
        "|---|---|---|---|---|---|",
    ]
    for r in results:
        s = r["summary"]
        lines.append(
            f"| {r['name']} | {s['total_pages']} | {s['avg_vector_score']} | {s['avg_text_chars']} | {s['avg_images']} | **{s['verdict']}** |"
        )
    lines.append("")
    lines.append("## 判定基準")
    lines.append("")
    lines.append("- **VECTOR**: line+rect が多く、テキストも豊富 → pdfplumber で直接構造化可能")
    lines.append("- **TEXT_LAYER_ONLY**: テキストはあるが図形要素少 → テキスト抽出は可、図形解析は別手段")
    lines.append("- **IMAGE_PDF**: 画像主体 → DPI増加 + Gemini Vision に画像で投入")
    lines.append("- **MIXED**: ページ間で要素にバラつきあり → 個別対応")
    lines.append("")
    lines.append("## ページ別詳細")
    for r in results:
        lines.append("")
        lines.append(f"### {r['name']} (`{r['file']}`)")
        lines.append("")
        lines.append("| p | 向き | 幅×高 (pt) | lines | rects | curves | images | chars | text |")
        lines.append("|---|---|---|---|---|---|---|---|---|")
        for p in r["pages"]:
            lines.append(
                f"| {p['page']} | {p['orientation']} | {p['width_pt']:.0f}×{p['height_pt']:.0f} "
                f"| {p['lines']} | {p['rects']} | {p['curves']} | {p['images']} | {p['chars']} | {p['text_chars']} |"
            )
    lines.append("")
    lines.append("## Phase B 着手判断（Day 3 ゲート）")
    lines.append("")
    verdicts = [r["summary"]["verdict"] for r in results]
    if all(v in ("VECTOR", "TEXT_LAYER_ONLY", "MIXED") for v in verdicts):
        lines.append("✅ **Phase B 進行可**: 主要PDFはベクター/テキスト系で、Gemini Vision に投入可能。")
    else:
        lines.append("⚠️ **要検討**: IMAGE_PDF が含まれるため、DPI増加でラスタライズしてから Gemini Vision 投入。")
    lines.append("")
    lines.append("## 次アクション（Phase A Day 1-2）")
    lines.append("- 図面8p を路線別に仕分け（表題欄テキストで路線判定）")
    lines.append("- 数量計算書 27+21p を路線別に分割（章ヘッダで分割）")
    lines.append("- `dataset_prep/case_001..006/drawing/` に配置")
    return "\n".join(lines)


def main() -> int:
    pdfs = sorted(SRC_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF found under {SRC_DIR}", file=sys.stderr)
        return 1
    results = []
    for pdf in pdfs:
        print(f"Auditing {pdf.name} ...", file=sys.stderr)
        audit = audit_pdf(pdf)
        results.append(summarize(audit))

    json_out = AUDIT_DIR / "data_audit.json"
    md_out = AUDIT_DIR / "data_audit.md"
    json_out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    md_out.write_text(render_markdown(results))
    print(f"Wrote {json_out}", file=sys.stderr)
    print(f"Wrote {md_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
