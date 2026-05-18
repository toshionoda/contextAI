# ディープリサーチ: 下水道PoC 図面→数量抽出 精度向上手法

- **調査日**: 2026-05-15
- **対象PoC**: 福岡市上下水道局「下水道工事 図面→数量計算書 自動生成」
- **調査担当**: 野田（Claude支援）
- **調査目的**: 現状 Macro F1=0.40（precision=0.25, recall=1.0）を **6/6 Go/No-Go判定までに F1≥0.65** に押し上げるための、論文・OSS・商用システム横断の改善メニューを編成する
- **関連文書**:
  - 事業性評価: `customers/municipal/fukuokacity/feasibility_quantity_calc_2026-05-07.md`
  - PoC実装: `customers/municipal/fukuokacity/poc/README.md`
  - 評価結果: `customers/municipal/fukuokacity/poc/results/_summary/eval_overall.json`

---

## エグゼクティブサマリー

### 主要発見

1. **現状 F1=0.40 は「精度問題」ではなく「GT粒度問題」が大半を占める**
   - case_001：precision=0.25（FP21件）、recall=1.0（FN=0）
   - GTが「管きょ更生工コア工種7項目」しか持たないのに対し、抽出側は計算書全体（共通仮設費・管路土工・取付管・マンホール・付帯工）まで拾っている
   - **GTを実用粒度（管路土工・付帯工含む20項目+）に再設計するだけで F1 0.55-0.70 帯に到達する可能性が高い**

2. **VLM単体の達成可能性能は学術論文ベースで F1=0.93+ が報告されている**
   - YOLOv11-obb + Donut のハイブリッド構成で機械図面 F1=93.5% / Recall 99.2%（arxiv 2506.17374）
   - 400件のFTでFlorence-2が GPT-4o より F1 +52.4% （arxiv 2411.03707）
   - Gemini 2.5 Pro の表抽出 94%、図面ディメンション抽出 80%（Businessware Tech ベンチマーク）
   - 商用 Civils.ai は modern PDF で 97% 精度（建設業 2D CAD/PDF）
   - **F1=0.65 ターゲットは、PoCスコープ内で十分達成可能なライン**

3. **最も効果的かつ低コストな改善レバーは「GT再設計」「プロンプトスコープ明示」「Few-shot例追加」の3点**
   - 合計2-3日工数で F1 +0.20-0.35 が見込める（Tier S/A）
   - ファインチューニングやハイブリッド構成は中長期、まずプロンプト・GT周りで Go閾値を超える

4. **整合性チェックF1=0.333 は「マッチング粒度ミスマッチ」が主因**
   - 計算書5項目（路線延長・管きょ延長・更生管材・内面更生・Tφ150土工）vs 図面1項目（L=18.10m）の構造的不一致
   - 整合性チェック側のマッチングロジック改善（呼び径＋単位＋数値の数式マッチ＋同義語辞書）で 0.50-0.70 帯に届く

5. **IBM Granite-Docling（258Mパラメータ）の登場で「VLM自体を載せ替える」という第3の選択肢が生まれた**
   - TEDS-structure 0.97（FinTabNet）、構造化出力のDocTags形式
   - PoC精度が頭打ちになったときの代替候補として有力

### 推奨アクション（6/6 Go/No-Go までの3週間）

- **Week 1 (5/15-5/22)**: GT再設計＋プロンプト改修＋Few-shot追加 → case_001-003で F1≥0.55 確認
- **Week 2 (5/22-5/29)**: 整合性チェックロジック改善＋pdfplumberベクター情報の併用 → F1≥0.65 確認
- **Week 3 (5/29-6/5)**: case_004-006 GT追加で6ケース評価＋他自治体PDFでの汎用抽出検証 → 横展開可能性検証
- **6/6 判定**: Go閾値クリアなら Phase 1 MVP着手、未達なら Donut/Florence-2 FT へ転換

---

## 1. 現状診断：F1=0.40 の解像度を上げる

### 1.1 FP21件の構造分析

`results/_summary/eval_overall.json` を読むと、case_001 の FP21件 は以下5領域に分類できる：

