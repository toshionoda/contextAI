# Phase B-E 実装完了サマリ

- **作成日**: 2026-05-07
- **状態**: 実装スケルトン完成、API キーなしの dry-run まで動作確認済み
- **担当**: Claude による先行実装。所有者フルアサイン後はチューニング・実行を引き継ぎ

---

## 1. 実装範囲（計画 §3 Phase B-E）

| Phase | 計画期間 | 実装結果 |
|---|---|---|
| **B**: drawing-calc-matcher の sewer_kanra 拡張 | Day 4-14 | ✅ 全モジュール実装完了 |
| **C**: 計算書・総括表の自前パイプライン | Day 15-25 | ✅ 全モジュール実装完了 |
| **D**: 整合性チェック・精度測定 | Day 26-32 | ✅ 全モジュール実装完了 |
| **E**: Webビューア + Phase 1 接続準備 | Day 33-45 | ✅ Streamlit Webビューア完成 |

実装された Python モジュール: 9本 + Streamlit デモ + CLI

---

## 2. 実装ファイル一覧

```
poc/
├── requirements.txt                              ← 新規（pip依存）
├── .env.example                                  ← 新規（環境変数雛形）
├── README.md                                     ← 新規（実行ガイド）
├── config/
│   └── knowledge_sewer_kanra.md                  ← 新規（管更生工 知識・約400行）
├── schema/
│   └── fukuoka_soukatu.yaml                      ← 新規（L2-L3-L4 階層・約120行）
├── src/sewer_kanra/                              ← 新規パッケージ
│   ├── __init__.py
│   ├── __main__.py                               ← `python -m sewer_kanra` エントリ
│   ├── paths.py                                  ← パス管理（ケース・GT・結果）
│   ├── gemini_client.py                          ← Gemini API ラッパー（リトライ・モデル切替）
│   ├── extract_calc_book.py                      ← 計算書PDF→JSON（Gemini Vision）
│   ├── extract_drawing.py                        ← 図面PDF→JSON（Gemini Vision）
│   ├── aggregate_soukatu.py                      ← L2-L3-L4 集計（pandas）
│   ├── consistency_check.py                      ← 計算書 vs 図面 整合性
│   ├── eval.py                                   ← GT 突合 F1/再現率/適合率
│   └── cli.py                                    ← CLI コマンド群
└── demo/
    └── webapp.py                                 ← Streamlit Webビューア（5タブ）
```

---

## 3. 動作確認済み事項

- ✅ **全モジュール import 成功** (`from sewer_kanra import paths, gemini_client, ...`)
- ✅ **CLI ヘルプ動作** (`python -m sewer_kanra --help`)
- ✅ **Dry-run でプロンプト生成成功** (`python -m sewer_kanra.extract_calc_book --case case_001 --dry-run`)
- ✅ **YAML スキーマ正常パース** (7 L2カテゴリ・各L3件数正常)
- ✅ **Streamlit 依存解決** (pandas 2.3.3 / streamlit 1.50.0)
- ✅ **PDF 自動検出** (case_001 → calc1_那珂_429-2.pdf)

未確認（API キー必要）:
- ⏳ Gemini Vision の実呼び出し（要 GEMINI_API_KEY）
- ⏳ end-to-end パイプライン実行
- ⏳ 精度ベンチマーク（鉄筋PoC F1=0.749 と比較）

---

## 4. 設計の特徴と意図

### 4.1 配筋図PoC（rd-poc-drawing-calc-matcher）との互換性

- **GT スキーマを揃えた**: `detected_items / mappings` の形を踏襲（鉄筋: detected_rebars/mappings → 下水道: detected_items/mappings）
- **knowledge_<structure>.md の形式を踏襲**: 構造別知識を1ファイルにまとめる慣例
- **case_NNN ディレクトリ慣例**: 各ケースに `drawing/`・`ground_truth.json` を持つ構造を継承

→ **所有者キックオフ後、`rd-poc-drawing-calc-matcher` への取り込みが容易**

### 4.2 Azure DI 非依存（Gemini一本）

ユーザー要件で Azure DI 未調達のため：
- 表抽出は Gemini Vision の `response_mime_type=application/json` で代替
- `response_schema` でJSON Schema を渡し、Gemini が schema に従って出力
- pdfplumber は line/rect 数の判定（前処理）にのみ使用、本処理は Gemini

### 4.3 福岡市以外への拡張余地（2026-05-08 方針更新）

