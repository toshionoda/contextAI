# 福岡市上下水道局 PoC キックオフメモ

- **日付**: 2026-05-07 ドラフト
- **作成**: 野田
- **共有先**: akakoumalme（実装主担当・フルアサイン依頼）、tatsuyanishimoto（マネジメント承認）、Katsushige-Onishi（仕様策定・建技152案件との連携協議）、川畑さん（経営承認）
- **計画ファイル**: `/Users/nodatoshio/.claude/plans/swift-hatching-comet.md`

---

## 1. 案件サマリ（30秒版）

福岡市道路下水道局（mirai@DX担当者経由・元下水道部署）から **「下水道工事 図面→数量計算書 自動生成」** の製品要望。**PoC受託ではなく自社プロダクト開発投資の事業性評価フェーズ**。

社内アセット `rd-poc-drawing-calc-matcher` の手法（配筋図-計算書マッチング、F1=74.9%）を **下水道版（管更生工）** に転用するのが最短ルートと判断。**1-2ヶ月で動くデモ + 精度数値レポート** を作り、**川畑さんへの本格 Phase 1（自社プロダクト開発）投資判断材料** にしたい。

PoC成功時はそのまま Phase 1 着手 = **事業性ゴーサイン並行進行**。

---

## 2. 事業性試算（裏付け）

| 項目 | 試算 |
|---|---|
| 市場規模（SAM） | 約3.6-6億円/年（政令市20＋中核市62＋特例市40） |
| 競合優位の窓 | 2-3年（東芝CISSARTの下水道領域参入まで） |
| 累計開発投資（社内アセット流用） | ¥900-1,650万 |
| Base Case 5年累計売上 | ¥1.9億 |
| 投資回収（社内アセット流用） | 2年目 |

詳細: `customers/municipal/fukuokacity/feasibility_quantity_calc_2026-05-07.md`

書式パターン共通性は10自治体比較で検証済み（JS下水道施設CAD製図基準＋政令市の国基準準拠で全国統一）。福岡市MVPは政令市レベルで **コアロジック85-90%再利用可能**。詳細: `customers/municipal/comparison/_pattern_analysis.md`

---

## 3. PoC スコープ（確定）

| 項目 | 内容 |
|---|---|
| 期間 | **1-2ヶ月**（実働40-45人日） |
| 工種範囲 | **管更生工のみ**（福岡市データの主要工種） |
| データ規模 | 福岡市1案件・6路線（429-2/430-3/410-1-3/86-1/209-4/452-5） |
| 入力 | PDF（受領済み5本） |
| 主担当 | **akakoumalme フルアサイン依頼**（8割以上・1-2ヶ月専任） |
| 副担当 | 野田（事業企画・GT作成・川畑相談・福岡市調整・約10日） |
| 主技術 | **Gemini Vision (gemini-3-flash-preview) 一本**（Azure DI不採用・予算取得回避） |
| デモ形式 | **Streamlit Webビューア + 精度レポート**（川畑＆福岡市同時提示） |

### 検証項目

1. 図面 PDF → 数量計算書ドラフト生成
2. 数量計算書 → 数量総括表 自動集計（JS共通工種体系で正規化、L2-L3-L4階層）
3. 図面 ⇔ 数量計算書 整合性チェック（drawing-calc-matcher の手法を sewer_kanra に転用）
4. 金抜き設計書 → 単価コード辞書化（PG/CB/ZD/PD のサンプル）
5. **汎用抽出の他自治体PDF適用検証**（横瀬町・大月市の図面PDFを同抽出ロジックに通し、F1劣化幅を計測。**自治体スキーマを増やさず**抽出精度のみで吸収できるかを検証）

> 製品方針（2026-05-08確定）：**自治体ごとの入力スキーマを持たない**。図面PDF→Vision LLMで汎用抽出。中間表現はJS共通工種体系。自治体差は出力フォーマッタでのみ吸収。PoCはPDF限定（DWG非対応）。

---

## 4. 受領済みデータの状態（Phase A Day 0 完了報告）

`customers/municipal/fukuokacity/` 配下5本のPDFを `pdfplumber` で構造判定済み。詳細は `customers/municipal/fukuokacity/poc/audit/data_audit.md`

| ファイル | ページ | ベクター度 | 判定 |
|---|---|---|---|
| 図面一式｜那珂二丁目外.pdf | 8 | **50,679** | ✅ VECTOR（極めて高い） |
| 数量計算書①｜那珂工区.pdf | 27 | 287 | ✅ VECTOR |
| 数量計算書②｜板付・諸岡工区.pdf | 21 | 361 | ✅ VECTOR |
| 数量総括表｜那珂二丁目外.pdf | 9 | 106 | ✅ VECTOR |
| 金抜き設計書｜那珂二丁目外.pdf | 51 | 39 | TEXT_LAYER_ONLY |

→ 画像PDFゼロ。**Phase B 進行可** の条件を満たす。Gemini Vision に直接投入するパスもあり、pdfplumber でベクター構造化する併用パスもあり。

---

## 5. 技術スタック（Gemini一本に確定）

```
[福岡市PDFセット（5本）]
   ↓
[pdfplumber] PDF構造判定 + ページ分割・路線別仕分け
   ↓
[Gemini Vision (gemini-3-flash-preview)]
   ├─ (a) 図面 → 数値抽出（管径・延長・土被り・規格・本数）
   ├─ (b) 数量計算書 → 構造化JSON
   ├─ (c) 数量総括表 → L2-L3-L4階層JSON
   └─ (d) 整合性チェック
   ↓
[pandas] 集計・差分・正規化
   ↓
[Streamlit] Webビューア + [results/] 精度レポート
```

