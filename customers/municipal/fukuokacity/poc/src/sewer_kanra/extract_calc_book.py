"""数量計算書PDF → 路線×L2/L3/L4×規格×単位×数量 の構造化JSON抽出。

Gemini Vision にPDFを投入し、knowledge_sewer_kanra.md を背景知識としてJSONを取り出す。
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

from . import paths
from .gemini_client import GeminiClient, self_consistency_generate, setup_logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Few-shot examples (Tier A: A1)
# 既存の case_002, case_003 の GT をテキストで埋め込み、出力スコープを範例で示す。
# ---------------------------------------------------------------------------
FEW_SHOT_EXAMPLES = """\
# Few-shot 範例（必ずこの形式に従う）

## 範例1: case_002（路線 430-3、既設管渠φ300、管きょ延長 33.90m、取付管5箇所）

入力PDF: 路線430-3 の数量計算書（共通仮設費・付帯工なども記載されているが **抽出対象外**）

期待出力:
```json
{
  "route": "430-3",
  "items": [
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "路線延長（φ300）", "単位": "m", "数量": 62.80,
     "備考": "数量総括表 φ300 路線延長 62.80m は 430-3 と 410-1-3 の合計（case_002単体 34.80m）"},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "管きょ延長（φ300）", "単位": "m", "数量": 33.90},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生管材", "規格": "更生自立管", "単位": "m", "数量": 34.80},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "内面更生工", "規格": "反転・引込工 硬化・形成工", "単位": "m", "数量": 33.90},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "仮設備設置・撤去工", "単位": "回", "数量": 1},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "本管口切断工 本管口仕上工", "単位": "箇所", "数量": 2},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "取付管口せん孔仕上工", "単位": "箇所", "数量": 5}
  ]
}
```

## 範例2: case_003（路線 410-1-3、既設管渠φ300、管きょ延長 27.10m、取付管4箇所）

期待出力:
```json
{
  "route": "410-1-3",
  "items": [
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "路線延長（φ300）", "単位": "m", "数量": 28.00},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "管きょ延長（φ300）", "単位": "m", "数量": 27.10},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生管材", "規格": "更生自立管", "単位": "m", "数量": 28.00},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "内面更生工", "規格": "反転・引込工 硬化・形成工", "単位": "m", "数量": 27.10},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "仮設備設置・撤去工", "単位": "回", "数量": 1},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "本管口切断工 本管口仕上工", "単位": "箇所", "数量": 2},
    {"L2": "管きょ更生工", "L3": "既設管渠300mm", "L4": "更生付帯工", "規格": "取付管口せん孔仕上工", "単位": "箇所", "数量": 4}
  ]
}
```

## 範例から学ぶスコープ規則（最重要）

- 範例1のPDFには「管内洗浄工 / 本管TV調査工 / 掘削 / 埋戻 / 小口径汚水桝 / 鉄蓋 / 舗装版切断 / 既設管撤去」なども記載されているが、**出力には1件も含まれていない**
- 抽出対象は **L2='管きょ更生工'** の 7項目程度。それ以外の L2 は **絶対に出力しない**
- 取付管口せん孔仕上工の「数量」は **取付管本数** と一致する（例: 5箇所 = 取付管5本）
"""


CALC_BOOK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "route": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "L2": {"type": "string"},
                    "L3": {"type": "string"},
                    "L4": {"type": "string"},
                    "規格": {"type": "string"},
                    "単位": {"type": "string"},
                    "数量": {"type": "number"},
                    "備考": {"type": "string"},
                    "source": {
                        "type": "object",
                        "properties": {
                            "page": {"type": "integer"},
                            "bbox": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4,
                            },
                        },
                    },
                },
                "required": ["L2", "L4", "単位", "数量"],
            },
        },
    },
    "required": ["route", "items"],
}


PROMPT_TEMPLATE = """\
あなたは下水道改築工事（管更生工）の数量計算書を読み取るアシスタントです。

以下の知識を背景として用いて、添付PDFに記載されている **路線 {expected_route}** の数量計算情報を JSON で構造化してください。

# 知識（必読）
{knowledge}

# 思考手順（Chain-of-Thought / 出力前の内部処理）

以下の順序で読み取りを行ってから JSON を生成してください（思考過程は出力に含めない）：

1. **路線の特定**: 表題欄・整理番号・吹き出しから expected_route と一致する路線を特定
2. **管径の判別**: 該当路線の既設管渠管径（φ250/φ300/φ150 等）を確認
3. **L2='管きょ更生工'のフィルタ**: 計算書PDFを読み、L2='管きょ更生工' の節（管きょ更生工 / 更生管材 / 内面更生工 / 更生付帯工 / 換気工）に該当する行 **だけ** を候補に絞る
4. **除外節の確認**: 共通仮設費・管布設工・管路土工・取付管およびます工・マンホール工・付帯工・スクラップ費 の節は **読み飛ばす**
5. **数量と規格の転記**: 各候補行から L4（細別）・規格・単位・数量 を計算書記載通り転記
6. **件数チェック**: 通常 6〜8 項目に収まる（範例参照）。20件超は除外節を拾い間違えているサイン

{few_shot}

# 出力ルール

