# 05. オブジェクトマップ

## 出所
- ODA Open Design Specification §20 相当

## 概要
ハンドル値（DWG 内で各オブジェクトを一意に識別する番号）と、
ファイル内オフセット（ページ内オフセット）のマッピングテーブル。

読み書きの両方で、オブジェクト変更時のオフセット再計算が最重要の
ロジックになる（Phase A6 の Write で大きな仕事になる）。

## 構造（TODO：Phase A3 で実測）

## Open Questions
- [ ] ハンドルの符号化（Modular Char / Modular Short）
- [ ] 削除マークの表現