PoC段階では `rd-poc-drawing-calc-matcher` のみを中核に使い、他5本（pdf-component-extractor / BLADE / tekkin_hyo_chushutsu / rebar-drawing-hierarchy / drawing_LLM_lab）は Phase 1 で再評価。Azure DI は使わない（予算取得・調達交渉を回避してスピード重視）。

---

## 6. 想定成果物

| 成果物 | 用途 |
|---|---|
| Streamlit Webアプリ（PDFアップロード→数量計算書ドラフト・総括表・精度可視化） | 川畑＆福岡市デモ |
| Jupyter Notebook 詳細版 | 技術詳細説明 |
| `results/_summary/accuracy_overall.md`（路線別・工種別 F1/再現率/適合率） | Go/No-Go判定 |
| `schema/fukuoka_soukatu.yaml`（**出力フォーマッタ**。自治体ごとの入力スキーマは持たない） | 福岡市の数量総括表レンダリング |
| `reports/report_for_kawabata.md` | 1枚サマリ |
| `reports/phase1_scoping_proposal.md` | Phase 1 詳細スコープ提案 |

---

## 7. アサイン・スケジュール依頼

### akakoumalme（実装主担当）への依頼

**フルアサイン 8割以上・1-2ヶ月専任**を希望。理由：
- Gemini API による構造別 knowledge.md 設計の主担当（5構造で実証済み）
- `rd-poc-drawing-calc-matcher` のリポジトリ最多コミッター（PoC運用の現場感最強）
- sewer_kanra 構造追加（管更生工）の主実装者として最適

工程ハイレベル（詳細は計画ファイル §実装ステップ）：

| Phase | 期間 | 内容 |
|---|---|---|
| A | Day 0-3 | 環境構築・データ前処理・GT作成 |
| B | Day 4-14 | matcher 拡張（knowledge_sewer_kanra.md 作成・反復チューニング） |
| C | Day 15-25 | 自前パイプライン（計算書/総括表 表抽出・単価コード辞書） |
| D | Day 26-32 | 整合性チェック・精度測定 |
| E | Day 33-45 | Streamlit Webビューア・レポート・川畑さんデモ |

### tatsuyanishimoto（マネジメント承認）への確認依頼

- akakoumalme のフルアサイン承認（既存業務との両立失敗が R4 リスク）
- リポジトリ運営方針（feature branch 作業 OR fork）
- PoC 成果の上流還流方針（PR提案OKかどうか）

### Katsushige-Onishi（仕様策定・建技152案件との連携）への協議依頼

- 建技 152「工程・概算算出自動化」案件との並列展開可否
- 大西さんの建技ネットワークから下水道領域での仕様協議が可能か

---

## 8. 連携合意項目（PoC 流用に関する事前確認）

| # | 確認事項 |
|---|---|
| 1 | PoC期間中の `rd-poc-drawing-calc-matcher` の **コード参照・改変・派生** の許可範囲 |
| 2 | **顧客先IPライセンス**: 派生案件由来コードが含まれていないか、福岡市データへの流用に制限はないか |
| 3 | PoC期間中の **質問対応窓口**（誰に・どの頻度で） |
| 4 | PoC成果（精度値・知見）の **元リポジトリへの還流** 可否 |
| 5 | Phase 1（プロダクト化）に進んだ場合の **権利関係・利用料・ライセンス** |
| 6 | 各アセットの **未公開の落とし穴**（スコープ外条件、依存ライブラリのバージョン制約） |
| 7 | sewer_kanra 構造を上流リポジトリに PR で還流するか、fork で独立進行するか |

---

## 9. 期待アウトプット（このキックオフ MTG で決めたいこと）

- [ ] akakoumalme フルアサイン承諾（tatsuyanishimoto 経由の組織判断含む）
- [ ] 既存業務の他メンバー一時委譲（必要なら川畑さん介入）
- [ ] feature branch 作業 vs fork の方針確定
- [ ] 連携合意項目 §8 の1-7 への回答
- [ ] PoC 期間中の週次レビュー枠の設定（毎週金曜30分など）
- [ ] 川畑さんへの正式相談タイミング（Phase A完了時 / Day 14中間ゲート時 / 完了時 のいずれか）
- [ ] mirai@経費負担交渉の可否（並行で福岡市と詰めるか）

---

## 10. 既に完了している準備（Phase A Day 0）

- ✅ 福岡市受領 PDF 5本の構造判定（`poc/audit/data_audit.md`）
- ✅ 全PDFがベクター/テキスト系で Gemini Vision 投入可能と確認
- ✅ アセット所有者特定（akakoumalme/tatsuyanishimoto/Katsushige-Onishi）
- ✅ PoC作業ディレクトリ作成（`customers/municipal/fukuokacity/poc/`）
- ✅ 計画ファイル作成（`/Users/nodatoshio/.claude/plans/swift-hatching-comet.md`）
- ✅ 事業性評価レポート最新化（`customers/municipal/fukuokacity/feasibility_quantity_calc_2026-05-07.md`）
- ✅ 書式パターン共通性レポート（`customers/municipal/comparison/_pattern_analysis.md`）

---

## 11. 次のステップ（このメモ送付後）

1. **野田 → akakoumalme（DM）**: 「下水道版 sewer_kanra 構造追加」の打診、本メモ共有
2. **野田 → tatsuyanishimoto（DM）**: アサイン承認の組織判断依頼
3. **野田 → 川畑（slack）**: 本案件の事業性ゴーサインを取りに行くタイミング相談（Phase A完了後の判断材料はそろっている）
4. **野田 → 福岡市mirai@DX担当**: PoC着手予定の通知 + 経費負担条件の確認
5. **三者キックオフMTG**（30分・希望日：来週前半）: 組織アサイン・連携合意・運営ルール確定
