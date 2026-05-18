# civilink-ed-agent

電子納品Agent（Python、野田さん個人用）。Track B として、自前 DWG パーサー（`../civilink-dwg-parser`）完成までの 2〜3週間で非CAD部分を通し、課題抽出する。

**現在のフェーズ**：Phase B0（足場整備）完了 → Phase B1（知識ベース + ファイル分類）

## セットアップ
親 repo の `requirements.txt` を流用。追加依存は下記：
```
pip install pypdf lxml typer pydantic pyyaml
```
`.env` を作成し `ANTHROPIC_API_KEY` を設定。

## 使い方
```
# スモークテスト
python -m ed_agent hello

# issue を手動起票（自動起票は各モジュールから）
python -m ed_agent issues new \
  --track B --severity major \
  --category spec-ambiguity --source classifier \
  --project sample_xxx --file report/chapter1.pdf \
  --phenomenon "..." --decision "..." --reason "..." --hypothesis "..."

# 集計
python -m ed_agent issues report
```

## フェーズ進捗
- [x] Phase B0: 足場
- [ ] Phase B1: 知識ベース + ファイル分類（次）
- [ ] Phase B2: INDEX_D.XML 生成
- [ ] Phase B3: バリデーション + パッケージ化
- [ ] Phase B4: **保留**（Track A Phase A8 完了まで）
- [ ] Phase B5: 課題レポート

## ディレクトリ
- `references/` — 戦略資料（`cde_learning_notes.md` 等）
- `knowledge/` — 電子納品要領 PDF、DTD、特記仕様書サンプル（`.gitignore`）
- `samples/` — 実プロジェクト入力（`.gitignore`）
- `output/` — 生成物（`.gitignore`）
- `issues/{open,resolved}` — 課題ログ

## Phase B0 入手タスク（野田さん手動）
- [ ] 国交省「土木設計業務等の電子納品要領 令和8年3月版」PDF を `knowledge/` に
- [ ] DTD 一式（`INDE_D05.DTD`, `REP05.DTD`, `DRAW05.DTD`, `PLA05.DTD`, `SPE05.DTD`, `OTHRS05.DTD`）を `knowledge/dtd/` に
- [ ] 電納ヘルパー または MLIT 検査プログラム を手元環境に
- [ ] 実プロジェクトサンプル最低1件を `samples/project_XXX/input/` に

## 計画詳細
`/Users/nodatoshio/.claude/plans/cuddly-roaming-pie.md`
