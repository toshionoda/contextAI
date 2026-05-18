"""計算書側の数量と図面側の検出値を突合し、整合性レポートを生成する。

Tier A3 改善:
- 同義工種グルーピング（路線延長／管きょ延長／更生管材／内面更生工 を1クラスタに集約）
- グループ内の代表値とのマッチング（最大延長＝路線延長 と図面側の延長を照合）
- LLM対話型ペアリング（--llm-pair / use_llm_pairing=True）：
  計算書JSON と 図面JSON を両方Geminiに渡し、同一物体を指す項目をペアリングさせる

将来拡張:
- 管径・勾配・荷重区分のマッチング
- マンホール本数の整合性
- 取付管口本数 ↔ 図面取付管記号
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any

from . import paths
from .gemini_client import GeminiClient, setup_logging

logger = logging.getLogger(__name__)


NUM_RE = re.compile(r"[-+]?\d*\.?\d+")

# 計算書側で「同じ路線の延長」を指す同義工種（L4ベース）
LENGTH_SYNONYM_KEYWORDS: tuple[str, ...] = (
    "路線延長",
    "管きょ延長",
    "更生管材",
    "内面更生工",
)

# 図面側で「延長」を表す category
DRAWING_LENGTH_CATEGORIES: tuple[str, ...] = (
    "延長",
    "管きょ延長",
    "路線延長",
)


def parse_num(s: str | float | None) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = NUM_RE.search(str(s))
    return float(m.group(0)) if m else None


def is_close(a: float, b: float, abs_tol: float = 0.01, rel_tol: float = 0.01) -> bool:
    if a == b:
        return True
    diff = abs(a - b)
    return diff <= abs_tol or diff <= rel_tol * max(abs(a), abs(b))


def _extract_calc_lengths(calc: dict) -> list[dict]:
    """計算書JSONから延長系の項目を抽出（個別アイテム）。"""
    out: list[dict] = []
    for item in calc.get("items", []) or []:
        unit = item.get("単位", "")
        l4 = item.get("L4", "") or ""
        if unit == "m" and any(k in l4 for k in LENGTH_SYNONYM_KEYWORDS):
            v = parse_num(item.get("数量"))
            if v is not None:
                out.append({**item, "数量_num": v})
    return out


def _group_calc_lengths(calc_lengths: list[dict]) -> list[dict]:
    """同義工種の延長群を「数値クラスタ」に集約する（Tier A3）。

    同じ路線で出現する延長は通常2系統:
      - 路線延長（管路センター長）= 更生管材 = 概ね同値
      - 管きょ延長（内面更生対象長）= 内面更生工 = 概ね同値（路線延長より約0.9m短い）

    abs_tol=0.5m / rel_tol=5% で同一クラスタとする。
    """
    clusters: list[dict] = []
    for item in calc_lengths:
        v = item["数量_num"]
        placed = False
        for cl in clusters:
            if is_close(v, cl["representative"], abs_tol=0.5, rel_tol=0.05):
                cl["members"].append(item)
                # 代表値は最大値（路線延長＝総延長を取る）
                if v > cl["representative"]:
                    cl["representative"] = v
                placed = True
                break
        if not placed:
            clusters.append({"representative": v, "members": [item]})

    # 整形
    return [
        {
            "representative_value": round(cl["representative"], 3),
            "members": cl["members"],
            "categories": sorted({m.get("L4", "") for m in cl["members"]}),
        }
        for cl in clusters
    ]


def _extract_drawing_lengths(drw: dict) -> list[dict]:
    out: list[dict] = []
    for dv in drw.get("detected_values", []) or []:
        if dv.get("category") in DRAWING_LENGTH_CATEGORIES:
            v = parse_num(dv.get("value"))
            if v is not None:
                out.append({**dv, "value_num": v})
    return out


def check_payloads(
    calc: dict,
    drw: dict,
    case_id: str = "upload",
    route: str = "",
    use_grouping: bool = True,
) -> dict:
    """計算書JSONと図面JSONを突合して整合性レポートを生成する。

    Args:
        use_grouping: True なら同義工種グルーピング後に照合（Tier A3）
    """
    calc_lengths = _extract_calc_lengths(calc)
    drw_lengths = _extract_drawing_lengths(drw)

    if not use_grouping:
        # 旧ロジック（個別アイテム × 図面側）
        return _check_per_item(calc_lengths, drw_lengths, case_id, route)

    # Tier A3: 同義工種グルーピング後の代表値マッチング
    clusters = _group_calc_lengths(calc_lengths)
    matches: list[dict] = []
    unmatched_clusters: list[dict] = []
    used_drw: set[int] = set()

    for cl in clusters:
        cl_v = cl["representative_value"]
        best_idx = -1
        best_diff = float("inf")
        for i, d in enumerate(drw_lengths):
            if i in used_drw:
                continue
            if is_close(cl_v, d["value_num"], abs_tol=0.5, rel_tol=0.05):
                diff = abs(cl_v - d["value_num"])
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i
        if best_idx >= 0:
            matches.append({"calc_cluster": cl, "drawing": drw_lengths[best_idx]})
            used_drw.add(best_idx)
        else:
            unmatched_clusters.append(cl)

    unmatched_drw = [d for i, d in enumerate(drw_lengths) if i not in used_drw]

    n_clusters = len(clusters)
    n_match = len(matches)
    recall = n_match / n_clusters if n_clusters else 0.0
    precision = n_match / len(drw_lengths) if drw_lengths else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "case_id": case_id,
        "route": route,
        "method": "synonym_grouping",
        "summary": {
            "calc_length_items": len(calc_lengths),
            "calc_clusters": n_clusters,
            "drawing_length_items": len(drw_lengths),
            "matched": n_match,
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "f1": round(f1, 3),
        },
        "matches": matches,
        "unmatched_calc_clusters": unmatched_clusters,
        "unmatched_drawing": unmatched_drw,
    }


def _check_per_item(
    calc_lengths: list[dict], drw_lengths: list[dict], case_id: str, route: str
) -> dict:
    """旧ロジック（個別アイテム × 図面側）。比較・回帰用に保持。"""
    matches: list[dict] = []
    unmatched_calc: list[dict] = []
    used_drw: set[int] = set()
    for c in calc_lengths:
        best = None
        best_idx = -1
        for i, d in enumerate(drw_lengths):
            if i in used_drw:
                continue
            if is_close(c["数量_num"], d["value_num"]):
                if best is None or abs(c["数量_num"] - d["value_num"]) < abs(
                    c["数量_num"] - best["value_num"]
                ):
                    best = d
                    best_idx = i
        if best is not None:
            matches.append({"calc": c, "drawing": best})
            used_drw.add(best_idx)
        else:
            unmatched_calc.append(c)
    unmatched_drw = [d for i, d in enumerate(drw_lengths) if i not in used_drw]

    n_calc = len(calc_lengths)
    n_match = len(matches)
    recall = n_match / n_calc if n_calc else 0.0
    precision = n_match / len(drw_lengths) if drw_lengths else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "case_id": case_id,
        "route": route,
        "method": "per_item",
        "summary": {
            "calc_length_items": n_calc,
            "drawing_length_items": len(drw_lengths),
            "matched": n_match,
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "f1": round(f1, 3),
        },
        "matches": matches,
        "unmatched_calc": unmatched_calc,
        "unmatched_drawing": unmatched_drw,
    }


# ---------------------------------------------------------------------------
# LLM 対話型ペアリング (Tier A3 拡張)
# ---------------------------------------------------------------------------
LLM_PAIRING_PROMPT = """\
あなたは下水道改築工事の整合性チェックを行うアシスタントです。

