# 福岡市上下水道局 PoC: 図面→数量計算書 自動生成

- 計画書: `/Users/nodatoshio/.claude/plans/swift-hatching-comet.md`
- 事業性評価: `../feasibility_quantity_calc_2026-05-07.md`
- 書式パターン分析: `../../comparison/_pattern_analysis.md`
- ハンドオフ資料: `PHASE_A_HANDOFF.md`

社内アセット `rd-poc-drawing-calc-matcher`（配筋図-計算書マッチング）の手法を **下水道改築工事（管更生工）** に転用する PoC。

## 製品方針（2026-05-08 確定）

- **自治体ごとの入力スキーマ・テンプレを持たない**
- **図面PDFを投入すると数量が抽出される** 汎用ロジックを中核に置く
- 中間表現は **JS（日本下水道事業団）共通工種体系**（足りないフィールドは独自拡張）
- 自治体差は **出力フォーマッタ**（数量計算書PDF / Excel総括表 / 汎用JSON）でのみ吸収
- **PoCはPDF限定、DWGは非対応**（DWG入力は Track A 完成後の発展課題）

`schema/fukuoka_soukatu.yaml` は「**福岡市の出力フォーマッタ**」であり、入力スキーマではない。他自治体向けは別 yaml を追加するのではなく、**同じ中間表現を別レンダラーに通す**方式を取る。

## クイックスタート

### 1. セットアップ

```bash
cd customers/municipal/fukuokacity/poc

# 依存パッケージ
pip install -r requirements.txt

# 環境変数
cp .env.example .env
# .env を編集して GEMINI_API_KEY を設定
```

### 2. CLI 実行

```bash
# PYTHONPATH を通す
export PYTHONPATH=$(pwd)/src

# 単一ケースで動作確認（推奨初回ステップ）
python -m sewer_kanra.extract_calc_book --case case_001 --dry-run
# → API キーなしでプロンプトを表示（中身確認用）

python -m sewer_kanra extract-calc --case case_001
# → 数量計算書PDFを Gemini Vision に投入し results/case_001/extracted_calc_book.json 生成

python -m sewer_kanra extract-drawing --case case_001
# → 図面PDFを Gemini Vision に投入し results/case_001/extracted_drawing.json 生成

python -m sewer_kanra check --case case_001
# → 計算書 vs 図面 整合性チェック → results/case_001/consistency_report.json

python -m sewer_kanra eval --case case_001
# → ground_truth.json と突合 → F1/再現率/適合率を出力

# 全ケース一括
python -m sewer_kanra all
```

### 3. Webビューア起動

```bash
streamlit run demo/webapp.py
# → http://localhost:8501
```

ビューアの2系統:

- **📤 アップロード解析タブ**（汎用抽出フロー）
  - 図面PDF（必須）を投入し、Vision LLM で工種・規格・数量を直接抽出
  - 計算書PDF（任意）も併せてアップロードすると整合性チェックも実行
  - 路線番号は必須入力（半角ハイフン区切り、例: `429-2`）
  - 結果はセッション内のみ保持（ファイル保存なし）
  - 各サブタブの「📍 検出位置」expander で、Vision LLM が **PDFのどこから値を読んだか**（番号付きのbboxオーバーレイ）を確認できる
- **既存ケース解析**（サイドバー）
  - `case_001..006` を選び、`extract-calc` / `extract-drawing` / `check` / `eval` をボタン実行
  - GT との F1 評価まで通せる開発ループ用
  - 「概要」タブの末尾に「📍 検出位置」セクションがあり、図面/計算書 それぞれの抽出位置を確認可能。`#` 列は番号と一致

> **注意（macOS）**: `pdfplumber` の `to_image` が内部で Ghostscript を呼ぶ場合があります。検出位置オーバーレイで `Unable to get page count` 等のエラーが出たら `brew install ghostscript` を実行してください。

## ディレクトリ構成