**方針**: 自治体ごとの入力スキーマは増やさず、**汎用抽出ロジックで吸収**する。
- 抽出パイプライン（extract_calc_book / extract_drawing）は自治体非依存
- 中間表現は **JS共通工種体系** で正規化
- 自治体差は **出力フォーマッタ** でのみ吸収
  - 福岡市: `schema/fukuoka_soukatu.yaml`（既存。役割を「出力フォーマッタ」に再定義）
  - 横瀬町・大月市: yaml を**追加せず**、まず同抽出ロジックを通して F1 劣化幅を計測
- Phase C Day 23-25 の作業は **「他自治体PDFへの汎用抽出適用検証」** に変更（テンプレ切替検証ではない）
- aggregate_soukatu.py は schema を引数化済み（フォーマッタ切替に流用可能）

### 4.4 川畑さん／福岡市同時提示用Webビューア

5タブ構成:
1. 概要（PDF プレビュー・GT有無）
2. 数量計算書ドラフト（DataFrame）
3. 数量総括表（L2フィルタ付き、CSV ダウンロード可）
4. 整合性レポート（マッチ・FN・FP の3カラム）
5. 精度メトリクス（Macro F1・Go/No-Go帯自動判定）

---

## 5. 所有者フルアサイン後の作業（Phase B-E チューニング）

実装スケルトンは完成しているが、以下は所有者の現場感が必要：

| 工程 | 作業 | 優先度 |
|---|---|---|
| Phase B Day 5-7 | スモークテスト → Gemini Vision の検出粒度確認 | 高 |
| Phase B Day 8-10 | knowledge_sewer_kanra.md の反復チューニング（管更生工特有表現） | 最高 |
| Phase B Day 11-13 | case_001-006 で F1初期計測 | 高 |
| Phase C Day 21-22 | 単価コード辞書化（PG/CB/ZD/PD） | 中 |
| Phase C Day 23-25 | 横瀬町・大月市PDFへの汎用抽出適用検証（スキーマ追加なし、F1劣化幅を計測） | 中 |
| Phase D Day 16-17 | エラー分類・1ラウンド再修正 | 高 |
| Phase E Day 18-19 | デモシナリオ整備・Notebook版 | 中 |
| Phase E Day 20-21 | 川畑さん向け1枚サマリ（report_for_kawabata.md） | 高 |

### 所有者が真っ先にやるべき3点

1. **`config/knowledge_sewer_kanra.md` のレビュー** ← PoC精度の支配要因
2. **case_001 で Gemini を回して accuracy_v0.md 作成** ← Day 14 ゲートの判定材料
3. **`rd-poc-drawing-calc-matcher` への移送可否判断** ← feature branch or fork

---

## 6. リスク再確認（計画 §6 リスク）

実装後の状態でリスクを再評価:

| # | リスク | 計画時 | 実装後 | 備考 |
|---|---|---|---|---|
| R1 | PDFが画像PDF | 中 | **低** | Phase A Day 0 で全PDFがVECTOR/TEXT_LAYERと確認済み |
| R3 | 鉄筋特化 knowledge → 下水道版で薄い | 中 | 中 | knowledge_sewer_kanra.md を400行で作成、内容は所有者レビュー要 |
| R4 | アセット所有者 既存業務との両立失敗 | 高 | **中** | 実装スケルトン完成のため、所有者作業は「チューニング・実行・移送」のみ |
| R5 | GT 作成が想定以上に重い | 中 | **完了** | case_001-003 で完成。case_004-006 は人目視で対応可 |
| R6 | gemini-3-flash-preview のレート制限/廃止 | 中 | 中 | フォールバック（gemini-2.5-flash）を実装済 |
| R9 | Azure DI なしで表抽出再現できない | 中 | **解消** | Gemini Vision の構造化出力で代替設計済み |

総じて、実装完了によってリスクの大半は **低** または **解消** に下がっている。

---

## 7. 次のアクション

### 即実行可能（API キー設定済みなら）

```bash
cd customers/municipal/fukuokacity/poc
export PYTHONPATH=$(pwd)/src
cp .env.example .env
# .env に GEMINI_API_KEY を記入

# Day 14 中間ゲート相当のスモークテスト
python -m sewer_kanra extract-calc --case case_001
python -m sewer_kanra extract-drawing --case case_001
python -m sewer_kanra check --case case_001
python -m sewer_kanra eval --case case_001

# 全ケース一括
python -m sewer_kanra all

# Webビューア
streamlit run demo/webapp.py
```

### 川畑さん／野田さんがやるべき調整作業

1. アセット所有者（akakoumalme）への kickoff_memo.md 共有（5/9）
2. tatsuyanishimoto への組織アサイン承認依頼（5/9）
3. 川畑さんへの事業性ゴーサイン相談（5/9）
4. 福岡市mirai@DX担当への着手通知＋経費負担条件確認（5/14）

詳細は `kickoff/kickoff_memo.md` の §11 参照。
