"""ground_truth.json と extracted_calc_book.json を突合して F1/再現率/適合率を算出。

GT は detected_items（symbol/value/unit/category）の形式。
extracted_calc_book.json は items（L2/L3/L4/規格/単位/数量）の形式。

照合ロジック:
- GT 各項目に対し、抽出側の items を「単位」と「数値」と「カテゴリ近似」でマッチング
- カテゴリの一致は L4/L3/L2 の文字列に GT category のキーワードが含まれるかで判定
- 数値マッチは abs_tol=0.01 / rel_tol=1%
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from . import paths
from .consistency_check import is_close, parse_num
from .gemini_client import setup_logging

logger = logging.getLogger(__name__)


def keywords(text: str) -> list[str]:
    if not text:
        return []
    return re.split(r"[\s/／・,，()（）]+", text)


def category_match(gt_cat: str, item: dict) -> bool:
    if not gt_cat:
        return False
    haystack = " ".join([str(item.get("L2", "")), str(item.get("L3", "")), str(item.get("L4", "")), str(item.get("規格", ""))])
    # GT category の主要キーワードがいずれか含まれていればマッチ
    for kw in keywords(gt_cat):
        if len(kw) >= 2 and kw in haystack:
            return True
    return False


def evaluate_case(case_id: str) -> dict | None:
    gt_path = paths.case_ground_truth(case_id)
    pred_path = paths.case_results_dir(case_id) / "extracted_calc_book.json"
    if gt_path is None or not pred_path.exists():
        return None

    gt = json.loads(gt_path.read_text())
    pred = json.loads(pred_path.read_text())

    gt_items = gt.get("detected_items", [])
    pred_items = pred.get("items", [])

    used_pred: set[int] = set()
    matches: list[dict] = []
    fn: list[dict] = []
    for g in gt_items:
        g_val = parse_num(g.get("value"))
        g_unit = (g.get("unit") or "").strip()
        g_cat = g.get("category", "")
        best = None
        best_idx = -1
        for i, p in enumerate(pred_items):
            if i in used_pred:
                continue
            p_val = parse_num(p.get("数量"))
            p_unit = (p.get("単位") or "").strip()
            if p_val is None or g_val is None:
                continue
            if p_unit and g_unit and p_unit != g_unit:
                # 単位ミスマッチは弱マッチ（カテゴリ一致なら許容）
                if not category_match(g_cat, p):
                    continue
            if not is_close(g_val, p_val):
                continue
            if not category_match(g_cat, p):
                continue
            best = p
            best_idx = i
            break
        if best is not None:
            matches.append({"gt": g, "pred": best})
            used_pred.add(best_idx)
        else:
            fn.append(g)
    fp = [p for i, p in enumerate(pred_items) if i not in used_pred]

    n_gt = len(gt_items)
    n_pred = len(pred_items)
    tp = len(matches)
    recall = tp / n_gt if n_gt else 0.0
    precision = tp / n_pred if n_pred else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "case_id": case_id,
        "n_gt": n_gt,
        "n_pred": n_pred,
        "tp": tp,
        "fp_count": len(fp),
        "fn_count": len(fn),
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "false_negatives": fn,
        "false_positives": fp,
        "matches": matches,
    }


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="単一ケース実行。省略時は全件")
    args = parser.parse_args()

    targets = [args.case] if args.case else [c for c, _ in paths.CASES]
    summary = {"cases": [], "overall": {}}
    macro_f1 = []
    macro_p = []
    macro_r = []
    for case_id in targets:
        rep = evaluate_case(case_id)
        if rep is None:
            print(f"{case_id} : GT or 抽出結果なし、スキップ")
            continue
        summary["cases"].append(rep)
        out = paths.case_results_dir(case_id) / "eval_report.json"
        out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
        macro_f1.append(rep["f1"])
        macro_p.append(rep["precision"])
        macro_r.append(rep["recall"])
        print(f"{case_id} F1={rep['f1']:.3f} P={rep['precision']:.3f} R={rep['recall']:.3f} (TP={rep['tp']}/GT={rep['n_gt']}, Pred={rep['n_pred']})")

    if macro_f1:
        summary["overall"] = {
            "macro_f1": round(sum(macro_f1) / len(macro_f1), 3),
            "macro_precision": round(sum(macro_p) / len(macro_p), 3),
            "macro_recall": round(sum(macro_r) / len(macro_r), 3),
            "n_cases": len(macro_f1),
        }
        print(f"\nMacro F1={summary['overall']['macro_f1']:.3f} P={summary['overall']['macro_precision']:.3f} R={summary['overall']['macro_recall']:.3f} ({summary['overall']['n_cases']} cases)")

    sumdir = paths.RESULTS_DIR / "_summary"
    sumdir.mkdir(parents=True, exist_ok=True)
    (sumdir / "eval_overall.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