```
poc/
├── README.md                       ← このファイル
├── PHASE_A_HANDOFF.md              ← Phase A 完了サマリ・所有者引き継ぎ
├── requirements.txt
├── .env.example
├── config/
│   └── knowledge_sewer_kanra.md    ← Gemini への背景知識（PoC精度の支配要因）
├── schema/
│   └── fukuoka_soukatu.yaml        ← 福岡市 L2-L3-L4 階層スキーマ
├── src/sewer_kanra/                ← パイプライン本体（pipモジュール）
│   ├── paths.py                    ← パス管理
│   ├── gemini_client.py            ← Gemini API ラッパー
│   ├── extract_calc_book.py        ← 計算書PDF→JSON
│   ├── extract_drawing.py          ← 図面PDF→JSON
│   ├── aggregate_soukatu.py        ← L2-L3-L4 集計
│   ├── consistency_check.py        ← 計算書 vs 図面 整合性チェック
│   ├── eval.py                     ← GT 突合 F1
│   └── cli.py / __main__.py        ← CLI エントリポイント
├── demo/
│   └── webapp.py                   ← Streamlit Webビューア
├── eval/                           ← 精度評価関連の追加スクリプト置き場
├── results/                        ← パイプライン実行結果（git管理外でも可）
│   ├── case_001/
│   │   ├── extracted_calc_book.json
│   │   ├── extracted_drawing.json
│   │   ├── consistency_report.json
│   │   └── eval_report.json
│   └── _summary/
│       ├── soukatu_aggregated.csv
│       ├── consistency_report_overall.json
│       └── eval_overall.json
├── dataset_prep/                   ← Phase A で準備済みのケースデータ
│   ├── calc_doc/sewer_types.json   ← 工種マスタ（ST001-ST020）
│   ├── case_001/
│   │   ├── calc/...pdf             ← 路線別 数量計算書 (11p)
│   │   ├── drawing/...pdf          ← 路線別 図面 (1p)
│   │   └── ground_truth.json       ← 手動GT（case_001-003 のみ）
│   ├── case_002/ ... case_006/
│   └── shared/
│       ├── calc/...                ← 全路線共通の総括・集計・付帯工 (31p)
│       └── drawing/...             ← 全体位置図 (2p)
├── audit/
│   ├── data_audit.md               ← Phase A Day 0 PDF構造判定レポート
│   └── route_assignment_summary.md ← 路線別仕分けの結果
├── kickoff/
│   └── kickoff_memo.md             ← 川畑さん・所有者向けキックオフメモ
└── scripts/
    ├── audit_pdf.py                ← PDF 構造判定スクリプト（再実行可）
    └── split_by_route.py           ← 路線別分割スクリプト（再実行可）
```

## パイプライン全体像

```
[PDF 5本（受領済み）]
  ↓ scripts/split_by_route.py
[dataset_prep/case_001..006/{calc, drawing}/  +  shared/]
  ↓ extract_calc_book.py     (Gemini Vision)
  ↓ extract_drawing.py       (Gemini Vision)
[results/case_NNN/extracted_*.json]
  ↓ aggregate_soukatu.py
[results/_summary/soukatu_aggregated.csv]
  ↓ consistency_check.py
[results/case_NNN/consistency_report.json]
  ↓ eval.py
[results/case_NNN/eval_report.json + _summary/eval_overall.json]
  ↓ demo/webapp.py
[Streamlit ビューア（PDF アップロード → 数量計算書ドラフト・整合性・精度可視化）]
```

## 重要ファイル（Critical Files）

| ファイル | 役割 |
|---|---|
| `config/knowledge_sewer_kanra.md` | **PoC精度を支配する最重要ファイル**。管更生工固有の知識（工法種別・呼び径×管厚・取付管マンホール処理）を集約。Phase B でチューニング |
| `dataset_prep/case_001/ground_truth.json` | F1の信頼度を決める基準。野田レビュー要 |
| `src/sewer_kanra/extract_calc_book.py` | PDF→数量計算書JSON のコア（Gemini Vision プロンプト含む） |
| `schema/fukuoka_soukatu.yaml` | **福岡市向け出力フォーマッタ**。L2-L3-L4 階層・行一致率を直接決める。他自治体向けは別 yaml を追加せず、同じ中間表現を別レンダラーに通す |
| `demo/webapp.py` | 川畑・福岡市同時提示用 |

## Go/No-Go 判定基準（Phase 1 接続）

| 指標 | Go閾値 | Conditional Go | No-Go |
|---|---|---|---|
| 図面→計算書マッチング **F1** | **≥ 0.65** | 0.50-0.64 | < 0.50 |
| 同 **再現率** | ≥ 0.80 | 0.65-0.79 | < 0.65 |
| 数量総括表 **行一致率** | **≥ 0.90** | 0.75-0.89 | < 0.75 |
| 整合性チェック **検出率** | ≥ 0.70 | 0.50-0.69 | < 0.50 |
| **汎用抽出の他自治体PDF適用**（横瀬町・大月市の図面PDFをそのまま投入） | 同抽出ロジックでF1劣化幅 ≤ 10pt | 10-25pt 劣化 | > 25pt 劣化 |
| API コスト | ¥10/路線以下 | ¥10-50/路線 | > ¥50/路線 |