| 分類 | FP件数 | 例 |
|---|---|---|
| 共通仮設費（準備費・管内洗浄・本管TV調査） | 4 | 「管内洗浄工 施工前 17.2m」「本管TV調査工 施工前 17.2m」 |
| 管路土工（掘削・埋戻・砂基礎・残土処分） | 4 | 「掘削 1.3m³」「埋戻 再生砂 1.0m³」 |
| 取付管およびます工 | 3 | 「小口径汚水桝 T-14 3箇所」 |
| マンホール工 | 3 | 「鉄蓋 φ600 T-14 2組」「足掛金物 W=300 1個」 |
| 付帯工（舗装・管撤去） | 7 | 「舗装版切断 4.0m」「既設管撤去 Tφ250 1.55m」 |

**観察**: 抽出側はこれらを「実在する」と認識して拾っているが、GTは管きょ更生工（ST001-ST020マスタ）のみを正解として持っている。**つまり抽出ロジックは妥当に動いており、GTのスコープと不一致**。

### 1.2 整合性チェック F1=0.333 の原因

| 計算書側（5項目） | 図面側（1項目） | マッチング結果 |
|---|---|---|
| 路線延長 18.10m | L=18.10m | ✅ マッチ |
| 管きょ延長 17.20m | （該当なし） | unmatched_calc |
| 更生管材 更生自立管 18.1m | （該当なし） | unmatched_calc |
| 内面更生工 反転・引込工 17.2m | （該当なし） | unmatched_calc |
| Tφ150土工延長 1.2m | （該当なし） | unmatched_calc |

**観察**:
- 図面PDFから抽出された長さ情報が1点しかない（おそらく代表寸法 L=18.10m のみ）
- 計算書側は「同じ路線の値を5項目に分けて記載」している（更生管材は管口仕上含む、内面更生は仕上含まない、Tφ150は取付管）
- これは **計算書の階層分解 vs 図面の集約表示** の根本的な情報量差。図面1枚から1値しか出ないのは妥当
- 整合性チェックを「数値一致」ではなく「**同義工種グルーピング後の数値合算一致**」に変える必要

---

## 2. 学術論文の動向（2023-2026）

### 2.1 工業図面からの自動抽出：F1の到達点

**arxiv 2411.03707 (2024)** — Fine-Tuning VLM for Engineering Drawing Information Extraction:

- Florence-2（230Mパラメータ）を 400件のGD&T図面でFT
- GPT-4o / Claude-3.5-Sonnet をゼロショットで比較
- 結果: **Florence-2 が F1 +52.4%、hallucination -43.15%**
- 教訓: ドメイン特化FTは 400件規模でも閉鎖型VLMを上回る

**arxiv 2506.17374 (2025)** — From Drawings to Decisions: Hybrid Vision-Language Framework:

- アーキテクチャ: **YOLOv11-obb（回転対応物体検出）→ パッチ抽出 → 軽量VLM（Donut/Florence-2）**
- データセット: 1,367 機械図面、9カテゴリ
- 結果: **Donut で Precision 88.5% / Recall 99.2% / F1 93.5% / Hallucination 11.5%**
- 教訓: **「検出 → クロップ → VLM」の2段構成が単独VLMを上回る**

**arxiv 2511.15090 (2025)** — BBox-DocVQA:

- 文書VQAに bbox grounding を組み込んだデータセット（30k QA pairs）
- 現状の VLM は IoU=35.20% (Qwen2.5VL-72B) と spatial grounding が弱い
- 教訓: **「答えだけでなく bbox を返させる」プロンプトは精度向上の余地が大きい**

### 2.2 建設業特化のデータセット・ベンチマーク

**CISOL (WACV 2025)** — Construction Industry Steel Ordering List:
- 建設業の表抽出データセット（PubTabNet系列）
- 評価指標: mAP @ 0.5:0.05:0.95（PubTabNet Challenge Track A準拠）

**AECV-Bench (2026)** — Architecture/Engineering/Construction Vision Benchmark:
- GPT-4o, Gemini, Claude, Qwen を AEC図面で評価
- タスク: symbol recognition, annotation interpretation, tag extraction, cross-reference identification
- 結論: 汎用VLMは AEC特化タスクで gap が大きい

