# 01. ファイル全体構造

## 出所
- ODA Open Design Specification §1, §2
- samples/r2018/{TODO}.dwg の hex 観測（offset 0x00-末尾）

## 構造（R2018 を基準、他バージョンは差分として §バージョン差分 に）
```
+-----------------+ 0x00
| File Header     |  128 bytes（先頭 6 バイトが ASCII バージョン識別）
+-----------------+
| System Section  |  R2004+ 暗号化、Magic "AcFssFcAJMB"
+-----------------+
| Section Map     |  各セクションのオフセット・型
+-----------------+
| Page Map        |  2段階圧縮データ
+-----------------+
| AcDb:Header     |
| AcDb:Classes    |
| AcDb:Handles    |
| AcDb:AcDbObjects|
| AcDb:Template   |
| AcDb:AuxHeader  |
| ...             |
+-----------------+
| File tail       |
+-----------------+
```

## Open Questions
- [ ] ヘッダの正確なバイト長はバージョンで変わるか？
- [ ] System Section の暗号化アルゴリズムは？（Phase A2 で 03_section_map.md を書く時に解決）
