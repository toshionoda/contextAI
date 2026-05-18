"""図面PDF → 路線ごとの図面記載数値の構造化JSON抽出。

Gemini Vision に図面PDFを投入し、平面・縦断・横断図に書かれている
「路線記号 / 管種 / 管径 / 勾配 / 延長 / 管底高 / 荷重区分 / 施工時間帯」を抽出。
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


# Few-shot examples (Tier A: A1)
FEW_SHOT_EXAMPLES = """\
# Few-shot 範例（必ずこの形式に従う）

## 範例1: case_002 図面（路線 430-3）

縦断図に「TPφ300」「i=10.5‰」「L=34.80m」「上流管底高 11.234」「下流管底高 10.870」、
平面図にマンホール「00112A-15」「00112A-16」、平面図凡例に「T-14 / 昼間施工 / 管更生」が記載されている場合：

期待出力:
```json
{
  "route": "430-3",
  "drawing_type": "平面図+縦断図",
  "scale": "S=1:300(A1) / V=1:100, H=1:300",
  "detected_values": [
    {"category": "管種", "value": "TP", "context": "TPφ300"},
    {"category": "管径", "value": "300", "unit": "mm", "context": "TPφ300"},
    {"category": "勾配", "value": "10.5", "unit": "‰", "context": "i=10.5‰"},
    {"category": "延長", "value": "34.80", "unit": "m", "context": "L=34.80m"},
    {"category": "上流管底高", "value": "11.234", "unit": "m", "context": "縦断図 起点側"},
    {"category": "下流管底高", "value": "10.870", "unit": "m", "context": "縦断図 終点側"},
    {"category": "荷重区分", "value": "T-14"},
    {"category": "施工時間帯", "value": "昼間施工"},
    {"category": "管更生工法", "value": "管更生"}
  ],
  "manholes": [
    {"id": "00112A-15", "type": "既設"},
    {"id": "00112A-16", "type": "既設"}
  ]
}
```

## 範例から学ぶ規則

- **延長 L はマンホール芯〜芯の数値**（計算書「路線延長」と一致）。複数記載がある場合は **代表値ではなく全部** detected_values に入れる
- **管径は数値のみ単位mmで分離**して `unit: "mm"` を付ける（"TPφ300" のような連結文字列だけでなく分解した値を返す）
- 取付管（Tφ150 等）が記載されていれば、それも detected_values に「管径」「150」「取付管」として記録する
- マンホール記号は `manholes` に列挙する（detected_values には入れない）
"""


DRAWING_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "route": {"type": "string"},
        "drawing_type": {"type": "string"},  # 平面図 / 縦断図 / 横断図 / 全体位置図
        "scale": {"type": "string"},
        "detected_values": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {"type": "string"},
                    "value": {"type": "string"},
                    "unit": {"type": "string"},
                    "context": {"type": "string"},
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
                "required": ["category", "value"],
            },
        },
        "manholes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "type": {"type": "string"},
                },
            },
        },
        "buried_utilities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kind": {"type": "string"},
                    "diameter": {"type": "string"},
                },
            },
        },
    },
    "required": ["route", "detected_values"],
}


PROMPT_TEMPLATE = """\
あなたは下水道工事の図面を読み取るアシスタントです。

添付PDFは **路線 {expected_route}** に関する図面（平面図・縦断図・横断図・全体位置図のいずれか／組合せ）です。

以下の背景知識を活用して、図面に記載されている数値・管路情報を JSON で構造化してください。

# 知識（必読）
{knowledge}

# 思考手順（Chain-of-Thought / 出力前の内部処理）

以下の順序で読み取りを行ってから JSON を生成してください（思考過程は出力に含めない）：

1. **路線の特定**: 平面図の楕円・吹き出し・表題欄から expected_route と一致する路線を探す
2. **図面種別の特定**: 1ページ目から順に「平面図 / 縦断図 / 横断図 / 全体位置図」のいずれかを判定
3. **数値の網羅収集**:
   - 縦断図: 上流管底高 / 下流管底高 / 勾配 i / 延長 L を **全マンホール区間ぶん**
   - 平面図: マンホール記号 / 既設地下埋設物（水道・ガス）
   - 横断図: 道路幅員 / 舗装厚 / 埋設深度