**Towards fully automated processing of construction diagrams (IJDAR 2024)**:
- YOLO系で mAP 79%、Faster R-CNN系で mAP 83%（建設図面シンボル検出）
- 教訓: 高解像度建設図面でも従来CNN系で 80%帯は達成可能

### 2.3 Few-shot 図面シンボル検出

**Few-Shot Symbol Detection in Engineering Drawings (TandFonline 2024)**:
- 稀少シンボルにはfew-shot学習が有効
- 大規模アノテーション工数を圧縮できる
- 教訓: 下水道の稀少工種（特殊継手・特殊マンホールなど）には適用余地

### 2.4 表構造認識SOTA

**TableFormer (IBM, 2022→2025更新)**:
- PubTabNet TEDS: 簡単な表 98.5% / 複雑な表 95%
- IBM Doclingに統合済み

**Granite-Docling-258M (IBM 2025)**:
- 258Mパラメータの軽量VLM
- FinTabNet TEDS-structure 0.97（前モデル比 +0.15）
- DocTags形式の構造化出力（チャート・表・式・脚注を統合表現）
- **PoCの代替VLM候補として最有力**

**TABLET (2025)**:
- Dual Transformer (horizontal + vertical) で TableFormer を超える
- 自己回帰型でない高速版

---

## 3. Vision LLM ベンチマークと精度向上テクニック

### 3.1 モデル別性能（Businessware Tech 2025）

| モデル | 表抽出 | 図面ディメンション | $/1000p | s/page |
|---|---|---|---|---|
| **Gemini 2.5 Pro** | 94.2% | 79.96% | $130 | 91.4 |
| Gemini 2.5 Flash | — | 77.34% | $30.5 | 77.5 |
| GPT-4o | 38.5% | — | $19 | 16.9 |
| GPT-4o mini | — | 39.59% | $24.9 | 41.8 |
| Claude Opus 4 | — | 40.49% | $312 | 64.8 |
| Azure Layout | 81.5% | （図面非対応） | $10 | 4.3 |

**インサイト**:
- 図面領域は **Gemini Pro が圧倒的に優秀**（GPT-4o系・Claude系は半分以下）
- PoCは Gemini 3 Flash → **Gemini 2.5 Pro / 3 Pro への切替検証は最優先確認事項**
- 表中心なら Azure DI / AWS Textract がコスト面で優位だが、図面では使えない

### 3.2 精度向上テクニック

#### (A) プロンプトエンジニアリング

- **Chain-of-Thought (CoT)**: 抽出前に「どの工種か推定 → 規格判別 → 数値抽出」の手順を踏ませる。reasoning タスクで +19-35%（PaLM 540B）
- **Few-shot**: case_002/003 を例として埋め込む。同型タスクで顕著な改善
- **Constrained output**: response_schema + enum で許容工種を限定（ST001-ST020マスタを直接enum化）
- **2025年研究**: Amazon Textract + Automatic Prompt Engineer で **Precision 95.5% / 抽出精度 91.5%**

#### (B) 構造化出力 (Gemini response_schema)

- 構文的に valid JSON は保証されるが **意味的正しさは別途検証必要**
- 既知の制約値（管径 250/300/450/600/700/800、工種マスタ20件）を enum で固定すれば FP を構造的に削減できる

#### (C) Self-Consistency (Majority Vote)

- 同じプロンプトを k=3 回呼び出し、多数決
- GSM8K で +17.9%、MATH で +23.7pp の改善実績
- コストは k倍だが、Geminiは比較的安価なので現実的
- **F1 +0.05-0.10 の上乗せが見込める**

#### (D) bbox Grounding

- 「数値だけでなく座標も返せ」と指示することで hallucination が減る
- 現状の `webapp.py` の「検出位置」expander の機構を強化材料として活用可能
- Qwen2.5-VL や Gemini 3 で grounding 性能が向上

#### (E) Hallucination 削減

