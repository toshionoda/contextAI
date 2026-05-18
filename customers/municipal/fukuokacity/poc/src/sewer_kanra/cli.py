"""CLI エントリポイント。

例:
  python -m sewer_kanra extract-calc           # 計算書抽出（全ケース）
  python -m sewer_kanra extract-drawing        # 図面抽出
  python -m sewer_kanra aggregate              # 数量総括表 集計
  python -m sewer_kanra check                  # 整合性チェック
  python -m sewer_kanra eval                   # GT 突合 F1
  python -m sewer_kanra all                    # 上記をパイプライン実行（全ケース）
  python -m sewer_kanra all --case case_001    # 単一ケース
"""
from __future__ import annotations

import argparse
import logging
import sys

from . import paths
from .gemini_client import setup_logging

logger = logging.getLogger(__name__)


def cmd_extract_calc(args: argparse.Namespace) -> int:
    from . import extract_calc_book
    from .gemini_client import GeminiClient

    knowledge = paths.KNOWLEDGE_FILE.read_text()
    client = GeminiClient()
    targets = [(args.case, dict(paths.CASES)[args.case])] if args.case else paths.CASES
    k = getattr(args, "k", 1)
    for case_id, route in targets:
        try:
            extract_calc_book.run_for_case(
                case_id, route, knowledge, client=client, self_consistency_k=k
            )
        except Exception as e:
            logger.error("extract-calc failed for %s: %s", case_id, e)
    return 0


def cmd_extract_drawing(args: argparse.Namespace) -> int:
    from . import extract_drawing
    from .gemini_client import GeminiClient

    knowledge = paths.KNOWLEDGE_FILE.read_text()
    client = GeminiClient()
    targets = [(args.case, dict(paths.CASES)[args.case])] if args.case else paths.CASES
    k = getattr(args, "k", 1)
    for case_id, route in targets:
        try:
            extract_drawing.run_for_case(
                case_id, route, knowledge, client=client, self_consistency_k=k
            )
        except Exception as e:
            logger.error("extract-drawing failed for %s: %s", case_id, e)
    return 0


def cmd_aggregate(args: argparse.Namespace) -> int:
    import yaml
    import pandas as pd
    from .aggregate_soukatu import aggregate, load_extracted_calc_books, write_outputs

    schema = yaml.safe_load(paths.SOUKATU_SCHEMA.read_text())
    docs = load_extracted_calc_books()
    if not docs:
        logger.error("計算書JSONが見つかりません。先に extract-calc を実行してください。")
        return 1
    df = aggregate(docs, schema)
    write_outputs(df, paths.RESULTS_DIR / "_summary")
    print(f"集計件数: {len(df)} / 入力ケース: {len(docs)}")
    print(df.head(20).to_string(index=False))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    from .consistency_check import check_case
    import json
    use_llm = getattr(args, "llm_pair", False)
    targets = [(args.case, dict(paths.CASES)[args.case])] if args.case else paths.CASES
    overall = {"cases": []}
    for case_id, route in targets:
        rep = check_case(case_id, route, use_llm_pairing=use_llm)
        overall["cases"].append(rep)
        out = paths.case_results_dir(case_id) / "consistency_report.json"
        out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
        if "summary" in rep:
            s = rep["summary"]
            print(f"{case_id}({route}) F1={s['f1']:.3f} R={s['recall']:.3f} P={s['precision']:.3f}")
        else:
            print(f"{case_id}({route}) skipped: {rep.get('reason')}")
    sumdir = paths.RESULTS_DIR / "_summary"
    sumdir.mkdir(parents=True, exist_ok=True)
    (sumdir / "consistency_report_overall.json").write_text(json.dumps(overall, indent=2, ensure_ascii=False))
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    from .eval import evaluate_case
    import json
    targets = [args.case] if args.case else [c for c, _ in paths.CASES]
    summary = {"cases": [], "overall": {}}
    f1s, ps, rs = [], [], []
    for c in targets:
        rep = evaluate_case(c)
        if rep is None:
            print(f"{c} : GT or 抽出結果なし、スキップ")
            continue
        summary["cases"].append(rep)
        (paths.case_results_dir(c) / "eval_report.json").write_text(
            json.dumps(rep, indent=2, ensure_ascii=False)
        )
        f1s.append(rep["f1"]); ps.append(rep["precision"]); rs.append(rep["recall"])
        print(f"{c} F1={rep['f1']:.3f} P={rep['precision']:.3f} R={rep['recall']:.3f}")
    if f1s:
        summary["overall"] = {
            "macro_f1": round(sum(f1s) / len(f1s), 3),
            "macro_precision": round(sum(ps) / len(ps), 3),
            "macro_recall": round(sum(rs) / len(rs), 3),
            "n_cases": len(f1s),
        }
        print(f"Macro F1={summary['overall']['macro_f1']:.3f}")
    sumdir = paths.RESULTS_DIR / "_summary"
    sumdir.mkdir(parents=True, exist_ok=True)
    (sumdir / "eval_overall.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


def cmd_all(args: argparse.Namespace) -> int:
    """一括パイプライン実行: extract-calc → extract-drawing → aggregate → check → eval"""
    rc = cmd_extract_calc(args)
    if rc:
        logger.warning("extract-calc returned %d, continuing", rc)
    rc = cmd_extract_drawing(args)
    if rc:
        logger.warning("extract-drawing returned %d, continuing", rc)
    cmd_aggregate(args)
    cmd_check(args)
    cmd_eval(args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sewer_kanra")
    sub = p.add_subparsers(dest="command", required=True)

    def common(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--case", help="単一ケース指定 (case_001..006)")

    def extract_opts(sp: argparse.ArgumentParser) -> None:
        sp.add_argument(
            "--k",
            type=int,
            default=1,
            help="Self-Consistency サンプル数 (推奨 3、デフォルト 1=単発)",
        )

    sp1 = sub.add_parser("extract-calc", help="数量計算書PDF→JSON")
    common(sp1); extract_opts(sp1); sp1.set_defaults(func=cmd_extract_calc)

    sp2 = sub.add_parser("extract-drawing", help="図面PDF→JSON")
    common(sp2); extract_opts(sp2); sp2.set_defaults(func=cmd_extract_drawing)

    sp3 = sub.add_parser("aggregate", help="L2-L3-L4 集計")
    common(sp3); sp3.set_defaults(func=cmd_aggregate)

    sp4 = sub.add_parser("check", help="計算書 vs 図面 整合性チェック")
    common(sp4)
    sp4.add_argument(
        "--llm-pair", action="store_true",
        help="LLMによる対話型ペアリング（Tier A3）。同義語辞書とLLMでマッチング",
    )
    sp4.set_defaults(func=cmd_check)

    sp5 = sub.add_parser("eval", help="GT 突合 F1/再現率/適合率")
    common(sp5); sp5.set_defaults(func=cmd_eval)

    sp6 = sub.add_parser("all", help="一括パイプライン実行")
    common(sp6); extract_opts(sp6); sp6.set_defaults(func=cmd_all)

    return p


def main() -> int:
    setup_logging()
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
