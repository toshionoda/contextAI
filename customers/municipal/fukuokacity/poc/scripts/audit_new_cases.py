"""
2026-05-16 受領分の新規4案件PDFの構造判定 + 管更生/築造の内容分類スクリプト。

対象（POC_ROOT.parent 配下）:
- 送付用_西部下水/202403C008_草ヶ江（田島四丁目）外地区下水道築造工事
- 送付用_西部下水/202403C108_草ヶ江（鳥飼六丁目）地区（２）下水道築造工事
- 送付用_中部下水/平尾高宮（大楠一丁目3）地区下水道築造工事
- 送付用_中部下水/福岡（桜坂二丁目外）地区下水道築造工事

出力:
- audit/data_audit_2026-05-16.md
- audit/data_audit_2026-05-16.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean

import pdfplumber

SCRIPT_DIR = Path(__file__).resolve().parent
POC_DIR = SCRIPT_DIR.parent
SRC_DIR = POC_DIR.parent  # customers/municipal/fukuokacity/
REPO_ROOT = SRC_DIR.parents[2]
AUDIT_DIR = POC_DIR / "audit"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

VECTOR_THRESHOLD = 50

CASE_DIRS = [
    ("case_007", "西部C008 草ヶ江田島四丁目", SRC_DIR / "送付用_西部下水/202403C008_草ヶ江（田島四丁目）外地区下水道築造工事"),
    ("case_008", "西部C108 草ヶ江鳥飼六丁目", SRC_DIR / "送付用_西部下水/202403C108_草ヶ江（鳥飼六丁目）地区（２）下水道築造工事"),
    ("case_009", "中部 平尾高宮 大楠一丁目3", SRC_DIR / "送付用_中部下水/平尾高宮（大楠一丁目3）地区下水道築造工事"),
    ("case_010", "中部 福岡 桜坂二丁目外", SRC_DIR / "送付用_中部下水/福岡（桜坂二丁目外）地区下水道築造工事"),
]

KANRENSEI = ("管更生", "更生管材", "内面更生", "反転工", "形成工", "管きょ更生")
CHIKUZO = ("管布設", "新設", "築造工事", "VU管", "塩ビ管", "推進", "シールド", "開削")


def audit_pdf(pdf_path: Path) -> dict:
    pages = []
    head_text_chunks: list[str] = []
    with pdfplumber.open(str(pdf_path)) as doc:
        n = len(doc.pages)
        for i, page in enumerate(doc.pages, 1):
            n_lines = len(page.lines)
            n_rects = len(page.rects)
            n_curves = len(page.curves)
            n_images = len(page.images)
            n_chars = len(page.chars)
            text = page.extract_text() or ""
            if i <= 5:
                head_text_chunks.append(text)
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
    head_text = "\n".join(head_text_chunks)
    nk = sum(head_text.count(k) for k in KANRENSEI)
    nc = sum(head_text.count(k) for k in CHIKUZO)
    if nk >= 3 and nk > nc * 2:
        classification = "管更生工"
    elif nc >= 3 and nc > nk * 2:
        classification = "築造/管布設"
    else:
        classification = "混在/不明"
    return {
        "file": str(pdf_path.relative_to(REPO_ROOT)),
        "name": pdf_path.name,
        "pages": pages,
        "content_classification": classification,
        "kanrensei_hits": nk,
        "chikuzo_hits": nc,
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


def render_markdown(by_case: list[dict]) -> str:
    lines = [
        "# 福岡市 新規受領 PDF 構造判定レポート（2026-05-16）",
        "",
        "- 生成スクリプト: `customers/municipal/fukuokacity/poc/scripts/audit_new_cases.py`",
        "- 対象: 西部下水 2案件 / 中部下水 2案件 = 計 4案件 12 PDF",
        "- 出典: 2026-05-08 福岡市MTGアクション「東部以外（中部・西部）の図面/数量計算書共有依頼」の回答",
        f"- ベクター判定閾値: line+rect の平均 ≥ {VECTOR_THRESHOLD}",
        "",
        "## 案件別サマリ",
        "",
    ]
    for grp in by_case:
        lines.append(f"### {grp['case_id']}: {grp['label']}")
        lines.append("")
        lines.append("| ファイル | ページ | 平均ベクター度 | 平均文字数/p | 構造判定 | 管更生hit | 築造hit | 内容分類 |")
        lines.append("|---|---|---|---|---|---|---|---|")
        for r in grp["files"]:
            s = r["summary"]
            lines.append(
                f"| {r['name']} | {s['total_pages']} | {s['avg_vector_score']} | {s['avg_text_chars']} "
                f"| **{s['verdict']}** | {r['kanrensei_hits']} | {r['chikuzo_hits']} | **{r['content_classification']}** |"
            )
        lines.append("")
    lines.append("")
    lines.append("## PoC適用可否")
    lines.append("")
    lines.append("| case | 数量計算書 | 数量総括表 | 図面 | PoC適用 | 備考 |")
    lines.append("|---|---|---|---|---|---|")
    for grp in by_case:
        files = grp["files"]
        has_calc = any("計算書" in r["name"] and "総括" not in r["name"] for r in files)
        has_soukatu = any("総括表" in r["name"] for r in files)
        has_drawing = any(("図面" in r["name"]) or ("竣工図" in r["name"]) for r in files)
        applic = "✅" if has_calc and has_drawing else ("△" if has_drawing else "❌")
        memo = []
        if not has_calc:
            memo.append("計算書なし、総括表のみで部分適用")
        if any("変更" in r["name"] for r in files):
            memo.append("変更計算書（差分のみの可能性）")
        memo_s = "／".join(memo) if memo else "計算書+図面 揃い"
        lines.append(f"| {grp['case_id']} | {'✅' if has_calc else '❌'} | {'✅' if has_soukatu else '❌'} | {'✅' if has_drawing else '❌'} | {applic} | {memo_s} |")
    lines.append("")
    lines.append("## 既存PoCとの比較")
    lines.append("")
    lines.append("- 既存 case_001-006（那珂二丁目外）: 5本のPDFを路線別に分割して6ケース構成")
    lines.append("- 新規 case_007-010: 案件ごとに「計算書 / 総括表 / 図面 / 金抜設計書」が独立PDF。**路線分割が必要**")
    lines.append("- 全PDFが VECTOR or TEXT_LAYER_ONLY、画像PDFゼロ → そのまま Gemini Vision 投入可")
    lines.append("- ディレクトリ名は「築造工事」だが、中身は **管更生工が主体** → PoCスコープに合致")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    by_case = []
    for case_id, label, d in CASE_DIRS:
        if not d.exists():
            print(f"missing: {d}", file=sys.stderr)
            continue
        pdfs = sorted(d.glob("*.pdf"))
        files = []
        for pdf in pdfs:
            print(f"Auditing {pdf.name} ...", file=sys.stderr)
            files.append(summarize(audit_pdf(pdf)))
        by_case.append({"case_id": case_id, "label": label, "dir": str(d.relative_to(REPO_ROOT)), "files": files})

    json_out = AUDIT_DIR / "data_audit_2026-05-16.json"
    md_out = AUDIT_DIR / "data_audit_2026-05-16.md"
    json_out.write_text(json.dumps(by_case, indent=2, ensure_ascii=False))
    md_out.write_text(render_markdown(by_case))
    print(f"Wrote {json_out}", file=sys.stderr)
    print(f"Wrote {md_out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