- 「reason+verify」パターン：抽出 → 自己検証 → 確信度低いものをdrop
- 後処理：単位・桁数の妥当性チェック（管径 250mm < L=18m など物理常識フィルタ）
- 出典: GitGuardian / Datadog の事例で実証

---

## 4. PDFベクター × Vision LLM ハイブリッド

### 4.1 ハイブリッド戦略の基本

**ルーティング型（PyMuPDF4LLM 標準）**:
- テキスト層あり → pdfplumber/PyMuPDF で直接抽出
- 画像PDF/複雑なネスト表 → Vision LLM
- **コスト効果**: 10-250倍安い

**福岡市PoC適用案**:
- 数量計算書PDF（VECTOR、テキスト層あり） → **pdfplumber先行で表構造を取得 → Vision LLMで意味解釈** のハイブリッド
- 図面PDF（VECTOR、ベクター度50,679） → 既存 rd-pdf-component-extractor で構造化 → Vision LLM
- 金抜き設計書（TEXT_LAYER_ONLY） → pdfplumber 単独で十分

### 4.2 ベクター情報の活用パターン

`pdfplumber.extract_tables()` / `extract_lines()` / `extract_rects()` で取得できる：
- 表のセル境界（rect）→ 表構造の事前推定
- 寸法線・引出線（line）→ 図面内テキストの所属推定
- テキストブロック位置（chars）→ 凡例・タイトル枠の事前領域分割

**活用案**:
1. **表構造を pdfplumber で固定** → Vision LLMには「このセル値は何の項目か」だけ問う
2. **領域別投入**：凡例・タイトル枠・本図・寸法表 を pre-segment してから VLM へ渡す
3. **FP削減**: Vision LLMの出力に対し「pdfplumber で実在するテキストか」を後処理で照合

---

## 5. 表抽出・領域別階層抽出

### 5.1 IBM Docling の活用検討

- **DocLayNet** (layout analysis) + **TableFormer** (table structure recognition) のスタック
- 数量計算書（表中心）には TableFormer の TEDS=98.5% が直接効く
- **代替検証案**: 現状のGemini単独 vs Docling パイプライン で精度・コスト比較

### 5.2 階層的領域分割

論文側の主流は **「Geometric role検出 → Logical role割当」の2段構え**:
1. テキスト・表・図・選択マーク（geometric）
2. タイトル・見出し・脚注（logical）

**下水道図面への翻訳**:
- Geometric: 平面図／縦断図／横断図／凡例／タイトル枠／寸法表
- Logical: 路線番号／工種凡例／管径表記／延長表記／勾配表記／管種

**実装パターン**:
- 既存 rd-blueprint-layout-detection-engine（BLADE）でgeometric分割
- VLMでlogical role判定
- これは **社内アセット②③④の組合せがそのまま回答**

---

## 6. 整合性チェック改善

### 6.1 現状の課題（F1=0.333）

計算書5項目を図面1項目とマッチングするのが構造的に不可能。

### 6.2 改善アプローチ

#### (A) 同義工種グルーピング

- 「路線延長 / 管きょ延長 / 更生管材 / 内面更生 / 仮設備」を **1つの『管路 18.1m / 17.2m』クラスタ** にまとめてから図面側と照合
- 計算書側の knowledge.md に「同じ路線で複数工種が同延長」のルールを記述

#### (B) Topology-based matching（ScienceDirect 2017 + 派生研究）

- グラフ構造での部分一致／全体一致
- 重い実装だが整合性チェックの王道

#### (C) LLMによる対話型整合性チェック

- 計算書JSONと図面JSONを両方プロンプトに入れ、「同一物体を指す項目をペアリングせよ」と Gemini に問う
- これが最も早く F1 0.50-0.70 に到達する現実解

#### (D) Articulate / FlowX.AI スタイル

- 「Drawing-to-Spec Cross-Reference」を行う商用システムは「材料コール vs 仕様要求」の照合に同義語辞書を持つ
- 下水道版は **管径・工種・施工法の同義語辞書** が肝（建設物価/JS標準歩掛から構築可能）

---

## 7. 改善メニュー（優先度 × 期待効果 × 実装コスト）

