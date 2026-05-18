# 03. セクションマップ（R2004+）

## 出所
- ODA Open Design Specification §4 / §5
- samples/r2018/{TODO}.dwg のオフセット観測

## 概要
R2004 以降、ファイルは「システムセクション」に包まれた構造になっている。
先頭 128 バイト（02_header.md）の後にシステムセクションが続き、その中に
セクションマップ（各 DWG セクションへのポインタ）とページマップが入る。

Magic: `AcFssFcAJMB` のような obfuscation が使われる。

## 構造（TODO：A2 フェーズで実測）

## Open Questions
- [ ] システムセクションの具体的な復号手順
- [ ] セクション型の定数一覧（AcDb:Header, AcDb:Classes, ...）
