# 06. オブジェクト共通構造とエンティティ

## 出所
- ODA Open Design Specification §10 以降

## 概要
DWG 内の全オブジェクト（LAYER, LTYPE, BLOCK_RECORD, BLOCK, 各エンティティ）は
共通のバイナリ構造を持つ：

- Object Size (MS / Modular Short)
- Handle
- Extended Data
- 型ごとの Body
- CRC

## 型別
- LAYER
- LTYPE
- STYLE
- BLOCK_RECORD / BLOCK / ENDBLK
- LINE, CIRCLE, ARC, LWPOLYLINE, POLYLINE, TEXT, MTEXT, INSERT
- ATTRIB, ATTDEF
- HATCH, DIMENSION, LEADER, MLEADER, SPLINE, ELLIPSE

（Phase A4・A5 でそれぞれ別ファイルに分割するかも）

## Open Questions
- [ ] OBJECT_TYPE 定数の一覧と安定性