### 凡例
- **コスト**: 工数（人日）
- **期待効果**: F1 への寄与（増分）
- **確度**: 高（既存研究で実証）／中（応用次第）／低（探索的）

### Tier S — 最初の3日で必ずやる（F1 +0.20-0.35）

| # | 施策 | 内容 | コスト | 効果 | 確度 |
|---|---|---|---|---|---|
| S1 | **GT再設計** | case_001-003 の GT を「管きょ更生工 + 付帯工 + 管路土工 + マンホール工 + 取付管」の20-25項目に拡張。FPを構造的に消す | 1-2日 | +0.15-0.25 | 高 |
| S2 | **プロンプトのスコープ明示** | 「ST001-ST020の管きょ更生工コア工種のみ抽出」（GTスコープに合わせる）、または「すべての工種を JS共通工種体系で抽出」（GTを広げる）のどちらかに統一 | 0.5日 | +0.05-0.15 | 高 |
| S3 | **response_schema に enum 制約** | 工種マスタ20件・管径バリエーション・単位を全部 enum 化。schema違反を構造的に防ぐ | 0.5日 | +0.05-0.10 | 高 |

### Tier A — 次の1週間で実装する（F1 +0.10-0.25）

| # | 施策 | 内容 | コスト | 効果 | 確度 |
|---|---|---|---|---|---|
| A1 | **Few-shot examples** | case_002 と case_003 を抽出プロンプトの few-shot に埋め込む（規格と数値の対応例） | 1-2日 | +0.05-0.15 | 高 |
| A2 | **knowledge_sewer_kanra.md チューニング** | 管更生工法（自立管／複合管）・取付管マンホール処理・付帯工の暗黙ルールを追加。Phase B Day 8-10 想定の作業 | 2-3日 | +0.10-0.20 | 高 |
| A3 | **整合性チェックの同義語辞書化** | 「路線延長／管きょ延長／更生管材」を同一クラスタ化。LLMにペアリングを問う対話型に変更 | 1-2日 | 整合性F1 +0.15-0.30 | 中 |
| A4 | **Self-Consistency (k=3)** | 同プロンプトを3回呼び出し、多数決。Geminiのvariance吸収 | 1日（コストx3） | +0.05-0.10 | 中 |
| A5 | **モデル切替検証** | Gemini 3 Flash → 2.5 Pro / 3 Pro でA/B比較。図面ディメンション 80% 実績あり | 0.5日 | +0.05-0.20 | 中 |

### Tier B — 2-3週間で実装する（F1 +0.05-0.20）

| # | 施策 | 内容 | コスト | 効果 | 確度 |
|---|---|---|---|---|---|
| B1 | **pdfplumber ハイブリッド** | 数量計算書を pdfplumber.extract_tables() で表抽出 → Vision LLM で意味解釈。社内アセット①②に直結 | 3-5日 | +0.10-0.20 (precision) | 中 |
| B2 | **領域別投入** | 凡例・タイトル枠・本図・数量表 を BLADE 系で pre-segment → 領域別にVLM | 3-5日 | +0.10-0.15 | 中 |
| B3 | **bbox grounding 強化** | 「数値+bbox+確信度」を返させ、低確信度はdrop。FP削減狙い | 1-2日 | precision +0.10 | 中 |
| B4 | **後処理：物理常識フィルタ** | 管径×延長×単位の妥当性チェック。管径250mm でL=1000mは異常などのルール | 1-2日 | precision +0.05-0.10 | 高 |
| B5 | **case_004-006 GT追加** | 評価分散を下げ Macro F1の信頼性向上。aka所有者と分担 | 2-3日 | （評価精度向上） | 高 |

### Tier C — Phase 1接続後の探索的施策（F1 +0.10-0.30）