以下に、同じ路線 **{route}** の「数量計算書から抽出したアイテム」と「図面から抽出した値」を渡します。
**同一の物理対象を指している項目をペアリング** してください。

# 照合のルール（重要）

- 「路線延長 = 更生管材」「管きょ延長 = 内面更生工」は同じ路線の延長を別工種で計上したもの。**代表的な数値クラスタを単一の物理対象**として扱う
- 図面側の「延長 L=X.XXm」は計算書の「路線延長」「管きょ延長」と一致する想定
- 取付管口せん孔の本数（箇所）は、図面側の「取付管」マンホール記号の本数と一致する想定
- マンホール（人孔）本数も照合候補
- 数値の許容差: 絶対0.5m or 相対5%（マンホール芯〜内寸の差を許容）

# 出力スキーマ

```json
{{
  "pairs": [
    {{
      "calc_indices": [int, ...],   // calc.items のインデックス（複数可：同義工種を束ねる）
      "drawing_indices": [int, ...], // drawing.detected_values のインデックス（複数可）
      "subject": "string",          // 例: "路線延長 φ250 = 18.10m"
      "confidence": "high|medium|low"
    }}
  ],
  "calc_unmatched": [int, ...],
  "drawing_unmatched": [int, ...],
  "notes": "string"  // 不一致や所見
}}
```

# 入力

## 計算書 items
```json
{calc_items}
```

