# civilink-dwg-parser

Malme 独自の DWG パーサー（Rust）。商用級、read/write 両対応を目指す 6〜12ヶ月計画。

**このプロジェクトの唯一絶対のルール**：LibreDWG / ODA Teigha の**ソースコードを開かない**。参照するのは ODA Open Design Specification（公開部分）と実DWGの観測のみ。クリーンルーム原則。

## ディレクトリ
- `crates/dwg-core` — ライブラリ本体
- `crates/dwg-cli` — `dwg-inspect` / `dwg-extract`
- `crates/dwg-py` — PyO3 バインディング（Phase A8 で有効化）
- `references/ODA_spec` — 仕様書 PDF（手動配置、`.gitignore`）
- `references/format_notes` — バージョン別の学習ノート（IPそのもの）
- `references/sample_inspections` — 実DWGのダンプ観測メモ
- `samples/{r2007,r2010,r2013,r2018}` — 実DWG（`.gitignore`）
- `issues/{open,resolved}` — 課題ログ（MD、frontmatter付）

## セットアップ
```
brew install rustup
rustup default stable
```

## 使い方（Phase A1 時点）
```
cargo build
cargo test -p dwg-core
cargo run -p dwg-cli --bin dwg-inspect -- samples/r2018/sample.dwg
```

## 現在のフェーズ
**Phase A0 進行中**（学習・リファレンス整備、3〜4週目安）。
実装計画の詳細は `/Users/nodatoshio/.claude/plans/cuddly-roaming-pie.md` 参照。

## フェーズ進捗
- [x] 足場（workspace, skeleton crates）
- [ ] **Phase A0**: 学習・リファレンス整備
- [ ] Phase A1: ファイルヘッダ / バージョン判定
- [ ] Phase A2: セクションマップ / ページマップ
- [ ] Phase A3: オブジェクトマップ
- [ ] Phase A4: 基本オブジェクト読み取り
- [ ] Phase A5: 追加エンティティ
- [ ] Phase A6: 書き込み（Write）対応
- [ ] Phase A7: マルチバージョン対応
- [ ] Phase A8: Python バインディング
- [ ] Phase A9: ドキュメント / リリース

## Phase A0 TODO（手動で進める）
- [ ] ODA Open Design Specification PDF を `references/ODA_spec/` に配置
- [ ] 実DWGサンプル 5〜10本を `samples/r2018/` 等に配置
- [ ] `references/format_notes/` に下記テンプレに沿って章別ノートを書く
  - `01_file_structure.md` — ファイル全体のレイアウト
  - `02_header.md` — ヘッダ128バイトの詳細
  - `03_section_map.md` — R2004+ の暗号化システムセクション
  - `04_page_map.md` — ページマップと圧縮
  - `05_object_map.md` — ハンドル→オフセット
  - `06_objects.md` — LAYER/BLOCK/entities
  - `07_encoding.md` — 文字コード仕様
- [ ] `references/sample_inspections/` に各サンプルの dwgread JSON 観測メモ
  - （`dwgread` は LibreDWG CLI。ソース閲覧ではなく観測ツールとしてのみ利用。JSONは観察してよい、ソースは禁止）