| # | 施策 | 内容 | コスト | 効果 | 確度 |
|---|---|---|---|---|---|
| C1 | **Donut / Florence-2 ファインチューニング** | 400件下水道図面でFT。論文ベースで F1 +52.4% 実績 | 2-4週間 | +0.15-0.30 | 中 |
| C2 | **Granite-Docling-258M 試験** | IBM最新軽量VLM。TEDS 0.97（表）。代替VLMとして検証 | 1-2週間 | 表F1大幅改善 | 中 |
| C3 | **YOLOv11-obb + Donut 2段構成** | arxiv 2506.17374 のアーキテクチャ移植。F1 93.5% 実績 | 3-4週間 | +0.20-0.30 | 中 |
| C4 | **社内アセット⑤(drawing-calc-matcher)流用** | F1=74.9% 実績の鉄筋PoC手法を下水道に転用。kawabata承認＋所有者協議が必要 | 2-3週間 | +0.20-0.30 | 高 |

---

## 8. 6/6 Go/No-Go までのロードマップ（3週間）

### Week 1 (5/15-5/22): 内部精度ブースト
- **5/15-5/16**: GT再設計（S1）/ プロンプトスコープ明示（S2）の合意形成。aka所有者キックオフ
- **5/17-5/19**: S1 + S2 + S3 を case_001-003 で実施。F1再計測
- **5/19-5/22**: A1 (few-shot) + A2 (knowledge.md) + A5 (モデル切替)
- **Week 1 ゲート**: case_001-003 で **F1≥0.55、Recall維持** を確認

### Week 2 (5/22-5/29): 整合性とハイブリッド
- **5/22-5/25**: A3（整合性チェック改善）→ 整合性F1≥0.50
- **5/25-5/27**: B1（pdfplumber ハイブリッド）の最小プロトタイプ
- **5/27-5/29**: B3 (bbox)・B4 (物理常識フィルタ) 適用
- **Week 2 ゲート**: case_001-003 で **F1≥0.65、整合性F1≥0.50** 確認

### Week 3 (5/29-6/5): 横展開検証と判定
- **5/29-6/2**: case_004-006 GT追加（B5）、6ケース Macro F1計測
- **6/2-6/4**: 横瀬町・大月市PDFへの汎用抽出適用（事業性レポート Phase C Day 23-25 タスク）。F1劣化幅を計測
- **6/5**: 判定レポート（report_for_kawabata.md）作成
- **6/6**: **Go/No-Go判定**
  - Go閾値（F1≥0.65、行一致率≥0.90、汎用抽出劣化≤10pt、コスト≤¥10/路線）クリアなら Phase 1 MVP着手
  - 未達なら Tier C へ（Donut FT or 社内アセット⑤移行）

---

## 9. リスクと要追加調査

### 9.1 残る不確実性

- **GT再設計時の「広げ過ぎ」リスク**: 計算書20項目すべて入れると、Vision LLM側の「拾えない項目」がFNとなり Recall が下がる可能性。Phase B Day 11-13 で測定が必要
- **Gemini Pro切替時のコスト**: 図面1枚 $0.13 / 1000p → 1路線あたり >¥10 になる可能性。Go閾値「¥10/路線」と矛盾しないか要試算
- **横瀬町・大月市データの代表性**: PDFが揃っているか未確認。所有者に確認要
- **Granite-Docling の日本語対応**: 日本語建設用語の認識精度は未検証

### 9.2 要追加調査項目

1. AECV-Bench の数値レベルでの結果（PDF本体精読）→ 苦手領域の特定
2. 東芝CISSARTの整合性チェック実装方式（特許・公開資料探索）
3. 自治体DX「Articulate」スタイルのspec-drawing matchingの建設業実装事例
4. 国内事例：建技 152案件（大西氏）との具体的なシナジーポイント
5. JS共通工種体系→各自治体出力フォーマッタの「変換時の情報落ち」の規模感

### 9.3 No-Go 時のフォールバック

- **A**: Tier C 移行（社内アセット⑤への合流）= 開発期間 +2-3週間
- **B**: パートナー連携（東芝CISSARTのOEM／オリエンタル白石のCAD連携）
- **C**: 1年保留（東芝の下水道参入待ち、Track A完成待ち）

---

## 10. 社内アセット6本との接続パターン

