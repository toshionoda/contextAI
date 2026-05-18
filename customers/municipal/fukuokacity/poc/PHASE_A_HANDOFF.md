# Phase A 完了サマリ + 所有者引き継ぎ資料

- **作成日**: 2026-05-07
- **Phase A 期間**: 計画 Day 0-3 → 実績 Day 0（1日内に終了）
- **目的**: Phase B（matcher 拡張）に着手するアセット所有者向けの引き継ぎ資料

---

## 1. Phase A 計画と実績

| タスク | 計画日 | 実績 | 成果物 |
|---|---|---|---|
| キックオフメモ作成 | Day 0 | ✅ 完了 | `kickoff/kickoff_memo.md` |
| 福岡市PDF構造判定 | Day 0 | ✅ 完了 | `audit/data_audit.md` / `data_audit.json` |
| feature branch 作成 | Day 1 | ⏸ 所有者キックオフ後 | （所有者作業） |
| ページ抽出・路線別仕分け | Day 1-2 | ✅ 完了 | `dataset_prep/case_001..006/` + `dataset_prep/shared/` |
| GT 手動作成（3案件） | Day 3 | ✅ ドラフト完成 | `dataset_prep/case_001..003/ground_truth.json` |

**実績**: 当初 4日工程の Phase A は、Auto Mode 下で 1日で全準備完了。

---

## 2. 福岡市受領 PDF の状態

詳細: `audit/data_audit.md`

| ファイル | ページ | ベクター度 | 判定 |
|---|---|---|---|
| 図面一式 | 8 | **50,679** | VECTOR（極めて高い） |
| 数量計算書① 那珂工区 | 27 | 287 | VECTOR |
| 数量計算書② 板付・諸岡工区 | 21 | 361 | VECTOR |
| 数量総括表 | 9 | 106 | VECTOR |
| 金抜き設計書 | 51 | 39 | TEXT_LAYER_ONLY |

**画像PDFゼロ・全ページにテキスト層あり**。Gemini Vision・pdfplumber の両方で扱える状態。Phase B 進行可。

---

## 3. 路線別仕分け結果

スクリプト: `scripts/split_by_route.py` （pdfplumber + pypdf 利用、再実行可能）
詳細: `audit/route_assignment_summary.md`

| ケース | 路線 | calc | drawing |
|---|---|---|---|
| case_001 | 429-2 | 11p | 1p |
| case_002 | 430-3 | 5p | 1p |
| case_003 | 410-1-3 | 5p | 1p |
| case_004 | 86-1 | 5p | 1p |
| case_005 | 209-4 | 5p | 1p |
| case_006 | 452-5 | 5p | 1p |
| **shared** | 全路線共通 | 31p（総括・集計・付帯工・舗装復旧） | 2p（全体位置図） |

**注**: 図面PDF が各case 1ページずつなのは、図面1枚に1路線の平面・縦断・横断が同居している構造のため。Phase B でクロップが必要なら所有者判断。

---

## 4. Ground Truth ドラフト

スキーマは `rd-poc-drawing-calc-matcher/dataset/u_wall/case_*/ground_truth.json` を参考。下水道工事用に転用。

**スキーマ**:
```json
{
  "case_id": "case_001",
  "route": "429-2",
  "detected_items": [
    {"symbol": "ST001_429-2", "value": "18.10", "unit": "m", "category": "更生管材 φ250", "bbox": null}
  ],
  "mappings": [
    {"item_type": "管更生工 φ250 更生管材", "item_type_id": "ST001", "symbol_detected": "ST001_429-2"}
  ]
}
```

**作成済みGT** (野田レビュー要):

| ケース | 路線 | 項目数 | 数量サマリ |
|---|---|---|---|
| case_001 | 429-2 | 7項目 | 更生管材 18.10m / 内面更生 17.20m / 仮設備 1回 / 本管口仕上 2箇所 / 取付管口せん孔 3箇所 |
| case_002 | 430-3 | 7項目 | 更生管材 34.80m / 内面更生 33.90m / 仮設備 1回 / 本管口仕上 2箇所 / 取付管口せん孔 5箇所 |
| case_003 | 410-1-3 | 7項目 | 更生管材 28.00m / 内面更生 27.10m / 仮設備 1回 / 本管口仕上 2箇所 / 取付管口せん孔 4箇所 |

**マスター**: `dataset_prep/calc_doc/sewer_types.json`（20項目の工種マスタ・ST001-ST020）

**注意点**: bboxは Phase B以降で所有者が画像から手動アノテートするか、Gemini Visionの自動bbox取得に任せる方針。GTドラフトでは null。

---

## 5. アセット所有者へのアクション

### akakoumalme（実装主担当・フルアサイン候補）

