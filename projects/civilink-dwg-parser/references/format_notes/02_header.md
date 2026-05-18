# 02. ファイルヘッダ

## 出所
- ODA Open Design Specification §2
- samples/{TODO}.dwg の先頭 128 バイト hex 観測

## フィールド詳細（概要テンプレ、Phase A1 で実測して埋める）
| offset | size | type | name | 備考 |
|---|---|---|---|---|
| 0x00 | 6  | ASCII | version | AC10xx |
| 0x06 | 5  | -     | padding |  |
| 0x0B | 1  | u8    | maintenance release | |
| 0x0C | 4  | u32 LE | image seeker | プレビュー画像へのオフセット |
| 0x10 | 2  | -     | unknown |  |
| 0x12 | 1  | u8    | codepage / locale | |
| 0x13 | 1  | u8    | app dwg version | |
| 0x14 | 1  | u8    | app maint release | |
| 0x15 | 3  | -     | unknown |  |
| 0x18 | 4  | u32 LE | section locator count | |
| 0x1C | ... | ...    | section locator records (5 records × 9 bytes) | |
| ...  |    |        |  |  |

## バージョン差分
| version | 差分 |
|---|---|
| R14   | TODO |
| R2000 | TODO |
| R2004 | TODO |
| R2007 | TODO |
| R2010 | TODO |
| R2013 | TODO |
| R2018 | TODO |

## 実装メモ
- 後続の `header.rs` で使う struct を、この表と 1:1 対応させる

## Open Questions
- [ ] locale / codepage の値一覧はどこにある？
- [ ] sentinel バイト列の位置