| アセット | PoCでの活用箇所 | 改善メニューとの対応 |
|---|---|---|
| ① rd-pdf-component-extractor | 図面PDF/計算書PDFのベクター構造化 | **B1**（pdfplumberハイブリッド）のベース |
| ② rd-blueprint-layout-detection-engine (BLADE) | 領域別 pre-segmentation | **B2**（領域別投入） |
| ③ rd-rebar-drawing-hierarchy | 章立て・目録認識 | 数量計算書48p の階層解析（Phase C） |
| ④ rd-tekkin_hyo_chushutsu | 表抽出→正規化→CSV | **B1** の表抽出部分そのまま |
| ⑤ rd-poc-drawing-calc-matcher | 計算書をマスターにVLMで図面要素検出 | **C4**（最後のフォールバック） |
| ⑥ drawing_LLM_lab | マルチエージェント設計 | **C3** の応用（Phase 1 後半） |

**統合パターン推奨**:
- Tier S/A は単独で実装、まず F1=0.65 を狙う
- Tier B でアセット①②④を組み込む（Phase 1 MVP の本線）
- Tier C はアセット⑤⑥の所有者協議が前提（事業性レポートの調査ピン③）

---

## 11. CiviLink事業への示唆

### 機会
- **PoC精度ターゲット F1=0.65 は技術的に十分達成可能**（学術論文ベースで F1=0.93+ 報告あり）
- **改善メニューはほぼ全てPoCの既存スタックで実装可能** → Phase 1 MVP までの追加投資は最小限
- **横展開時の差別化軸が明確化**：「VLM単体」ではなく「JS共通工種体系正規化 × 領域別ハイブリッド × 整合性チェック対話型」の3点セットが東芝CISSARTにない強み

### 脅威
- **東芝CISSARTは整合性チェックを既に実装**（図面と数量総括表の名称・規格・数量整合性・正誤表出力）→ 「整合性チェック」自体は差別化にならない。**抽出精度＋汎用性＋プラットフォーム連携** で勝つ必要
- **KK Generation（建設業特化）が「ほぼ100%精度」を謳う** → 下水道領域への参入は時間の問題。先行優位の窓 2-3年 を 1-2年 に修正する必要があるかも
- **Civils.ai（海外）が97%精度** → 国内自治体市場には日本語要件で参入しにくいが、技術スタックは追従可能

### 推奨アクション（事業企画レベル）
1. **6/6 判定までに「F1=0.65 達成済み」「VLM単体ではなく統合スタックで戦う」というメッセージを準備**
2. 川端さん・武井さん・川畑さんへの中間報告（Week 2 終わり）で改善メニューと進捗を共有
3. 社内アセット所有者（akakoumalme, tatsuyanishimoto, Onishi）への Tier C 早期協議（No-Go時の即時切替準備）
4. 東芝CISSART 5/21ヒアリング時に「整合性チェックの実装手法・精度」を必ず質問項目に入れる

---

## 12. ソース一覧

### 論文（査読／arXiv）