**最初の3日でやってほしいこと**:

1. **キックオフメモのレビュー** (`kickoff/kickoff_memo.md`)
   - フルアサイン依頼 + 連携合意項目 §8 の 1-7 への回答
2. **dataset_prep の中身レビュー**
   - 路線別仕分けの結果妥当性
   - GTドラフト3件の正確性（数値が計算書と合っているか）
3. **`rd-poc-drawing-calc-matcher` への取り込み判断**
   - feature branch `feat/sewer_kanra-fukuoka` を作成
   - dataset_prep 配下を `dataset/sewer_kanra/` へ移送
   - sewer_types.json は `dataset/sewer_kanra/calc_doc/` 配下に
   - GT は `dataset/sewer_kanra/case_001..003/ground_truth.json` に
4. **Phase B 着手**
   - `src/config/knowledge_sewer_kanra.md` のドラフト作成
   - `src/main.py` に `--structure sewer_kanra` 経路追加
   - case_001 でスモークテスト

### tatsuyanishimoto（マネジメント承認）

- akakoumalme フルアサイン承認
- feature branch 作業 vs fork の方針確定

### Katsushige-Onishi（仕様策定・建技152案件接点）

- 仕様協議の参加可否
- 建技152案件との並列展開検討

---

## 6. 引き継ぎファイル一覧

```
customers/municipal/fukuokacity/poc/
├── PHASE_A_HANDOFF.md                      # このファイル
├── audit/
│   ├── data_audit.md                       # PDF構造判定（人読み）
│   ├── data_audit.json                     # 同（機械読み）
│   └── route_assignment_summary.md         # 路線別仕分けの結果
├── kickoff/
│   └── kickoff_memo.md                     # 所有者・川畑さん向けキックオフメモ
├── scripts/
│   ├── audit_pdf.py                        # PDF構造判定スクリプト（再実行可）
│   └── split_by_route.py                   # 路線別分割スクリプト（再実行可）
└── dataset_prep/
    ├── route_mapping.json                  # 路線判定の trace
    ├── calc_doc/
    │   └── sewer_types.json                # 工種マスタ（ST001-ST020）
    ├── case_001/                           # 路線 429-2
    │   ├── calc/calc1_那珂_429-2.pdf       (11p)
    │   ├── drawing/drawing_全路線_429-2.pdf (1p)
    │   └── ground_truth.json
    ├── case_002/                           # 路線 430-3
    │   ├── calc/calc1_那珂_430-3.pdf       (5p)
    │   ├── drawing/drawing_全路線_430-3.pdf (1p)
    │   └── ground_truth.json
    ├── case_003/                           # 路線 410-1-3
    │   ├── calc/calc1_那珂_410-1-3.pdf     (5p)
    │   ├── drawing/drawing_全路線_410-1-3.pdf (1p)
    │   └── ground_truth.json
    ├── case_004/                           # 路線 86-1（GTなし）
    ├── case_005/                           # 路線 209-4（GTなし）
    ├── case_006/                           # 路線 452-5（GTなし）
    └── shared/
        ├── calc/                           # 数量計算書の総括・集計・付帯工
        │   ├── calc1_那珂_shared.pdf       (15p)
        │   └── calc2_板付諸岡_shared.pdf   (16p)
        └── drawing/
            └── drawing_全路線_shared.pdf   (2p, 全体位置図)
```

---

## 7. リスク・残課題（Phase B 着手前に確認）

| # | 項目 | 対応案 |
|---|---|---|
| 1 | GTドラフトの bbox が null | Phase B Day 7 までに所有者がアノテーション or 自動bbox取得 |
| 2 | case_004-006 の GT 未作成 | Phase B 後半でアセット所有者が作成 |
| 3 | 図面PDFが各case 1ページずつ | 1ページ内に複数路線が含まれる場合のクロップが必要か Phase B で判断 |
| 4 | shared/ の計算書 31p が未利用 | Phase C の総括表自動集計でマスター比較対象として使う |
| 5 | 金抜き設計書51p の単価コード辞書化 | Phase C Day 21-22 で対応（PG/CB/ZD/PD） |
| 6 | 横瀬町・大月市データを Phase C **汎用抽出適用検証**で利用（スキーマ追加せずF1劣化幅を計測。2026-05-08 方針変更） | `customers/municipal/comparison/` 配下に既存 |

---

## 8. 上位文書

- 計画ファイル: `/Users/nodatoshio/.claude/plans/swift-hatching-comet.md`
- 事業性評価レポート: `customers/municipal/fukuokacity/feasibility_quantity_calc_2026-05-07.md`
- 書式パターン共通性レポート: `customers/municipal/comparison/_pattern_analysis.md`
