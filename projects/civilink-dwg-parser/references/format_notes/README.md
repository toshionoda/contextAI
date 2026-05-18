# format_notes

Phase A0（学習フェーズ）の成果物を蓄積する場所。**ここの密度がそのまま Track A の IP になる**。

## 書き方テンプレ

各ノートは Markdown で、以下の骨格を踏襲する：

```markdown
# {章タイトル}

## 出所
- ODA Open Design Specification §X.Y
- samples/r2018/{file}.dwg の hex 観測（offset 0x00-0x80）
- sample_inspections/{file}.json の該当箇所

## 構造
{バイナリ構造を ASCII 図 / 表で書き起こす}

## フィールド詳細
| offset | size | type | name | 備考 |
|---|---|---|---|---|

## バージョン差分
| version | 差分 |
|---|---|

## 実装メモ
- {実装上の注意、罠、疑問}

## Open Questions
- [ ] {解決していない疑問。ODA spec を読み直したら追記}
```

## 想定章リスト（Phase A0 でカバーする最小範囲）

- [ ] `01_file_structure.md` — ファイル全体のレイアウト（最初の0x80バイトから末尾まで）
- [ ] `02_header.md` — ヘッダ128バイトの詳細
- [ ] `03_section_map.md` — R2004+ の暗号化システムセクション（Magic "AcFssFcAJMB"）
- [ ] `04_page_map.md` — ページマップと 2段階圧縮
- [ ] `05_object_map.md` — オブジェクトマップ、ハンドル→オフセット
- [ ] `06_objects.md` — LAYER/BLOCK_RECORD/BLOCK/entities 共通構造
- [ ] `07_encoding.md` — Shift_JIS / UTF-16LE / CP932 の扱い（バージョン依存）
- [ ] `08_bitstream.md` — DWG の bit 単位読取規則（RC/RS/RL/RD/BS/BL/BD/MC/MS等）

## 禁則
- LibreDWG や ODA Teigha のソースコードから書き起こしたと疑われる内容は書かない
- 全ての節に出所を明記する（検証可能性を担保）