`demo/webapp.py` の「精度メトリクス」タブが Macro F1 から自動的に判定帯を表示する。

## 既知の制約（Phase B 着手前確認事項）

- **GT の bbox は null**: 数値マッチングのみで動作。座標精度が必要なら所有者がアノテート
- **case_004-006 の GT 未作成**: 推論評価のみで使う想定（人目視サンプリング）
- **Azure DI 不採用**: 表抽出は Gemini Vision の構造化出力で代替（Phase 1 で再評価）
- **DWG 入力非対応**: PDF のみ（DWG パーサー Track A 完成後の Phase 1 後半で対応）

## 関連リソース

- 元アセット: `https://github.com/structuralengine/rd-poc-drawing-calc-matcher`
- 計画ファイル: `/Users/nodatoshio/.claude/plans/swift-hatching-comet.md`
- 福岡市受領 PDF: `customers/municipal/fukuokacity/*.pdf`
- 他自治体比較データ: `customers/municipal/comparison/`（横瀬町・大月市・JS等）

## 次のアクション（Phase B → C → D → E）

1. **環境セットアップ**: `pip install -r requirements.txt` + `.env` 作成
2. **API キー設定**: `GEMINI_API_KEY` を取得・設定
3. **スモークテスト**: `python -m sewer_kanra extract-calc --case case_001` で1ケースだけ実行
4. **knowledge_sewer_kanra.md チューニング**: 結果を見て知識を反復改善（Phase B Day 8-10 想定）
5. **全ケース実行**: `python -m sewer_kanra all` で6ケース回す
6. **精度評価**: `eval` の Macro F1 が Go閾値（≥ 0.65）を超えるか確認
7. **デモ整備**: `streamlit run demo/webapp.py` で川畑さんへ提示

---

## Tier A 改善メニュー（2026-05-15 追加）

### A1: Few-shot 範例

`extract_calc_book.py` / `extract_drawing.py` のプロンプトに case_002 / case_003 の入出力範例を埋め込み済み。
ablation したい場合は `--no-few-shot` を渡す:

```bash
python -m sewer_kanra.extract_calc_book --case case_001 --no-few-shot
```

### A2: knowledge.md スコープ規則

`config/knowledge_sewer_kanra.md` §0 に「L2='管きょ更生工' 以外は抽出しない」スコープ規則を追加。
FP21件の主因（共通仮設費・管路土工・付帯工の混入）を構造的に防ぐ。

### A3: 整合性チェック改善

2系統:

```bash
# (a) 同義工種グルーピング（デフォルト・無料）
python -m sewer_kanra check --case case_001

# (b) LLM対話型ペアリング（Gemini API 1回／ケース、確度の高いペアのみ採用）
python -m sewer_kanra check --case case_001 --llm-pair
```

`method` フィールドで `synonym_grouping` / `llm_pairing` / `per_item`（旧）が区別できる。

### A4: Self-Consistency（多数決）

`--k` で同一プロンプトを複数回呼び出し、`>= ⌈k/2⌉+1` 票のアイテムだけ残す。

```bash
# 推奨: k=3（多数決の最小単位）
python -m sewer_kanra extract-calc --case case_001 --k 3
python -m sewer_kanra all --case case_001 --k 3
```

コストは k 倍（Gemini 3 Flash で1ケース ~$0.01 → ~$0.03）。
出力JSON に `_self_consistency` フィールドが付き、票数の内訳が確認できる。

### A5: モデル切替

環境変数で切替可能（`gemini_client.py` がデフォルト値を持つ）:

```bash
# 高精度モデル（図面ディメンション 80% 実績、コスト x4）
export GEMINI_MODEL_PRIMARY=gemini-2.5-pro
export GEMINI_MODEL_FALLBACK=gemini-2.5-flash

# 最新軽量モデル（既定）
export GEMINI_MODEL_PRIMARY=gemini-3-flash-preview
export GEMINI_MODEL_FALLBACK=gemini-2.5-flash
```

A/B 評価したいときは別の RESULTS_DIR を切って実行:

```bash
RESULTS_DIR=results_pro GEMINI_MODEL_PRIMARY=gemini-2.5-pro \
  python -m sewer_kanra all --case case_001 --k 3
```

### 推奨実行レシピ（Week 1）

```bash
# 1) Tier A 全部入りで case_001 だけ実行
python -m sewer_kanra all --case case_001 --k 3

# 2) 整合性チェックは LLM ペアリングも比較
python -m sewer_kanra check --case case_001 --llm-pair

# 3) Macro F1 確認（Go閾値: ≥ 0.65）
python -m sewer_kanra eval --case case_001
```