- 路線番号は半角ハイフン区切り（例: 429-2）。expected_route と必ず一致させる
- 数量は計算書記載の値そのまま（丸めない）
- 単位は §unit_aliases の正規化前の表記（記載通り）でOK
- L2/L3/L4 は知識 §0 / §4 の体系に従う
- **L2='管きょ更生工' 以外は絶対に出力しない**（知識 §0 のスコープ規則）
- 「路線延長」「管きょ延長」は L2=管きょ更生工 / L3=（既設管渠の管径ごと） / L4=路線延長 or 管きょ延長 と扱う
- 見つからない項目は出力しない（推測しない）
- `備考` は計算書に記載がある場合のみ

# 出典情報（source）の付与ルール
各 items 項目に、可能な限り **source** を付けてください。
- `source.page`: その項目（数量行）が記載されているページ番号（**1-indexed**、計算書PDFは複数ページなのでページ番号は重要）
- `source.bbox`: ページ画像内での該当行の境界ボックス。`[ymin, xmin, ymax, xmax]` の4要素配列で、**0-1000 に正規化**（左上が (0, 0)、右下が (1000, 1000)）
- bbox はその数量行（L4 や 数量 セルを含む行全体）を囲む矩形を推奨
- 行の場所が特定できない場合は `source` を省略可（必須ではない）

# 期待する JSON スキーマ
```json
{schema}
```
"""


def _build_prompt(expected_route: str, knowledge: str, with_few_shot: bool = True) -> str:
    return PROMPT_TEMPLATE.format(
        expected_route=expected_route,
        knowledge=knowledge,
        few_shot=FEW_SHOT_EXAMPLES if with_few_shot else "",
        schema=json.dumps(CALC_BOOK_SCHEMA, indent=2, ensure_ascii=False),
    )


def extract(
    pdf_path: Path,
    expected_route: str,
    knowledge: str,
    client: GeminiClient | None = None,
    self_consistency_k: int = 1,
    with_few_shot: bool = True,
) -> dict:
    """計算書PDFから構造化JSONを抽出する。

    Args:
        self_consistency_k: 1 なら単発呼び出し。2 以上なら k 回呼び出し→多数決でアイテムをフィルタ
        with_few_shot: Few-shot 範例をプロンプトに含めるか
    """
    client = client or GeminiClient()
    prompt = _build_prompt(expected_route, knowledge, with_few_shot=with_few_shot)

    if self_consistency_k <= 1:
        result = client.generate_json(
            prompt=prompt, pdf_path=pdf_path, response_schema=CALC_BOOK_SCHEMA
        )
        payload = result.parse_json()
        payload["_meta"] = {"model": result.model, "elapsed_s": round(result.elapsed_s, 2)}
        return payload

    # Self-Consistency パス（Tier A: A4）
    payload, _votes = self_consistency_generate(
        client=client,
        prompt=prompt,
        pdf_path=pdf_path,
        response_schema=CALC_BOOK_SCHEMA,
        list_key="items",
        item_keys=("L2", "L3", "L4", "規格", "単位", "数量"),
        k=self_consistency_k,
        min_votes=max(2, (self_consistency_k // 2) + 1),
        base_temperature=0.2,
    )
    payload["_meta"] = {
        "model": payload.get("_self_consistency", {}).get("models", ["?"])[0],
        "elapsed_s": payload.get("_self_consistency", {}).get("elapsed_s_total", 0.0),
    }
    return payload


def run_for_case(
    case_id: str,
    route: str,
    knowledge: str,
    client: GeminiClient | None = None,
    self_consistency_k: int = 1,
) -> dict | None:
    pdf = paths.case_calc_pdf(case_id)
    if pdf is None:
        logger.warning("No calc PDF for %s", case_id)
        return None
    logger.info(
        "Extract calc_book: %s (%s) <- %s (k=%d)", case_id, route, pdf.name, self_consistency_k
    )
    payload = extract(
        pdf, route, knowledge, client=client, self_consistency_k=self_consistency_k
    )
    out = paths.case_results_dir(case_id) / "extracted_calc_book.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", out)
    return payload


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="case_001..006 を指定。省略時は全件")
    parser.add_argument("--dry-run", action="store_true", help="API を叩かずプロンプトだけ出力")
    parser.add_argument(
        "--k",
        type=int,
        default=int(os.environ.get("SELF_CONSISTENCY_K", "1")),
        help="Self-Consistency サンプル数 (1=単発、推奨 3)",
    )
    parser.add_argument(
        "--no-few-shot", action="store_true", help="Few-shot 範例を含めない（ablation 用）"
    )
    args = parser.parse_args()

    knowledge = paths.KNOWLEDGE_FILE.read_text()

    if args.dry_run:
        case_id, route = paths.CASES[0]
        pdf = paths.case_calc_pdf(case_id)
        prompt = _build_prompt(route, knowledge, with_few_shot=not args.no_few_shot)
        print(f"# DRY RUN\n# Case: {case_id} ({route})\n# PDF: {pdf}\n# k: {args.k}\n\n--- PROMPT ---\n{prompt}")
        return 0

    targets = [(args.case, dict(paths.CASES)[args.case])] if args.case else paths.CASES
    client = GeminiClient()
    for case_id, route in targets:
        try:
            run_for_case(case_id, route, knowledge, client=client, self_consistency_k=args.k)
        except Exception as e:
            logger.error("Failed %s: %s", case_id, e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
