# 08. ビットストリーム読取規則

## 出所
- ODA Open Design Specification §1.4

## DWG の圧縮整数型
| 型 | 名称 | 概要 |
|---|---|---|
| B  | Bit                          | 1 bit |
| BB | Bit Pair                     | 2 bits |
| BS | Bit Short                    | 2/8/16 bits（プレフィックスで決定） |
| BL | Bit Long                     | 2/8/32 bits |
| BD | Bit Double                   | 2/64 bits |
| MC | Modular Char                 | 可変長 unsigned、7 bits/byte |
| MS | Modular Short                | 可変長 unsigned、15 bits/word |
| RC | Raw Char                     | 8 bits |
| RS | Raw Short                    | 16 bits LE |
| RL | Raw Long                     | 32 bits LE |
| RD | Raw Double                   | 64 bits IEEE754 LE |
| H  | Handle                       | 可変長 |
| T  | Text（legacy）                | codepage 依存 |
| TU | Text（UTF-16LE）              | R2007+ |

## 実装メモ
- `bitstream.rs` で `BitReader` / `BitWriter` を型付きメソッドで提供
- 境界でのパディング規則に注意（セクション単位でバイト境界に戻る）

## Open Questions
- [ ] Modular Short の終端判定ビットの位置
- [ ] 符号付き整数の符号拡張規則