- [Fine-Tuning Vision-Language Model for Automated Engineering Drawing Information Extraction (arxiv 2411.03707)](https://arxiv.org/abs/2411.03707)
- [From Drawings to Decisions: A Hybrid Vision-Language Framework (arxiv 2506.17374)](https://arxiv.org/abs/2506.17374)
- [BBox-DocVQA (arxiv 2511.15090)](https://arxiv.org/html/2511.15090v1)
- [AECV-Bench: Benchmarking Multimodal Models on AEC Drawings (arxiv 2601.04819)](https://arxiv.org/pdf/2601.04819)
- [TableFormer: Table Structure Understanding with Transformers (arxiv 2203.01017)](https://arxiv.org/abs/2203.01017)
- [TABLET: Table Structure Recognition using Encoder-only Transformers (arxiv 2506.07015)](https://arxiv.org/html/2506.07015v1)
- [Towards fully automated processing and analysis of construction diagrams (IJDAR 2024)](https://link.springer.com/article/10.1007/s10032-024-00492-9)
- [Few-Shot Symbol Detection in Engineering Drawings (TandFonline 2024)](https://www.tandfonline.com/doi/full/10.1080/08839514.2024.2406712)
- [Review of deep learning methods for engineering diagrams (Springer AI Review 2024)](https://link.springer.com/article/10.1007/s10462-024-10779-2)
- [CISOL Dataset (WACV 2025)](https://arxiv.org/html/2501.15469)
- [ManuRAG: Multi-modal RAG for Manufacturing QA (arxiv 2601.15434)](https://arxiv.org/html/2601.15434v2)
- [Topology-based 2D/3D Drawing Matching (Graphical Models 2017)](https://www.sciencedirect.com/science/article/abs/pii/S1524070317300504)
- [Optimizing Text Recognition in Mechanical Drawings (MDPI Machines 2025)](https://www.mdpi.com/2075-1702/13/3/254)
- [From concept to manufacturing: evaluating VLMs for engineering design (Springer AI Review 2025)](https://link.springer.com/article/10.1007/s10462-025-11290-y)
- [Confidence Improves Self-Consistency in LLMs (arxiv 2502.06233)](https://arxiv.org/pdf/2502.06233)
- [Majority Rules: LLM Ensemble for Content Categorization (arxiv 2511.15714)](https://arxiv.org/html/2511.15714v1)

### OSS / 商用ツール

- [IBM Granite-Docling-258M (2025)](https://www.ibm.com/new/announcements/granite-docling-end-to-end-document-conversion)
- [Docling Document Processing Framework](https://www.docling.ai/papers/)
- [PyMuPDF4LLM (PyPI)](https://pypi.org/project/pymupdf4llm/)
- [Gemini API Structured Outputs (Google AI Developers)](https://ai.google.dev/gemini-api/docs/structured-output)
- [Qwen2.5-VL Visual Grounding (PyImageSearch 2025)](https://pyimagesearch.com/2025/06/09/object-detection-and-visual-grounding-with-qwen-2-5/)

### 商用システム・国内ベンダー

- [東芝 CISSART 設計図書類照査支援](https://www.global.toshiba/jp/products-solutions/public-ict/icon.html)
- [東芝 CISSART 機能（整合性チェック）](https://www.global.toshiba/jp/products-solutions/public-ict/icon/function.html)
- [KK Generation 積算AI](https://kk-generation.com/takeoff)
- [大塚商会 AI積算](https://www.cadjapan.com/products/items/ai_sekisan/)
- [Civils.ai - AI for 2D CAD Quantity Takeoffs](https://civils.ai/blog/ai-for-pdf-cad-quantity-takeoffs/)
- [Kreo Software AI Takeoff](https://www.kreo.net/)
- [Togal AI Construction Takeoff](https://www.togal.ai/)

### ベンチマーク・比較記事

- [Benchmarking AI on Tables and Engineering Drawings (Businessware Tech)](https://www.businesswaretech.com/blog/benchmarking-ai-on-tables-and-engineering-drawings-results-findings)
- [Multimodal AI Face-Off: Claude, GPT-4V, Gemini 2026](https://claude5.com/news/multimodal-ai-face-off-claude-gpt-4v-and-gemini-in-2026)
- [PDF Data Extraction Benchmark 2025: Docling / Unstructured / LlamaParse](https://procycons.com/en/blogs/pdf-data-extraction-benchmark/)
- [7 Best Open-Source OCR Models 2025](https://www.e2enetworks.com/blog/complete-guide-open-source-ocr-models-2025)

### 国内記事

- [建設ITブログ: KK Generation 積算AI](https://ken-it.world/it/2025/07/ai-takes-off-paper.html)
- [建築設備図面への画像認識AI研究（空気調和・衛生工学会2019）](https://www.jstage.jst.go.jp/article/shasetaikai/2019.5/0/2019.5_189/_pdf)
- [建設DX KKE 図面認識AI](https://con-dx.kke.co.jp/tech/ai/recognition/)
- [AI Market 図面OCR導入解説](https://ai-market.jp/purpose/drawing-ai-ocr/)

---

*作成: 2026-05-15  Claude (Opus 4.7) by toshio.noda@malme.co.jp*
*次の更新: 6/6 Go/No-Go判定後*
