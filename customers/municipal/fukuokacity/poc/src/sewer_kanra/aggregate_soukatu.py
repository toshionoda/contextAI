"""路線別の計算書JSONを横串で集計し、L2-L3-L4 の数量総括表を生成する。

入力:
  results/{case_id}/extracted_calc_book.json (route, items: [{L2,L3,L4,規格,単位,数量}])
出力:
  results/_summary/soukatu_aggregated.csv     # 集計結果
  results/_summary/soukatu_aggregated.json    # 同 JSON 版（後段比較用）

集計キー: (L2, L3, L4, 規格, 単位)
集計値: 数量の合計、寄与した路線の一覧
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd
import yaml

from . import paths
from .gemini_client import setup_logging

logger = logging.getLogger(__name__)


def load_extracted_calc_books() -> list[dict]:
    docs = []
    for case_id, route in paths.CASES:
        f = paths.case_results_dir(case_id) / "extracted_calc_book.json"
        if not f.exists():
            continue
        d = json.loads(f.read_text())
        d["_case_id"] = case_id
        d["_route"] = route
        docs.append(d)
    return docs


def normalize_unit(unit: str, alias_map: dict[str, list[str]]) -> str:
    if not unit:
        return unit
    for canon, aliases in alias_map.items():
        if unit in aliases or unit == canon:
            return canon
    return unit


def aggregate(docs: list[dict], schema: dict) -> pd.DataFrame:
    alias_map = schema.get("unit_aliases", {})
    rows = []
    for doc in docs:
        route = doc.get("route") or doc.get("_route")
        for item in doc.get("items", []):
            rows.append(
                {
                    "L2": item.get("L2"),
                    "L3": item.get("L3"),
                    "L4": item.get("L4"),
                    "規格": item.get("規格") or "",
                    "単位": normalize_unit(item.get("単位", ""), alias_map),
                    "数量": float(item.get("数量") or 0.0),
                    "route": route,
                }
            )
    if not rows:
        return pd.DataFrame(columns=["L2", "L3", "L4", "規格", "単位", "数量", "routes"])

    df = pd.DataFrame(rows)
    grouped = (
        df.groupby(["L2", "L3", "L4", "規格", "単位"], dropna=False)
        .agg(数量=("数量", "sum"), routes=("route", lambda s: sorted(set(s))))
        .reset_index()
    )
    return grouped.sort_values(["L2", "L3", "L4", "規格"]).reset_index(drop=True)


def write_outputs(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    csv = out_dir / "soukatu_aggregated.csv"
    js = out_dir / "soukatu_aggregated.json"
    df.to_csv(csv, index=False)
    df.to_json(js, orient="records", force_ascii=False, indent=2)
    logger.info("Wrote %s", csv)
    logger.info("Wrote %s", js)


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(paths.RESULTS_DIR / "_summary"))
    args = parser.parse_args()

    schema = yaml.safe_load(paths.SOUKATU_SCHEMA.read_text())
    docs = load_extracted_calc_books()
    if not docs:
        logger.error("extracted_calc_book.json が見つかりません。先に extract_calc_book.py を実行してください。")
        return 1
    df = aggregate(docs, schema)
    write_outputs(df, Path(args.out))

    # コンソールサマリ
    print(f"集計件数: {len(df)} 件 / 入力路線: {len(docs)}")
    print(df.head(20).to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
