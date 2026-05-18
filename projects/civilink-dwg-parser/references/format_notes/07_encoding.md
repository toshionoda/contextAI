# 07. 文字コード

## 出所
- ODA Open Design Specification §2 の codepage
- 実 DWG（日本語環境）サンプルの観測

## 概要
- R14〜R2004 ごろ：locale に依存（日本語は Shift_JIS / CP932）
- R2007+：UTF-16LE（U）プレフィックスで明示
- DWG 内の文字列型には T（legacy）と TU/TV（Unicode）がある

## 実装メモ
- `encoding.rs` は 2種類のデコーダ（CP932 / UTF-16LE）を保持
- ヘッダの codepage フィールドでディスパッチ

## Open Questions
- [ ] CP932 の subset / superset 問題（機種依存文字）
- [ ] 混在ケース（R2007+ でも CP932 で書かれた文字列が来ることはあるか）