## 図面 detected_values
```json
{drawing_values}
```
"""


LLM_PAIRING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "calc_indices": {"type": "array", "items": {"type": "integer"}},
                    "drawing_indices": {"type": "array", "items": {"type": "integer"}},
                    "subject": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                },
                "required": ["calc_indices", "drawing_indices", "subject", "confidence"],
            },
        },
        "calc_unmatched": {"type": "array", "items": {"type": "integer"}},
        "drawing_unmatched": {"type": "array", "items": {"type": "integer"}},
        "notes": {"type": "string"},
    },
    "required": ["pairs"],
}


def check_with_llm_pairing(
    calc: dict,
    drw: dict,
    case_id: str = "upload",
    route: str = "",
    client: GeminiClient | None = None,
) -> dict:
    """LLM対話型ペアリング。計算書全体 × 図面全体を Gemini に渡してペアリングさせる。

    confidence=high のペアだけを採用し、F1 を計算する。
    """
    client = client or GeminiClient()
    calc_items = calc.get("items", []) or []
    drw_values = drw.get("detected_values", []) or []

    if not calc_items or not drw_values:
        return {
            "case_id": case_id,
            "route": route,
            "skipped": True,
            "reason": "calc.items or drawing.detected_values empty",
        }

    prompt = LLM_PAIRING_PROMPT.format(
        route=route,
        calc_items=json.dumps(calc_items, ensure_ascii=False, indent=2),
        drawing_values=json.dumps(drw_values, ensure_ascii=False, indent=2),
    )
    result = client.generate_json(
        prompt=prompt, pdf_path=None, response_schema=LLM_PAIRING_SCHEMA
    )
    pairing = result.parse_json()

    # F1 計算（high のみカウント）
    pairs = pairing.get("pairs", []) or []
    high_pairs = [p for p in pairs if p.get("confidence") == "high"]
    all_pairs = pairs

    # 計算書側の「ペアに参加した（high）」index 数 / 全 items を recall とする
    matched_calc_indices: set[int] = set()
    matched_drw_indices: set[int] = set()
    for p in high_pairs:
        matched_calc_indices.update(p.get("calc_indices", []))
        matched_drw_indices.update(p.get("drawing_indices", []))

    n_calc = len(calc_items)
    n_drw = len(drw_values)
    # 「計算書アイテムのうち何個がhighペアに含まれたか」を recall に
    recall = (len(matched_calc_indices) / n_calc) if n_calc else 0.0
    precision = (len(matched_drw_indices) / n_drw) if n_drw else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return {
        "case_id": case_id,
        "route": route,
        "method": "llm_pairing",
        "summary": {
            "calc_items_total": n_calc,
            "drawing_values_total": n_drw,
            "pairs_total": len(all_pairs),
            "pairs_high": len(high_pairs),
            "matched_calc_indices": sorted(matched_calc_indices),
            "matched_drawing_indices": sorted(matched_drw_indices),
            "recall": round(recall, 3),
            "precision": round(precision, 3),
            "f1": round(f1, 3),
        },
        "pairs": all_pairs,
        "calc_unmatched": pairing.get("calc_unmatched", []),
        "drawing_unmatched": pairing.get("drawing_unmatched", []),
        "notes": pairing.get("notes", ""),
        "_meta": {"model": result.model, "elapsed_s": round(result.elapsed_s, 2)},
    }


def check_case(case_id: str, route: str, use_llm_pairing: bool = False) -> dict:
    calc_path = paths.case_results_dir(case_id) / "extracted_calc_book.json"
    drw_path = paths.case_results_dir(case_id) / "extracted_drawing.json"
    if not calc_path.exists() or not drw_path.exists():
        return {
            "case_id": case_id,
            "route": route,
            "skipped": True,
            "reason": "extracted_calc_book.json or extracted_drawing.json missing",
        }

    calc = json.loads(calc_path.read_text())
    drw = json.loads(drw_path.read_text())

    if use_llm_pairing:
        return check_with_llm_pairing(calc, drw, case_id=case_id, route=route)
    return check_payloads(calc, drw, case_id=case_id, route=route, use_grouping=True)


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="単一ケース実行。省略時は全件")
    parser.add_argument(
        "--llm-pair",
        action="store_true",
        help="LLM対話型ペアリング（Tier A3）。計算書全体×図面全体を Gemini に渡す",
    )
    args = parser.parse_args()

    targets = [(args.case, dict(paths.CASES)[args.case])] if args.case else paths.CASES
    overall = {"cases": []}
    for case_id, route in targets:
        rep = check_case(case_id, route, use_llm_pairing=args.llm_pair)
        overall["cases"].append(rep)
        out = paths.case_results_dir(case_id) / "consistency_report.json"
        out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
        logger.info("Wrote %s", out)
        if "summary" in rep:
            s = rep["summary"]
            mtd = rep.get("method", "?")
            mt = s.get("matched", s.get("pairs_high", "?"))
            denom = s.get("calc_clusters", s.get("calc_length_items", s.get("calc_items_total", "?")))
            print(
                f"{case_id}({route}) [{mtd}] F1={s['f1']:.3f} R={s['recall']:.3f} P={s['precision']:.3f} matched={mt}/{denom}"
            )
        else:
            print(f"{case_id}({route}) skipped: {rep.get('reason')}")

    sumdir = paths.RESULTS_DIR / "_summary"
    sumdir.mkdir(parents=True, exist_ok=True)
    (sumdir / "consistency_report_overall.json").write_text(json.dumps(overall, indent=2, ensure_ascii=False))
    logger.info("Wrote consistency_report_overall.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