4. **同義表現の正規化**:「TPφ300」→ 管種 "TP" + 管径 "300mm" のように分解
5. **件数チェック**: detected_values は **延長Lだけでも複数本ある**のが普通（マンホール区間ぶん）。1つしか拾えていなければ取り逃しを疑う

{few_shot}

# 抽出するもの
1. 路線番号（必ず {expected_route} と一致するように特定）
2. 図面種別（平面図/縦断図/横断図/全体位置図のいずれか、または複合）
3. 縮尺（例: S=1:300(A1) / V=1:100, H=1:300）
4. detected_values:
   - 管種・管径（例: TPφ250）
   - 勾配（例: i=11.2‰）
   - 延長（例: L=18.10m）
   - 上流管底高 / 下流管底高（数値のみ、単位mGL）
   - 荷重区分（T-14, T-25）
   - 施工時間帯（昼間施工, 夜間施工）
   - 管更生工法（管更生 等）
5. マンホール（人孔）番号と種別
6. 既設地下埋設物（水道管φ75 / ガス管φ50 等）

# 出力ルール
- 路線番号は半角ハイフン区切り
- 数値は記載通り（丸めない）
- 「detected_values」の category は「管種」「管径」「勾配」「延長」「上流管底高」「下流管底高」「荷重区分」「施工時間帯」「管更生工法」のいずれか
- 見つからない項目は出力しない
- 出力は §DRAWING_SCHEMA に従う

# 出典情報（source）の付与ルール
各 detected_values 項目に、可能な限り **source** を付けてください。
- `source.page`: その値が記載されているページ番号（**1-indexed**、複数ページPDFでは1, 2, 3, ...）
- `source.bbox`: ページ画像内での値文字の境界ボックス。`[ymin, xmin, ymax, xmax]` の4要素配列で、**0-1000 に正規化**（左上が (0, 0)、右下が (1000, 1000)）
- bbox はその値の文字（数値テキスト）の周囲を囲む矩形にしてください
- 値の場所が特定できない場合は `source` を省略可（必須ではない）

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
        schema=json.dumps(DRAWING_SCHEMA, indent=2, ensure_ascii=False),
    )


def extract(
    pdf_path: Path,
    expected_route: str,
    knowledge: str,
    client: GeminiClient | None = None,
    self_consistency_k: int = 1,
    with_few_shot: bool = True,
) -> dict:
    client = client or GeminiClient()
    prompt = _build_prompt(expected_route, knowledge, with_few_shot=with_few_shot)

    if self_consistency_k <= 1:
        result = client.generate_json(
            prompt=prompt, pdf_path=pdf_path, response_schema=DRAWING_SCHEMA
        )
        payload = result.parse_json()
        payload["_meta"] = {"model": result.model, "elapsed_s": round(result.elapsed_s, 2)}
        return payload

    # Self-Consistency: detected_values を多数決でフィルタ
    payload, _votes = self_consistency_generate(
        client=client,
        prompt=prompt,
        pdf_path=pdf_path,
        response_schema=DRAWING_SCHEMA,
        list_key="detected_values",
        item_keys=("category", "value", "unit"),
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
    pdf = paths.case_drawing_pdf(case_id)
    if pdf is None:
        logger.warning("No drawing PDF for %s", case_id)
        return None
    logger.info(
        "Extract drawing: %s (%s) <- %s (k=%d)", case_id, route, pdf.name, self_consistency_k
    )
    payload = extract(
        pdf, route, knowledge, client=client, self_consistency_k=self_consistency_k
    )
    out = paths.case_results_dir(case_id) / "extracted_drawing.json"
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    logger.info("Wrote %s", out)
    return payload


def main() -> int:
    setup_logging()
    parser = argparse.ArgumentParser()
    parser.add_argument("--case", help="case_001..006 を指定。省略時は全件")
    parser.add_argument("--dry-run", action="store_true")
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
        pdf = paths.case_drawing_pdf(case_id)
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
