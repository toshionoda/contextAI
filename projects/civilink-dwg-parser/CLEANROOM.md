# クリーンルーム開発原則

本プロジェクトは、GPL-3 でライセンスされている LibreDWG、商用の ODA SDK、
その他派生実装の**ソースコードを一切参照せずに** DWG パーサーを実装する。

## 絶対に守るルール

1. **ソースを開かない**
   - `libredwg` リポジトリの `.c` / `.h` / `.rb` / `.py` / `.pl` を開かない
   - ODA Teigha / Open Design Alliance SDK のヘッダやサンプルコードを開かない
   - 派生の OSS（`dxf_grabber`, `ezdxf` 内部の DWG 処理等がもしあれば）も同様
   - Kaitai Struct の DWG 定義は "仕様再記述" とみなしスタンスを個別判断（まず開かない方向）

2. **許される参照**
   - ODA Open Design Specification PDF（公開部分）
   - AutoDesk の公開ドキュメント（APIリファレンス、製品ヘルプ）
   - 学術論文、reverse engineering 論文
   - 実DWGファイルのバイナリ観測（hex ダンプ、`xxd`、`hexdump`）
   - `dwgread` / `dwg2dxf` の**出力**（JSONやDXF）の観察（ソースではない）

3. **汚染が疑われる状況**
   - 誤ってソースを開いてしまった場合は、その瞬間から24時間は実装作業を止めて別タスクに移る
   - 汚染の可能性があるモジュールは CLEANROOM.md に記録し、別の実装者が書き直す

4. **記録**
   - 全ての実装判断の根拠は `references/format_notes/*.md` に書く
   - 根拠の出所は「ODA spec §N.M」「sample_inspections/{file}.json」「hex観測」等と明記
   - 「なんとなく」で書いたコードはコメントに `// TODO: ground in reference` と残す

## Why

- LibreDWG は GPL-3。ソースを参照して書くと派生物とみなされ、本ライブラリ全体に GPL が伝染する
- Malme が商用プロダクトに組み込むことを前提にしているため、GPL は致命的
- Apache-2.0 / MIT など寛容なライセンスで配布するためには、**完全に独立した実装**である必要がある
- 裁判リスクを避けるには証跡（references/format_notes/）が決定的に重要

## How to apply

- 新しい実装者が参加する場合、まず本ドキュメントを読んで合意してから作業開始
- 「この挙動は LibreDWG ではこうだから…」という会話が出たら即座に止める
- コードレビューは "ソース参照の形跡" を探すことも含む
